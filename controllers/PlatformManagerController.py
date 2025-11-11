# controllers/PlatformManagerController.py
# Merged controller: Platform Manager (dashboard + category assignment) + Reports
# - Provides reports_bp (same routes as old ReportsController)
# - Provides pm_bp with dashboard + category update routes and preserves endpoint names

from datetime import datetime, timedelta
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    send_file,
)
from sqlalchemy import desc, func

# ---- Shared DB / Entities ----
from entities.UserEntity import db  # shared db instance
from entities.UserEntity import UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.VolunteerServiceCategoryEntity import VolunteerServiceCategoryEntity as VCat
from entities.ReportingEntities import ReportGenerator, ReportRun


# If you rely on helper methods for category counts:
# list_with_counts() returns (categories_list, totals_only_map)
# counts_for(cat_ids) returns {cat_id: {'pending','active','late','completed','total'}}
try:
    from controllers.CategoryController import CategoryController
except Exception:
    CategoryController = None  # Optional fallback if not present


# =============================================================================
# Reports blueprint (kept identical to your original ReportsController routes)
# =============================================================================
reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")


def _default_range(granularity: str):
    now = datetime.now()
    if granularity == "daily":
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif granularity == "weekly":
        start = (now - timedelta(weeks=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=180)
    return start, now


@reports_bp.route("", methods=["GET"])
def view_reports():
    granularity = request.args.get("granularity", "daily")
    start_arg = request.args.get("start")
    end_arg = request.args.get("end")

    if start_arg and end_arg:
        try:
            period_start = datetime.fromisoformat(start_arg)
            period_end = datetime.fromisoformat(end_arg)
        except Exception:
            flash("Invalid date range.", "error")
            return redirect(url_for("reports.view_reports"))
    else:
        period_start, period_end = _default_range(granularity)

    payload = None
    if request.args.get("autogen", "1") == "1":
        payload = ReportGenerator(db).generate(period_start, period_end, granularity)  # A09 main flow

    return render_template(
        "admin/reports.html",
        payload=payload,
        granularity=granularity,
        period_start=period_start,
        period_end=period_end,
    )


@reports_bp.route("/generate", methods=["POST"])
def generate():
    granularity = request.form.get("granularity", "daily")
    start = request.form.get("start")
    end = request.form.get("end")
    if not start or not end:
        flash("Please provide a valid date range.", "error")
        return redirect(url_for("reports.view_reports"))

    period_start = datetime.fromisoformat(start)
    period_end = datetime.fromisoformat(end)

    payload = ReportGenerator(db).generate(period_start, period_end, granularity)

    # A09.E1: No data
    if (
        not payload["timeseries"]["buckets"]
        and payload["kpis"]["new_users"] == 0
        and payload["kpis"]["new_requests"] == 0
    ):
        flash("No results found for the selected range.", "warning")

    return render_template(
        "reports.html",
        payload=payload,
        granularity=granularity,
        period_start=period_start,
        period_end=period_end,
    )


@reports_bp.route("/export", methods=["POST"])
def export():
    granularity = request.form.get("granularity", "daily")
    period_start = datetime.fromisoformat(request.form.get("start"))
    period_end = datetime.fromisoformat(request.form.get("end"))
    generator = ReportGenerator(db)

    try:
        payload = generator.generate(period_start, period_end, granularity)
        path = generator.export_csv(payload, out_dir="instance/reports")
        # (optional) persist run
        # run = ReportRun(job_id=None, period_start=period_start, period_end=period_end,
        #                 granularity=granularity, file_path=path, status="SUCCESS")
        # db.session.add(run); db.session.commit()
        return send_file(path, as_attachment=True)
    except Exception:
        flash("Download failed.", "error")  # A09.E3
        return redirect(url_for("reports.view_reports"))


# =============================================================================
# Platform Manager dashboard + request category update routes
# =============================================================================
pm_bp = Blueprint("pm", __name__, url_prefix="/admin")


class PlatformManagerController:
    """Platform Manager dashboard (list & filter requests) and category assignment handlers."""

    # 🟩 View dashboard (requests + users + categories)
    @staticmethod
    def display_dashboard():
        q_status = (request.args.get("status") or "").strip().lower()
        q_text = (request.args.get("q") or "").strip()
        q_pin = (request.args.get("pin") or "").strip()
        page = max(int(request.args.get("page", 1) or 1), 1)
        per_page = 20

        query = PINRequestEntity.query

        # Filter by status
        if not q_status:
            query = query.filter(PINRequestEntity.status.in_(["pending", "active", "late"]))
        else:
            allowed = {"pending", "active", "completed", "late"}
            if q_status in allowed:
                query = query.filter(PINRequestEntity.status == q_status)

        # Text search
        if q_text:
            like = f"%{q_text}%"
            query = query.filter(
                (PINRequestEntity.title.ilike(like))
                | (PINRequestEntity.description.ilike(like))
                | (PINRequestEntity.location.ilike(like))
            )

        # Filter by PIN (user) name
        if q_pin:
            like_pin = f"%{q_pin}%"
            pins = (
                UserEntity.query.filter(
                    UserEntity.role == "pin",
                    (UserEntity.fullname.ilike(like_pin)) | (UserEntity.username.ilike(like_pin)),
                ).all()
            )
            pin_ids = [p.user_id for p in pins]
            if pin_ids:
                query = query.filter(PINRequestEntity.requested_by_id.in_(pin_ids))
            else:
                query = query.filter(False)

        query = query.order_by(desc(PINRequestEntity.created_at))
        pages = query.paginate(page=page, per_page=per_page, error_out=False)

        # Preload display names for request owners
        pin_ids = [r.requested_by_id for r in pages.items if r.requested_by_id]
        if pin_ids:
            users = {
                u.user_id: (u.fullname or u.username)
                for u in UserEntity.query.filter(UserEntity.user_id.in_(pin_ids)).all()
            }
        else:
            users = {}

        categories = VCat.query.order_by(VCat.name.asc()).all()

        # Totals-by-category and per-status breakdowns
        cats = categories
        totals_only = {}
        breakdown = {}

        if CategoryController:
            # From your helper controller if available
            try:
                cats, totals_only = CategoryController.list_with_counts()
            except Exception:
                # fall back to simple totals if helper not available
                pass

            try:
                cat_ids = [c.id for c in cats]
                breakdown = CategoryController.counts_for(cat_ids)
            except Exception:
                breakdown = {}
        else:
            # Minimal fallback if CategoryController is not present
            # totals per category
            totals_q = (
                db.session.query(
                    PINRequestEntity.volunteer_service_category_id.label("cid"),
                    func.count().label("total"),
                )
                .group_by(PINRequestEntity.volunteer_service_category_id)
                .all()
            )
            totals_only = {row.cid: int(row.total or 0) for row in totals_q}
            cats = categories
            breakdown = {}

        # Unassigned bucket (None) with per-status + total
        unassigned_rows = (
            db.session.query(PINRequestEntity.status, func.count().label("cnt"))
            .filter(PINRequestEntity.volunteer_service_category_id.is_(None))
            .group_by(PINRequestEntity.status)
            .all()
        )
        unassigned = {"pending": 0, "active": 0, "late": 0, "completed": 0, "total": 0}
        for status, cnt in unassigned_rows:
            key = (status or "unknown").lower()
            if key not in unassigned:
                unassigned[key] = 0
            unassigned[key] += int(cnt or 0)
            unassigned["total"] += int(cnt or 0)
        breakdown[None] = unassigned

        return render_template(
            "dashboard_platform_manager.html",
            requests=pages.items,
            users=users,
            categories=categories,
            categories_left=cats,
            category_counts=totals_only,  # totals-only map (if template uses it)
            counts=breakdown,  # dict-of-dicts so Jinja can do c.get('total')
            cats=cats,
            meta={
                "page": page,
                "pages_total": pages.pages or 1,
                "total": pages.total or 0,
                "filters": {"status": q_status, "q": q_text, "pin": q_pin},
            },
        )

    # 🟦 Update a single request's category
    @staticmethod
    def update_request_category(request_id: str):
        cat_id = request.form.get("category_id")
        req = PINRequestEntity.query.filter_by(request_id=request_id).first_or_404()

        if cat_id in (None, "", "null"):
            req.volunteer_service_category_id = None
        else:
            cat = VCat.query.get(int(cat_id))
            if not cat:
                flash("Category not found.", "error")
                return redirect(url_for("dashboard_platform_manager"))
            req.volunteer_service_category_id = cat.id

        try:
            db.session.commit()
            flash(f"Category updated for {req.request_id}", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating category: {e}", "danger")

        return redirect(url_for("dashboard_platform_manager"))

    # 🟨 Bulk update multiple requests' category
    @staticmethod
    def bulk_update_categories():
        ids = request.form.getlist("request_ids")
        cat_id = request.form.get("bulk_category_id")

        if not ids:
            flash("No requests selected.", "warning")
            return redirect(url_for("dashboard_platform_manager"))

        new_cat_id = None
        if cat_id not in (None, "", "null"):
            cat = VCat.query.get(int(cat_id))
            if not cat:
                flash("Category not found.", "error")
                return redirect(url_for("dashboard_platform_manager"))
            new_cat_id = cat.id

        try:
            updated = (
                PINRequestEntity.query.filter(PINRequestEntity.request_id.in_(ids)).update(
                    {"volunteer_service_category_id": new_cat_id}, synchronize_session=False
                )
            )
            db.session.commit()
            flash(f"Updated {updated} request(s).", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

        return redirect(url_for("dashboard_platform_manager"))


# -----------------------------------------------------------------------------
# Blueprint route bindings for the Platform Manager dashboard/handlers
# -----------------------------------------------------------------------------

# Keep endpoint name **dashboard_platform_manager** for backward-compat with url_for("dashboard_platform_manager")
@pm_bp.route("/dashboard", methods=["GET"], endpoint="dashboard_platform_manager")
def _dashboard_platform_manager_route():
    return PlatformManagerController.display_dashboard()


@pm_bp.route("/dashboard/request/<string:request_id>/category", methods=["POST"])
def _update_request_category_route(request_id: str):
    return PlatformManagerController.update_request_category(request_id)


@pm_bp.route("/dashboard/bulk-update", methods=["POST"])
def _bulk_update_categories_route():
    return PlatformManagerController.bulk_update_categories()
