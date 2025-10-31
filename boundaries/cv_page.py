# boundary/cv_page.py
from datetime import datetime
from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity



def display_dashboard_cv():
    if 'username' not in session:
        return redirect('/')

    user = UserEntity.query.filter_by(username=session['username'], role='cv').first()

    # Auto-mark expired requests
    now = datetime.utcnow()
    for req in PINRequestEntity.query.filter(PINRequestEntity.status.in_(["pending", "active"])).all():
        if req.end_date < now:
            req.status = "expired"
    db.session.commit()

    # get PIN requests assigned to this CV that are pending or active
    assigned_requests = (
        PINRequestEntity.query
        .filter(
            PINRequestEntity.assigned_to_id == user.user_id,
            PINRequestEntity.status.in_(["pending", "active"])
        )
        .all()
    )
    
    # attach the PIN's name to each request
    for req in assigned_requests:
        pin_user = UserEntity.query.get(req.requested_by_id)
        req.pin_name = pin_user.fullname if pin_user else "Unknown"

    return render_template('dashboard_cv.html', user=user, requests=assigned_requests)

def display_history_cv():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='cv').first()

    # get PIN requests completed by this CV - status == "completed"
    completed_requests = (
        PINRequestEntity.query
        .filter(
            PINRequestEntity.assigned_to_id == user.user_id,
            PINRequestEntity.status.in_(["completed", "expired"])
        )
        .all()
    )

    # attach the PIN's name to each request
    for req in completed_requests:
        pin_user = UserEntity.query.get(req.requested_by_id)
        req.pin_name = pin_user.fullname if pin_user else "Unknown"

    return render_template('history_cv.html', user=user, requests=completed_requests)





