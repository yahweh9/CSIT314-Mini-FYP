# boundaries/admin_boundary.py
from flask import request, session, redirect, url_for, render_template, flash
from importlib import import_module, reload

# Load (and try to reload) the controller module so we don't hit stale bytecode
_uac_mod = import_module('controllers.UserAccountController')
try:
    _uac_mod = reload(_uac_mod)
except Exception:
    pass

UserAccountController = getattr(_uac_mod, 'UserAccountController', None)

def _fallback_dashboard_data():
    # Only used if controller method is missing
    from entities.UserEntity import UserEntity
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

def display_dashboard_admin():
    if "username" not in session or session.get("role") != "admin":
        return redirect("/")
    if not UserAccountController or not hasattr(UserAccountController, "get_admin_dashboard_data"):
        data = _fallback_dashboard_data()
    else:
        data = UserAccountController.get_admin_dashboard_data()
    return render_template("dashboard_admin.html", **data)

# ---- Form handlers (unchanged) ----
def submit_create_user():
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.create_user(request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))

def submit_update_user(user_id: int):
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.update_user(user_id, request.form)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))

def submit_deactivate_user(user_id: int):
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.deactivate_user(user_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))

def submit_approve_user(user_id: int):
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.approve_user(user_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))

def submit_suspend_user(user_id: int):
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.suspend_user(user_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))

def submit_reject_user(user_id: int):
    if session.get("role") != "admin":
        return redirect("/")
    ok, msg = UserAccountController.reject_user(user_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("dashboard_admin"))