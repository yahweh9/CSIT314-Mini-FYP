# boundary/web_boundary.py

from flask import request, session, redirect, url_for, render_template, flash
from controllers.LoginController import LoginController
from controllers.RegisterController import RegisterController

def display_login_page():
    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']

        if LoginController.authenticateUser(input_username, input_password):
            user = LoginController.findUserByUsername(input_username)
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.user_id
            
            role = user.role.lower()
            if role == 'pm':
                return redirect(url_for('dashboard_platform_manager'))
            elif role == 'admin':
                return redirect(url_for('dashboard_admin'))
            elif role == 'pin':
                return redirect(url_for('dashboard_pin'))
            elif role == 'csrrep':
                return redirect(url_for('dashboard_csrrep'))
            elif role == 'cv':
                return redirect(url_for('dashboard_cv'))
        else:
            flash("Wrong username or password!", "danger")
            return redirect(url_for('login_page'))



    return render_template('login.html')

def display_successful_registration():
    if request.method == 'POST':
        if 'role' in session and session['role'].lower() == 'pm':
            return redirect(url_for('dashboard_platform_manager'))
        elif 'role' in session and session['role'].lower() == 'admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('login_page'))
    return render_template('successful_registration.html')

def display_register_admin():
    if request.method == 'POST':
        if RegisterController.register_admin():
            return render_template('successful_registration.html')
    return render_template('register_admin.html')