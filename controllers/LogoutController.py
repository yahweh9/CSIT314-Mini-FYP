from flask import request, session, redirect, url_for, render_template
from boundaries.web_page import display_login_page

class LogoutController:
    @staticmethod
    def logout():
        session.pop('username', None)
        session.pop('role', None)
        session.pop('user_id', None)

        return display_login_page()
        
        #return redirect('/')