# entities/ReportingEntities.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Dict, Any, List, Optional

from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy

# ✅ Use the shared db you already initialize in app.py
from entities.UserEntity import db, UserEntity as UserEntity
from entities.PINRequestEntity import PINRequestEntity as RequestEntity

Granularity = Literal["daily", "weekly", "monthly"]


# -------------------- Persistence models (optional scheduling) --------------------

class ReportJob(db.Model):
    __tablename__ = "report_jobs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    granularity = db.Column(db.String(10), nullable=False)  # 'daily'|'weekly'|'monthly'
    email_to = db.Column(db.String(191), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_run_at = db.Column(db.DateTime, nullable=True)


class ReportRun(db.Model):
    __tablename__ = "report_runs"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("report_jobs.id"), nullable=True)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    granularity = db.Column(db.String(10), nullable=False)
    file_path = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False)  # SUCCESS|NO_DATA|ERROR
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# --------------------------- Domain reporting service ----------------------------

@dataclass
class ReportGenerator:
    db: SQLAlchemy

    @property
    def _is_sqlite(self) -> bool:
        try:
            return (self.db.engine.name or "").startswith("sqlite")
        except Exception:
            # In migrations/CLI contexts engine may not be ready; default to sqlite-safe behavior
            return True

    # SQL “bucket” label for GROUP BY depending on granularity & dialect
    def _bucket(self, col, granularity: Granularity):
        if self._is_sqlite:
            # SQLite strftime tokens:
            #  - %Y-%m-%d (day), %Y-%m (month), %W week number (Mon-based, 00-53)
            if granularity == "daily":
                return func.strftime("%Y-%m-%d", col)
            elif granularity == "weekly":
                # Approx ISO-like week label "YYYY-Www"
                return func.printf("%s-W%s", func.strftime("%Y", col), func.strftime("%W", col))
            else:
                return func.strftime("%Y-%m", col)
        else:
            # Postgres
            if granularity == "daily":
                return func.to_char(col, "YYYY-MM-DD")
            elif granularity == "weekly":
                return func.to_char(col, 'IYYY-"W"IW')  # e.g. 2025-W46
            else:
                return func.to_char(col, "YYYY-MM")

    # Build an ordered list of bucket labels between start..end (inclusive)
    def _fill_buckets(self, granularity: Granularity, start: datetime, end: datetime) -> List[str]:
        cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        buckets: List[str] = []
        while cur <= end:
            if granularity == "daily":
                buckets.append(cur.strftime("%Y-%m-%d"))
                cur += timedelta(days=1)
            elif granularity == "weekly":
                # Keep the same label format we use in SQL
                buckets.append(f"{cur.strftime('%Y')}-W{cur.strftime('%W')}")
                cur += timedelta(days=7)
            else:
                buckets.append(cur.strftime("%Y-%m"))
                y, m = cur.year, cur.month
                if m == 12:
                    cur = cur.replace(year=y + 1, month=1, day=1)
                else:
                    cur = cur.replace(month=m + 1, day=1)
        return buckets

    def generate(self, period_start: datetime, period_end: datetime, granularity: Granularity) -> Dict[str, Any]:
        U, R = UserEntity, RequestEntity

        # --- Buckets for group-by
        b_users = self._bucket(U.created_at, granularity).label("b")
        b_reqs  = self._bucket(R.created_at, granularity).label("b")

        # For "matches", we’ll count completed requests bucketed by completed_date
        # If completed_date is NULL, we ignore it (not a completed match)
        b_match = self._bucket(R.completed_date, granularity).label("b")

        # --- Queries
        q_users = (
            self.db.session.query(b_users, func.count(U.user_id))
            .filter(U.created_at >= period_start, U.created_at <= period_end)
            .group_by(b_users).order_by(b_users.asc()).all()
        )

        q_reqs = (
            self.db.session.query(b_reqs, func.count(R.request_id))
            .filter(R.created_at >= period_start, R.created_at <= period_end)
            .group_by(b_reqs).order_by(b_reqs.asc()).all()
        )

        q_match = (
            self.db.session.query(b_match, func.count(R.request_id))
            .filter(
                R.status == "completed",
                R.completed_date.isnot(None),
                R.completed_date >= period_start,
                R.completed_date <= period_end,
            )
            .group_by(b_match).order_by(b_match.asc()).all()
        )

        users_by_b  = {str(k): int(v) for k, v in q_users if k is not None}
        reqs_by_b   = {str(k): int(v) for k, v in q_reqs if k is not None}
        match_by_b  = {str(k): int(v) for k, v in q_match if k is not None}

        buckets = self._fill_buckets(granularity, period_start, period_end)

        timeseries = {
            "buckets": buckets,
            "new_users":    [users_by_b.get(b, 0) for b in buckets],
            "new_requests": [reqs_by_b.get(b, 0) for b in buckets],
            "matches":      [match_by_b.get(b, 0) for b in buckets],
        }

        total_users = (
            self.db.session.query(func.count(U.user_id))
            .filter(U.created_at <= period_end)
            .scalar()
            or 0
        )
        new_users = (
            self.db.session.query(func.count(U.user_id))
            .filter(U.created_at >= period_start, U.created_at <= period_end)
            .scalar()
            or 0
        )
        new_reqs = (
            self.db.session.query(func.count(R.request_id))
            .filter(R.created_at >= period_start, R.created_at <= period_end)
            .scalar()
            or 0
        )
        matches = (
            self.db.session.query(func.count(R.request_id))
            .filter(
                R.status == "completed",
                R.completed_date.isnot(None),
                R.completed_date >= period_start,
                R.completed_date <= period_end,
            )
            .scalar()
            or 0
        )

        conversion = round((matches / new_reqs) * 100, 2) if new_reqs else 0.0

        kpis = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "granularity": granularity,
            "total_users": int(total_users),
            "new_users": int(new_users),
            "new_requests": int(new_reqs),
            "matches": int(matches),
            "request_to_match_conversion_pct": conversion,
        }
        return {"kpis": kpis, "timeseries": timeseries}

    # Optional: export CSV from entities layer (keeps controller thin)
    def export_csv(self, payload: Dict[str, Any], out_dir: str = "instance/reports") -> str:
        import csv, os
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"platform_report_{payload['kpis']['granularity']}_{stamp}.csv"
        path = os.path.join(out_dir, fn)

        t = payload["timeseries"]
        k = payload["kpis"]
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Metric", "Value"])
            for kk, vv in k.items():
                w.writerow([kk, vv])
            w.writerow([])
            w.writerow(["Bucket", "New Users", "New Requests", "Matches"])
            for i, b in enumerate(t["buckets"]):
                w.writerow([b, t["new_users"][i], t["new_requests"][i], t["matches"][i]])
        return path
