# boundary/cv_page.py
from datetime import datetime
from flask import request, session, redirect, url_for, render_template
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity
from controllers.RequestController import RequestController

def display_dashboard_cv():
    if 'username' not in session:
        return redirect('/')

    cv = UserEntity.query.filter_by(username=session['username'], role='cv').first()

    status = request.args.get('status')
    urgency = request.args.get('urgency')
    sort = request.args.get('sort')

    assigned_requests = RequestController.get_incomplete_requests(cv, 
                                                                  status=status, 
                                                                  urgency=urgency, 
                                                                  sort=sort)

    return render_template('dashboard_cv.html', user=cv, requests=assigned_requests)

def display_history_cv():
    if 'username' not in session:
        return redirect('/')
    cv = UserEntity.query.filter_by(username=session['username'], role='cv').first()

    completed_requests = RequestController.get_request_history(cv)

    return render_template('history_cv.html', user=cv, requests=completed_requests)

def display_report_page():
    if 'username' not in session:
        return redirect('/')

    cv = UserEntity.query.filter_by(username=session['username'], role='cv').first()
    completed_requests = RequestController.get_request_history(cv)

    return render_template('cv_report.html', user=cv, requests=completed_requests)

def display_account_page():
    if 'username' not in session:
        return redirect('/')
    cv = UserEntity.query.filter_by(username=session['username'], role='cv').first()
    return render_template('cv_account_info.html', user=cv)


