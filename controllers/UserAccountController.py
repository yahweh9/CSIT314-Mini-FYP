# controllers/UserAccountController.py
from typing import Dict, Any, Tuple
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from entities.UserEntity import db, UserEntity

class UserAccountController:
    """Control layer for A03: Manage User Accounts."""

    # ------- Queries for dashboard -------
    @staticmethod
    def get_admin_dashboard_data() -> Dict[str, Any]:
        users = UserEntity.query.all()
        return {
            "users": users,
            "total_users": len(users),
            "pending_approvals": UserEntity.query.filter_by(status="pending").count(),
            "pin_count": UserEntity.query.filter_by(role="pin", status="active").count(),
            "cv_count": UserEntity.query.filter_by(role="cv", status="active").count(),
            "csrrep_count": UserEntity.query.filter_by(role="csrrep").count(),
            "pending_users": UserEntity.query.filter_by(status="pending").all(),
            "pin_users": UserEntity.query.filter_by(role="pin").all(),
            "cv_users": UserEntity.query.filter_by(role="cv").all(),
            "csrrep_users": UserEntity.query.filter_by(role="csrrep").all(),
        }

    # ------- Create / Update / Deactivate -------
    @staticmethod
    def create_user(data: Dict[str, Any]) -> Tuple[bool, str]:
        required = ("username", "password", "role")
        if any(not data.get(k) for k in required):
            return False, "Username, password, and role are required."

        if data.get("role") not in {"pm", "admin", "pin", "csrrep", "cv"}:
            return False, "Invalid role."

        try:
            u = UserEntity(
                username=data["username"].strip(),
                password=generate_password_hash(data["password"]),
                role=data["role"],
                fullname=(data.get("fullname") or "").strip() or None,
                email=(data.get("email") or "").strip() or None,
                status=data.get("status") or "active",
                address=(data.get("address") or "").strip() or None,
                phone=(data.get("phone") or "").strip() or None,
                company=(data.get("company") or "").strip() or None,
                department=(data.get("department") or "").strip() or None,
            )
            db.session.add(u)
            db.session.commit()
            return True, "User created."
        except IntegrityError:
            db.session.rollback()
            return False, "Username already exists."
        except Exception as e:
            db.session.rollback()
            return False, f"Create failed: {e}"

    @staticmethod
    def update_user(user_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        u = UserEntity.query.get(user_id)
        if not u:
            return False, "User not found."

        try:
            # Basic editable fields
            for field in ["fullname", "email", "address", "phone", "company", "department"]:
                if field in data:
                    setattr(u, field, (data.get(field) or "").strip() or None)

            # Optional role/status edits (guard if you want to restrict)
            if "role" in data and data["role"] in {"pm", "admin", "pin", "csrrep", "cv"}:
                u.role = data["role"]
            if "status" in data and data["status"] in {"active", "pending", "suspended"}:
                u.status = data["status"]

            db.session.commit()
            return True, "User updated."
        except Exception as e:
            db.session.rollback()
            return False, f"Update failed: {e}"

    @staticmethod
    def deactivate_user(user_id: int) -> Tuple[bool, str]:
        u = UserEntity.query.get(user_id)
        if not u:
            return False, "User not found."
        try:
            u.status = "suspended"
            db.session.commit()
            return True, "User deactivated."
        except Exception as e:
            db.session.rollback()
            return False, f"Deactivate failed: {e}"

    # ------- Convenience actions used by your existing admin routes -------
    @staticmethod
    def approve_user(user_id: int) -> Tuple[bool, str]:
        u = UserEntity.query.get(user_id)
        if not u:
            return False, "User not found."
        try:
            u.status = "active"
            db.session.commit()
            return True, "User approved."
        except Exception as e:
            db.session.rollback()
            return False, f"Approve failed: {e}"

    @staticmethod
    def suspend_user(user_id: int) -> Tuple[bool, str]:
        u = UserEntity.query.get(user_id)
        if not u:
            return False, "User not found."
        try:
            u.status = "suspended"
            db.session.commit()
            return True, "User suspended."
        except Exception as e:
            db.session.rollback()
            return False, f"Suspend failed: {e}"
        
    @staticmethod
    def reject_user(user_id: int) -> Tuple[bool, str]:
        u = UserEntity.query.get(user_id)
        if not u:
            return False, "User not found."
        try:
            if u.status != "pending":
                return False, "Only pending users can be rejected."
            db.session.delete(u)
            db.session.commit()
            return True, "User rejected."
        except Exception as e:
            db.session.rollback()
            return False, f"Reject failed: {e}"
