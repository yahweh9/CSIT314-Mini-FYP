# boundary/pin_boundary.py

from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import UserEntity

def display_dashboard_pin():
    if 'username' not in session:
        return redirect('/')
    
    user = UserEntity.query.filter_by(username=session['username'], role='pin').first()
    return render_template('dashboard_pin.html', user=user)