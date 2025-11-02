# controllers/CVRequestController.py
from datetime import datetime
from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity

class RequestController:
    
    # Get all requests that a CV has yet to complete (status is 'pending' or 'active')
    @staticmethod
    def get_incomplete_requests(cv):
        
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
                PINRequestEntity.assigned_to_id == cv.user_id,
                PINRequestEntity.status.in_(["pending", "active"])
            )
            .all()
        )

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

