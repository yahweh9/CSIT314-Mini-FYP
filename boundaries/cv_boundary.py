# boundary/cv_boundary.py

from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import UserEntity

def display_dashboard_cv():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='cv').first()
    return render_template('dashboard_cv.html', user=user)

def display_history_cv():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='cv').first()
    return render_template('history_cv.html', user=user)