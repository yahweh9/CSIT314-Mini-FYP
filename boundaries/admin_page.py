# boundary/admin_boundary.py

from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import UserEntity

def display_dashboard_admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    # Get all users for different tables
    users = UserEntity.query.all()
    total_users = len(users)
    pending_approvals = UserEntity.query.filter_by(status='pending').count()
    pin_count = UserEntity.query.filter_by(role='pin', status='active').count()
    cv_count = UserEntity.query.filter_by(role='cv', status='active').count()
    csrrep_count = UserEntity.query.filter_by(role='csrrep').count()
    
    # Get filtered user lists
    pending_users = UserEntity.query.filter_by(status='pending').all()
    pin_users = UserEntity.query.filter_by(role='pin').all()
    cv_users = UserEntity.query.filter_by(role='cv').all()
    csrrep_users = UserEntity.query.filter_by(role='csrrep').all()
    
    return render_template('dashboard_admin.html', 
                         users=users, 
                         total_users=total_users,
                         pending_approvals=pending_approvals,
                         pin_count=pin_count,
                         cv_count=cv_count,
                         csrrep_count=csrrep_count,
                         pending_users=pending_users,
                         pin_users=pin_users,
                         cv_users=cv_users,
                         csrrep_users=csrrep_users)