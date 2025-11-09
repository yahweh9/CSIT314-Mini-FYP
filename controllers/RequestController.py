# controllers/CVRequestController.py
from datetime import datetime, timedelta
from flask import request, session, redirect, url_for, render_template
from sqlalchemy import func
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity


class RequestController:
    
    # Get all requests that a CV has yet to complete (status is 'pending' or 'active')
    @staticmethod
    def get_incomplete_requests(cv, status=None, urgency=None, sort=None):
        
        now = datetime.utcnow()
        # If active requests past the deadline, change the status to 'late'
        late = (PINRequestEntity.query
                     .filter(PINRequestEntity.assigned_to_id == cv.user_id,
                             PINRequestEntity.status.in_(["active"]),
                             PINRequestEntity.end_date < now)
                     .all())
        for r in late:
            r.status = "late"
        db.session.commit()

        # Get CV's assigned request with "pending", "active", "late" status
        query = (PINRequestEntity.query
             .filter(PINRequestEntity.assigned_to_id == cv.user_id,
                     PINRequestEntity.status.in_(["pending", "active", "late"])))
        
        #  Filter by status (only if filter applied)
        if status:
            query = query.filter(PINRequestEntity.status == status)

        # Filter by urgency (only if filter applied)
        if urgency:
            query = query.filter(func.lower(PINRequestEntity.urgency) == urgency.lower())

        # Sort order of assigned resquests if requested
        if sort == "end_date_asc":
            query = query.order_by(PINRequestEntity.end_date.asc())
        elif sort == "end_date_desc":
            query = query.order_by(PINRequestEntity.end_date.desc())

        assigned_requests = query.all()

        # attach PIN name to be displayed
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
                PINRequestEntity.status.in_(["completed"])
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

    # Set request status to 'active'
    @staticmethod
    def accept_request(request_id):
        try:
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            if req and req.status == 'pending':
                req.status = 'active'
                db.session.commit()
                return True
            return False

        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False
        
    @staticmethod
    def reject_request(request_id):
        try:
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            if req and req.status == 'pending':
                db.session.delete(req)
                db.session.commit()
                return True
            return False
        
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False
        
    @staticmethod
    def complete_request(request_id):
        try:
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            if req and (req.status == 'active' or req.status == 'late'):
                req.status = 'completed'
                req.completed_date = datetime.utcnow() + timedelta(hours=8)
                db.session.commit()
                return True
            return False
        
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False