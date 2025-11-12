# app.py
from flask import (
    Flask, jsonify, render_template, url_for, request,
    redirect, session, flash, send_file
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv

# -----------------------------
# BOUNDARIES
# -----------------------------
# Prefer the new boundary; fall back to the old module name if the remote still uses it.
try:
    from boundaries.platform_manager_boundary import display_dashboard_platform_manager
except Exception:
    try:
        from boundaries.platform_manager_boundary import display_dashboard_platform_manager
    except Exception:
        def display_dashboard_platform_manager():
            flash("Platform Manager page missing. Please ensure boundary file exists.", "warning")
            return redirect("/")

from boundaries.web_page import (
    display_login_page, display_register_admin, display_successful_registration
)
from boundaries.pin_page import display_dashboard_pin
from boundaries.csrrep_page import display_dashboard_csrrep
from boundaries.cv_page import (
    display_dashboard_cv, display_history_cv, display_report_page, display_account_page
)
from boundaries.admin_page import display_dashboard_admin
from boundaries.info_boundary import display_homepage, display_csr_mission

# PIN Feature Boundaries
from boundaries.pin_feedback_boundary import (
    display_pin_feedback_dashboard, display_feedback_form, submit_feedback
)
from boundaries.pin_request_boundary import (
    display_create_request_form,
    handle_create_request,
    display_my_requests,
    display_request_history,
    display_request_detail,
)

# CSR Rep Opportunities Boundary (NEW)
from boundaries.csrrep_opportunities_boundary import (
    display_search_opportunities,
    display_my_shortlist,
    add_to_shortlist,
    remove_from_shortlist,
    display_opportunity_detail,
    display_completed_services,
    display_service_detail,
    display_history_analytics,
    export_to_csv
)

# -----------------------------
# CONTROLLERS
# -----------------------------
from controllers.LoginController import LoginController
from controllers.RegisterController import RegisterController
from controllers.RequestController import RequestController
from controllers.LogoutController import LogoutController
from controllers.CategoryController import CategoryController
from controllers.PlatformManagerController import PlatformManagerController  # used by boundary

# PIN Feature Controllers
from controllers.FeedbackController import FeedbackController
from controllers.PINRequestController import PINRequestController

# -----------------------------
# ENTITIES
# -----------------------------
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.FeedbackEntity import FeedbackEntity
from entities.InterestEntity import InterestEntity
from entities.RequestViewEntity import RequestViewEntity
from entities.ShortlistEntity import ShortlistEntity  # NEW

# Be resilient if the remote doesn’t have this yet.
try:
    from entities.VolunteerServiceCategoryEntity import VolunteerServiceCategoryEntity as VCat
except Exception:
    VCat = None

# -----------------------------
# APP & DB SETUP
# -----------------------------
app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.secret_key = "fj39fj_29f9@1nfa91"

db.init_app(app)

def is_logged_in() -> bool:
    return "username" in session

def is_pm() -> bool:
    return session.get("role") == "pm"

with app.app_context():
    db.create_all()
    if UserEntity.query.count() == 0:
        print("🌱 Seeding database with initial data...")
        from seed_database import seed_database
        seed_database()
        print("✅ Database seeded successfully!")

# -----------------------------
# REPORTS: MOCK DATA GENERATOR
# -----------------------------
def _build_report_payload(period_start: datetime, period_end: datetime, granularity: str):
    granularity = (granularity or "weekly").lower()
    if granularity == "daily":
        buckets = ["D-3", "D-2", "D-1", "D0"]
        new_users = [1, 2, 3, 2]
        new_requests = [2, 3, 2, 4]
        matches = [0, 1, 1, 2]
    elif granularity == "monthly":
        buckets = ["M-5", "M-4", "M-3", "M-2", "M-1", "M0"]
        new_users = [3, 5, 4, 7, 6, 8]
        new_requests = [6, 7, 5, 8, 7, 9]
        matches = [2, 3, 2, 3, 3, 4]
    else:  # weekly
        buckets = ["W-3", "W-2", "W-1", "W0"]
        new_users = [2, 3, 1, 2]
        new_requests = [4, 5, 3, 3]
        matches = [1, 2, 1, 1]

    total_users = 42  # placeholder
    kpis = {
        "total_users": total_users,
        "new_users": sum(new_users),
        "new_requests": sum(new_requests),
        "matches": sum(matches),
        "request_to_match_conversion_pct": int(round((sum(matches) / max(1, sum(new_requests))) * 100)),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "granularity": granularity,
    }
    return {
        "kpis": kpis,
        "timeseries": {
            "buckets": buckets,
            "new_users": new_users,
            "new_requests": new_requests,
            "matches": matches,
        },
    }

# -----------------------------
# GUEST HOMEPAGE
# -----------------------------
@app.route("/", methods=["POST", "GET"])
def homepage():
    return display_homepage()

@app.route("/csr_mission")
def csr_mission():
    return display_csr_mission()

@app.route("/login_page", methods=["POST", "GET"])
def login_page():
    return display_login_page()

# -----------------------------
# DASHBOARD ROUTES
# -----------------------------
@app.route("/dashboard_pin")
def dashboard_pin():
    return display_dashboard_pin()

@app.route("/dashboard_csrrep")
def dashboard_csrrep():
    return display_dashboard_csrrep()

@app.route("/dashboard_cv")
def dashboard_cv():
    return display_dashboard_cv()

# -----------------------------
# PIN FEEDBACK ROUTES
# -----------------------------
@app.route("/pin/feedback")
def pin_feedback_dashboard():
    return display_pin_feedback_dashboard()

@app.route("/pin/feedback/<request_id>")
def display_feedback_form_route(request_id):
    return display_feedback_form(request_id)

@app.route("/pin/feedback/submit", methods=["POST"])
def submit_feedback_route():
    return submit_feedback()

@app.route("/pin/feedback/bulk_rate", methods=["POST"])
def bulk_rate_requests():
    if "user_id" not in session or session.get("role") != "pin":
        return jsonify({"success": False, "message": "Unauthorized access"})

    request_ids = request.form.getlist("request_ids[]")
    rating = request.form.get("rating")
    comments = request.form.get("comments", "")

    if not request_ids or not rating:
        return jsonify({"success": False, "message": "Please select requests and provide a rating"})

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"success": False, "message": "Rating must be between 1 and 5"})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid rating value"})

    successful_ratings = 0
    errors = []

    for request_id in request_ids:
        pin_request = PINRequestEntity.query.filter_by(
            request_id=request_id,
            requested_by_id=session["user_id"],
            status="completed",
        ).first()

        if not pin_request:
            errors.append(f"Request {request_id} not found or not completed")
            continue

        existing_feedback = FeedbackEntity.query.filter_by(
            request_id=request_id,
            pin_id=session["user_id"],
        ).first()

        if existing_feedback:
            errors.append(f"Feedback already submitted for request {request_id}")
            continue

        if pin_request.assigned_by_id:
            rated_user_id = pin_request.assigned_by_id
            rated_user_role = "csrrep"
        elif pin_request.assigned_to_id:
            rated_user_id = pin_request.assigned_to_id
            rated_user_role = "cv"
        else:
            errors.append(f"No assigned user for request {request_id}")
            continue

        new_feedback = FeedbackEntity(
            request_id=request_id,
            pin_id=session["user_id"],
            rated_user_id=rated_user_id,
            rated_user_role=rated_user_role,
            rating=rating,
            comments=comments,
        )
        db.session.add(new_feedback)
        successful_ratings += 1

    if successful_ratings > 0:
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully rated {successful_ratings} requests"})
    else:
        return jsonify({"success": False, "message": "No requests were rated. " + "; ".join(errors)})

# -----------------------------
# PIN REQUEST MANAGEMENT
# -----------------------------
@app.route("/pin/request/create", methods=["GET"])
def pin_create_request():
    return display_create_request_form()

@app.route("/pin/request/create", methods=["POST"])
def pin_create_request_submit():
    return handle_create_request()

@app.route("/pin/requests")
def pin_my_requests():
    return display_my_requests()

@app.route("/pin/requests/history")
def pin_request_history():
    return display_request_history()

@app.route("/pin/request/<request_id>")
def pin_request_detail(request_id):
    return display_request_detail(request_id)

@app.route("/pin/request/<string:request_id>/edit", methods=["GET", "POST"])
def pin_edit_request(request_id):
    from boundaries.pin_request_boundary import handle_edit_request
    return handle_edit_request(request_id)

@app.route("/pin/request/<string:request_id>/cancel", methods=["POST"])
def pin_cancel_request(request_id):
    from boundaries.pin_request_boundary import handle_cancel_request
    return handle_cancel_request(request_id)

# -----------------------------
# PIN SELF-MANAGEMENT
# -----------------------------
@app.route("/pin/request/activate/<string:request_id>", methods=["POST"])
def pin_activate_request(request_id):
    if "user_id" not in session or session.get("role") != "pin":
        return redirect("/")

    req = PINRequestEntity.query.filter_by(
        request_id=request_id, requested_by_id=session["user_id"]
    ).first()

    if req and req.status == "pending":
        req.status = "active"
        req.updated_at = datetime.utcnow()
        db.session.commit()
        session["flash_message"] = "Request activated! You can now mark it as completed."
        session["flash_category"] = "success"

    return redirect(url_for("pin_my_requests"))

@app.route("/pin/request/complete/<string:request_id>", methods=["POST"])
def pin_complete_request(request_id):
    if "user_id" not in session or session.get("role") != "pin":
        return redirect("/")

    req = PINRequestEntity.query.filter_by(
        request_id=request_id, requested_by_id=session["user_id"]
    ).first()

    if req and req.status == "active":
        req.status = "completed"
        req.updated_at = datetime.utcnow()
        db.session.commit()
        session["flash_message"] = "Request marked as completed! You can now give feedback."
        session["flash_category"] = "success"

    return redirect(url_for("pin_my_requests"))

@app.route("/fix_completed_requests")
def fix_completed_requests():
    if "user_id" not in session or session.get("role") != "pin":
        return redirect("/")

    completed_requests = (
        PINRequestEntity.query.filter_by(
            requested_by_id=session["user_id"], status="completed"
        )
        .filter(
            (PINRequestEntity.assigned_to_id.is_(None))
            & (PINRequestEntity.assigned_by_id.is_(None))
        )
        .all()
    )

    cv_user = UserEntity.query.filter_by(role="cv", status="active").first()
    csr_user = UserEntity.query.filter_by(role="csrrep", status="active").first()

    fixed_count = 0
    for req in completed_requests:
        if cv_user:
            req.assigned_to_id = cv_user.user_id
            fixed_count += 1
            print(f"✅ Assigned CV {cv_user.username} to request {req.request_id}")

    if fixed_count > 0:
        db.session.commit()
        session["flash_message"] = f"Fixed {fixed_count} completed requests! You can now give feedback."
        session["flash_category"] = "success"
    else:
        session["flash_message"] = "All completed requests already have assigned users."
        session["flash_category"] = "info"

    return redirect(url_for("pin_feedback_dashboard"))

# -----------------------------
# CV REQUEST MANAGEMENT
# -----------------------------
@app.route("/dashboard_cv/accept/<string:request_id>", methods=["POST"])
def accept_request(request_id):
    RequestController.accept_request(request_id)
    return redirect(url_for("dashboard_cv"))

@app.route("/dashboard_cv/reject/<string:request_id>", methods=["POST"])
def reject_request(request_id):
    RequestController.reject_request(request_id)
    return redirect(url_for("dashboard_cv"))

@app.route("/cv/complete/<string:request_id>", methods=["POST"])
def complete_request(request_id):
    RequestController.complete_request(request_id)
    return redirect(url_for("dashboard_cv"))

@app.route("/dashboard_cv/interest/<string:request_id>", methods=["POST"])
def express_interest(request_id):
    cv = UserEntity.query.filter_by(username=session["username"], role="cv").first()

    interested = InterestEntity.query.filter_by(request_id=request_id).all()
    print("BEFORE interested for", request_id, ":", [i.cv_id for i in interested])

    RequestController.express_interest(request_id, cv.user_id)

    print("Express interest triggered!")
    print("Request ID:", request_id)
    print("CV ID:", cv.user_id)
    print("AFTER interested for", request_id, ":", [i.cv_id for i in interested])

    return redirect(url_for("dashboard_cv"))

@app.route("/view_request/<string:request_id>")
def view_request(request_id):
    cv = UserEntity.query.filter_by(username=session["username"], role="cv").first()
    RequestController.record_view(request_id, cv.user_id)
    return redirect(url_for("dashboard_cv", open=request_id))

# -----------------------------
# A08: Service Category Mgmt (PM)
# -----------------------------
@app.post("/pm/categories/create")
def route_pm_category_create():
    if not (is_logged_in() and is_pm()):
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard_platform_manager"))

    name = request.form.get("name", "")
    description = request.form.get("description", "")
    is_active = request.form.get("is_active") == "on"

    ok, msg = CategoryController.create_category(name, description, is_active)
    flash("Category created." if ok else msg, "success" if ok else "warning")
    return redirect(url_for("dashboard_platform_manager"))

@app.post("/pm/categories/<int:cat_id>/update")
def route_pm_category_update(cat_id):
    if not (is_logged_in() and is_pm()):
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard_platform_manager"))

    name = request.form.get("name", "")
    description = request.form.get("description", "")
    is_active = request.form.get("is_active") == "on"

    ok, msg = CategoryController.update_category(cat_id, name, description, is_active)
    flash("Category updated." if ok else msg, "success" if ok else "warning")
    return redirect(url_for("dashboard_platform_manager"))

@app.post("/pm/categories/<int:cat_id>/delete")
def route_pm_category_delete(cat_id):
    if not (is_logged_in() and is_pm()):
        flash("Unauthorized.", "danger")
        return redirect(url_for("dashboard_platform_manager"))

    ok, msg = CategoryController.delete_category(cat_id)
    flash("Category deleted." if ok else msg, "success" if ok else "warning")
    return redirect(url_for("dashboard_platform_manager"))

# -----------------------------
# ACCOUNT / ADMIN PAGES
# -----------------------------
@app.route("/cv_account_info")
def cv_account_info():
    return display_account_page()

@app.route("/history_cv")
def history_cv():
    return display_history_cv()

@app.route("/dashboard_platform_manager")
def dashboard_platform_manager():
    return display_dashboard_platform_manager()

@app.route("/dashboard_admin")
def dashboard_admin():
    return display_dashboard_admin()

@app.route('/view_history_report')
def view_history_report():
    return display_report_page()

# -----------------------------
# REPORTS UI (no blueprint)
# -----------------------------
@app.route("/view_report", methods=["GET", "POST"])
def view_report():
    """
    Renders the reports page (templates/reports.html).
    Accepts:
      - GET with optional ?granularity= and ?autogen=1
      - POST from the form with granularity, start, end
    """
    granularity = (request.values.get("granularity") or "weekly").lower()
    now = datetime.utcnow()

    autogen = request.args.get("autogen", "0") == "1"
    start_raw = request.values.get("start")
    end_raw = request.values.get("end")

    if start_raw and end_raw and not autogen:
        try:
            period_start = datetime.fromisoformat(start_raw)
            period_end = datetime.fromisoformat(end_raw)
        except Exception:
            flash("Invalid date range.", "error")
            if granularity == "daily":
                period_start = now - timedelta(days=6)
            elif granularity == "monthly":
                period_start = now - timedelta(days=180)
            else:
                period_start = now - timedelta(days=60)
            period_end = now
    else:
        if granularity == "daily":
            period_start = now - timedelta(days=6)
        elif granularity == "monthly":
            period_start = now - timedelta(days=180)
        else:
            period_start = now - timedelta(days=60)
        period_end = now

    payload = _build_report_payload(period_start, period_end, granularity)

    return render_template(
        "reports.html",
        granularity=granularity,
        period_start=period_start,
        period_end=period_end,
        payload=payload,
    )

@app.route("/reports/export", methods=["POST"])
def export_report():
    """
    Exports a CSV derived from the same mock payload as the view.
    The reports template should POST granularity/start/end to this route.
    """
    granularity = (request.form.get("granularity") or "weekly").lower()
    try:
        period_start = datetime.fromisoformat(request.form.get("start"))
        period_end = datetime.fromisoformat(request.form.get("end"))
    except Exception:
        flash("Invalid export range.", "error")
        return redirect(url_for("view_report"))

    payload = _build_report_payload(period_start, period_end, granularity)

    out_dir = os.path.join(BASE_DIR, "instance", "reports")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"report_{granularity}_{period_start.date()}_{period_end.date()}.csv"
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bucket", "new_users", "new_requests", "matches"])
        ts = payload["timeseries"]
        for i, bucket in enumerate(ts["buckets"]):
            writer.writerow([
                bucket,
                ts["new_users"][i],
                ts["new_requests"][i],
                ts["matches"][i],
            ])

    return send_file(out_path, as_attachment=True)

@app.route("/admin/reports")
def reports_alias():
    return redirect(url_for("view_report", autogen=request.args.get("autogen", "0")))

# -----------------------------
# REGISTRATION ROUTES
# -----------------------------
@app.route("/register_admin", methods=["GET", "POST"])
def register_admin():
    return display_register_admin()

@app.route("/register_pin", methods=["GET", "POST"])
def register_pin():
    return RegisterController.register_pin()

@app.route("/register_csrrep_or_cv", methods=["GET", "POST"])
def register_csrrep_or_cv():
    return RegisterController.register_csrrep_or_cv()

@app.route("/register_info_pin", methods=["GET", "POST"])
def registration_info_pin():
    return RegisterController.register_info_pin()

@app.route("/register_info_csrrep", methods=["GET", "POST"])
def registration_info_csrrep():
    return RegisterController.register_info_csrrep()

@app.route("/register_info_cv", methods=["GET", "POST"])
def registration_info_cv():
    return RegisterController.register_info_cv()

@app.route("/successful_registration", methods=["GET", "POST"])
def successful_registration():
    return display_successful_registration()

# -----------------------------
# ADMIN MANAGEMENT
# -----------------------------
@app.route("/admin/create_csr_rep", methods=["GET", "POST"])
def admin_create_csr_rep():
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        csr_rep = UserEntity(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"]),
            role="csrrep",
            fullname=request.form["fullname"],
            email=request.form["email"],
            company=request.form["company"],
            status="active",
        )
        db.session.add(csr_rep)
        db.session.commit()
        return redirect(url_for("dashboard_admin"))

    return redirect(url_for("dashboard_admin"))

@app.route("/admin/approve_user/<int:user_id>")
def admin_approve_user(user_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")

    user = UserEntity.query.get(user_id)
    if user and user.status == "pending":
        user.status = "active"
        db.session.commit()

    return redirect(url_for("dashboard_admin"))

@app.route("/admin/reject_user/<int:user_id>")
def admin_reject_user(user_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")

    user = UserEntity.query.get(user_id)
    if user and user.status == "pending":
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for("dashboard_admin"))

@app.route("/admin/suspend_user/<int:user_id>")
def admin_suspend_user(user_id):
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")

    user = UserEntity.query.get(user_id)
    if user and user.status == "active":
        user.status = "suspended"
        db.session.commit()

    return redirect(url_for("dashboard_admin"))

# ============================================================================
# CSR REP FEATURES - SEARCH & SHORTLIST OPPORTUNITIES
# ============================================================================

@app.route('/csrrep/search_opportunities', methods=['GET'])
def csrrep_search_opportunities():
    """Search and browse volunteer opportunities"""
    return display_search_opportunities()

@app.route('/csrrep/opportunity/<string:request_id>')
def csrrep_opportunity_detail(request_id):
    """View detailed information about a specific opportunity"""
    return display_opportunity_detail(request_id)

@app.route('/csrrep/my_shortlist', methods=['GET'])
def csrrep_my_shortlist():
    """View CSR Rep's shortlisted opportunities"""
    return display_my_shortlist()

@app.route('/csrrep/shortlist/add', methods=['POST'])
def csrrep_add_to_shortlist():
    """Add opportunity to shortlist (AJAX)"""
    return add_to_shortlist()

@app.route('/csrrep/shortlist/remove', methods=['POST'])
def csrrep_remove_from_shortlist():
    """Remove opportunity from shortlist (AJAX)"""
    return remove_from_shortlist()

# ============================================================================
# CSR REP FEATURES - COMPLETED SERVICES HISTORY & ANALYTICS
# ============================================================================

@app.route('/csrrep/completed_services', methods=['GET'])
def csrrep_completed_services():
    """View completed volunteer services with filters"""
    return display_completed_services()

@app.route('/csrrep/service/<string:request_id>')
def csrrep_service_detail(request_id):
    """View detailed information about a completed service"""
    return display_service_detail(request_id)

@app.route('/csrrep/history_analytics', methods=['GET'])
def csrrep_history_analytics():
    """View analytics dashboard for completed services"""
    return display_history_analytics()

@app.route('/csrrep/history/export_csv', methods=['GET'])
def csrrep_export_history():
    """Export completed services to CSV"""
    return export_to_csv()

# ============================================================================
# END OF CSR REP FEATURES
# ============================================================================

# UTILITY ROUTES
# -----------------------------
@app.route("/list_users")
def list_users():
    users = UserEntity.query.all()
    return "<br>".join(
        [
            f"Username: {u.username} - UserID: {u.user_id} - Full Name: {u.fullname} - Role: {u.role}"
            for u in users
        ]
    )

@app.route("/logout")
def logout():
    return LogoutController.logout()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print("📡 Access your web at: http://127.0.0.1:5000")
    app.run(debug=True)
