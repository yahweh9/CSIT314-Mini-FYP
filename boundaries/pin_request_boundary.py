# boundaries/pin_request_boundary.py
from flask import request, session, redirect, url_for, render_template, flash
from controllers.PINRequestController import PINRequestController
from entities.UserEntity import UserEntity

def display_create_request_form():
    """Display the request creation form"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    return render_template('pin_create_request.html', user=user)

def handle_create_request():
    """Handle request creation form submission"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    if PINRequestController.create_request():
        return redirect(url_for('pin_my_requests'))
    else:
        return redirect(url_for('pin_create_request'))

def display_my_requests():
    """Display user's active requests"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    active_requests = PINRequestController.get_active_requests(session['user_id'])
    
    return render_template('pin_my_requests.html', user=user, requests=active_requests)

def display_request_history():
    """Display user's request history"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    completed_requests = PINRequestController.get_completed_requests(session['user_id'])
    
    return render_template('pin_request_history.html', user=user, requests=completed_requests)

def display_request_detail(request_id):
    """Display detailed view of a specific request"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    request_obj = PINRequestController.get_request_by_id(request_id, session['user_id'])
    
    if not request_obj:
        flash('Request not found', 'error')
        return redirect(url_for('pin_my_requests'))
    
    return render_template('pin_request_detail.html', user=user, request=request_obj)