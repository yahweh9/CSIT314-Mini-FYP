# boundary/project_manager_boundary.py

from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import UserEntity

def display_dashboard_platform_manager():
    if 'username' not in session:
        return redirect('/')
    users = UserEntity.query.all()
    total_users = len(users)
    return render_template('dashboard_platform_manager.html', users=users, total_users=total_users)
