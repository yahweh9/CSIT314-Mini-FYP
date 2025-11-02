# NOT IN USE

'''from flask import render_template, request, session
from werkzeug.security import generate_password_hash

#from test import db
from entities.UserEntity import db
from entities.UserEntity import UserEntity
from entities.PINRequestEntity import PINRequestEntity


class CVReportController:

    @staticmethod
    def get_completed_requests(cv):
        
        completed_requests = PINRequestEntity.query.filter_by(
            assigned_to_id=cv.user_id, status='completed'
        ).all()

        return completed_requests'''