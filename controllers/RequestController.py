# controllers/CVRequestController.py
from datetime import datetime
from flask import request, session, redirect, url_for, render_template
from sqlalchemy import func
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity


class RequestController:
    
    # Get all requests that a CV has yet to complete (status is 'pending' or 'active')
    @staticmethod
    def get_incomplete_requests(cv, urgency=None, sort=None):
        # Only expire assigned ones (optional; safer)
        now = datetime.utcnow()
        to_expire = (PINRequestEntity.query
                     .filter(PINRequestEntity.assigned_to_id == cv.user_id,
                             PINRequestEntity.status.in_(["pending", "active"]),
                             PINRequestEntity.end_date < now)
                     .all())
        for r in to_expire:
            r.status = "expired"
        db.session.commit()

        q = (PINRequestEntity.query
             .filter(PINRequestEntity.assigned_to_id == cv.user_id,
                     PINRequestEntity.status.in_(["pending", "active"])))

        # filter urgency only if provided
        if urgency:
            q = q.filter(func.lower(PINRequestEntity.urgency) == urgency.lower())

        # sort if requested
        if sort == "end_date_asc":
            q = q.order_by(PINRequestEntity.end_date.asc())
        elif sort == "end_date_desc":
            q = q.order_by(PINRequestEntity.end_date.desc())

        assigned_requests = q.all()

        # attach PIN name
        for req in assigned_requests:
            pin_user = UserEntity.query.get(req.requested_by_id)
            req.pin_name = pin_user.fullname if pin_user else "Unknown"

        return assigned_requests

    # Get all completed requests of a CV (status is 'completed' or 'expired')
    @staticmethod
    def get_request_history(cv):
        # get PIN requests completed by this CV - status == "completed"
        completed_requests = (
            PINRequestEntity.query
            .filter(
                PINRequestEntity.assigned_to_id == cv.user_id,
                PINRequestEntity.status.in_(["completed", "expired"])
            )
            .all()
        )

        # attach the PIN's name to each request
        for req in completed_requests:
            pin_user = UserEntity.query.get(req.requested_by_id)
            req.pin_name = pin_user.fullname if pin_user else "Unknown"

        return completed_requests
    
    @staticmethod
    def accept_request(request_id):
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if req and req.status == 'pending':
            req.status = 'active'
            db.session.commit()
        return redirect(url_for('dashboard_cv'))

    @staticmethod
    def reject_request(request_id):
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if req and req.status == 'pending':
            db.session.delete(req)
            db.session.commit()
        return redirect(url_for('dashboard_cv'))

