from flask import request, session
from werkzeug.security import check_password_hash
from entities.CSRRepEntity import CSRRepEntity
from entities.PINEntity import PINEntity
from entities.CorporateVolunteerEntity import CorporateVolunteerEntity
from entities.AdminEntity import AdminEntity

class LoginController:
    @staticmethod
    def findUserByUsername(username):
        user = (
            CSRRepEntity.query.filter_by(username=username).first()
            or PINEntity.query.filter_by(username=username).first()
            or CorporateVolunteerEntity.query.filter_by(username=username).first()
            or AdminEntity.query.filter_by(username=username).first()
        )
        return user
    
    @staticmethod
    def authenticateUser(input_username, input_password):
        if not input_username.strip() or not input_password.strip():
            return False
        
        user = LoginController.findUserByUsername(input_username)
        if user and check_password_hash(user.password, input_password):
            return True
