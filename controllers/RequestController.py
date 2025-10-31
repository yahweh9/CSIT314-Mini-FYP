# controllers/CVRequestController.py

from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity

class RequestController:
    
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

    @staticmethod
    def complete_request(request_id):
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if req and req.status == 'active':
            req.status = 'completed'
            db.session.commit()
        return redirect(url_for('dashboard_cv'))
