from flask import Flask, jsonify, render_template, url_for, request, redirect, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# BOUNDARIES
from boundaries.web_page import display_login_page, display_register_admin, display_successful_registration
from boundaries.pin_page import display_dashboard_pin
from boundaries.csrrep_page import display_dashboard_csrrep
from boundaries.cv_page import display_dashboard_cv, display_history_cv, display_report_page, display_account_page
from boundaries.admin_page import display_dashboard_admin
from boundaries.platform_manager_page import display_dashboard_platform_manager

# PIN Feature Boundaries
from boundaries.pin_feedback_boundary import display_pin_feedback_dashboard, display_feedback_form, submit_feedback
from boundaries.pin_request_boundary import (
    display_create_request_form, 
    handle_create_request, 
    display_my_requests, 
    display_request_history, 
    display_request_detail
)

# CONTROLLERS
from controllers.LoginController import LoginController
from controllers.RegisterController import RegisterController
from controllers.RequestController import RequestController
from controllers.LogoutController import LogoutController

# PIN Feature Controllers
from controllers.FeedbackController import FeedbackController
from controllers.PINRequestController import PINRequestController
from controllers.RequestController import RequestController

# ENTITIES
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.FeedbackEntity import FeedbackEntity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db.init_app(app)
app.secret_key = 'fj39fj_29f9@1nfa91'

with app.app_context():
    db.create_all()
    
    # Seed database if empty
    if UserEntity.query.count() == 0:
        print("🌱 Seeding database with initial data...")
        from seed_database import seed_database
        seed_database()
        print("✅ Database seeded successfully!")

@app.route('/', methods=['POST', 'GET'])                                         
def login_page():
    return display_login_page()

# DASHBOARD ROUTES
@app.route('/dashboard_pin')
def dashboard_pin():
    return display_dashboard_pin()

@app.route('/dashboard_csrrep')
def dashboard_csrrep():
    return display_dashboard_csrrep()

@app.route('/dashboard_cv')
def dashboard_cv():
    return display_dashboard_cv()

# PIN FEEDBACK ROUTES
@app.route('/pin/feedback')
def pin_feedback_dashboard():
    return display_pin_feedback_dashboard()

@app.route('/pin/feedback/<request_id>')
def display_feedback_form_route(request_id):
    return display_feedback_form(request_id)

@app.route('/pin/feedback/submit', methods=['POST'])
def submit_feedback_route():
    return submit_feedback()

@app.route('/pin/feedback/bulk_rate', methods=['POST'])
def bulk_rate_requests():
    """Handle bulk rating of multiple requests"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    # Get form data
    request_ids = request.form.getlist('request_ids[]')
    rating = request.form.get('rating')
    comments = request.form.get('comments', '')
    
    if not request_ids or not rating:
        return jsonify({'success': False, 'message': 'Please select requests and provide a rating'})
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid rating value'})
    
    successful_ratings = 0
    errors = []
    
    for request_id in request_ids:
        # Check if request exists and is completed
        pin_request = PINRequestEntity.query.filter_by(
            request_id=request_id,
            requested_by_id=session['user_id'],
            status='completed'
        ).first()
        
        if not pin_request:
            errors.append(f"Request {request_id} not found or not completed")
            continue
        
        # Check for duplicate feedback
        existing_feedback = FeedbackEntity.query.filter_by(
            request_id=request_id,
            pin_id=session['user_id']
        ).first()
        
        if existing_feedback:
            errors.append(f"Feedback already submitted for request {request_id}")
            continue
        
        # Determine who to rate
        if pin_request.assigned_by_id:
            rated_user_id = pin_request.assigned_by_id
            rated_user_role = 'csrrep'
        elif pin_request.assigned_to_id:
            rated_user_id = pin_request.assigned_to_id
            rated_user_role = 'cv'
        else:
            errors.append(f"No assigned user for request {request_id}")
            continue
        
        # Create feedback
        new_feedback = FeedbackEntity(
            request_id=request_id,
            pin_id=session['user_id'],
            rated_user_id=rated_user_id,
            rated_user_role=rated_user_role,
            rating=rating,
            comments=comments
        )
        
        db.session.add(new_feedback)
        successful_ratings += 1
    
    if successful_ratings > 0:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Successfully rated {successful_ratings} requests'})
    else:
        return jsonify({'success': False, 'message': 'No requests were rated. ' + '; '.join(errors)}) 

# PIN REQUEST MANAGEMENT ROUTES
@app.route('/pin/request/create', methods=['GET'])
def pin_create_request():
    return display_create_request_form()

@app.route('/pin/request/create', methods=['POST'])
def pin_create_request_submit():
    return handle_create_request()

@app.route('/pin/requests')
def pin_my_requests():
    return display_my_requests()

@app.route('/pin/requests/history')
def pin_request_history():
    return display_request_history()

@app.route('/pin/request/<request_id>')
def pin_request_detail(request_id):
    return display_request_detail(request_id)

# PIN SELF-MANAGEMENT ROUTES
@app.route('/pin/request/activate/<string:request_id>', methods=['POST'])
def pin_activate_request(request_id):
    """Allow PIN to activate their own requests for testing"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    req = PINRequestEntity.query.filter_by(
        request_id=request_id, 
        requested_by_id=session['user_id']
    ).first()
    
    if req and req.status == 'pending':
        req.status = 'active'
        req.updated_at = datetime.utcnow()
        db.session.commit()
        session['flash_message'] = 'Request activated! You can now mark it as completed.'
        session['flash_category'] = 'success'
    
    return redirect(url_for('pin_my_requests'))

@app.route('/pin/request/complete/<string:request_id>', methods=['POST'])
def pin_complete_request(request_id):
    """Allow PIN to mark their requests as completed"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    req = PINRequestEntity.query.filter_by(
        request_id=request_id, 
        requested_by_id=session['user_id']
    ).first()
    
    if req and req.status == 'active':
        req.status = 'completed'
        req.updated_at = datetime.utcnow()
        db.session.commit()
        session['flash_message'] = 'Request marked as completed! You can now give feedback.'
        session['flash_category'] = 'success'
    
    return redirect(url_for('pin_my_requests'))

@app.route('/fix_completed_requests')
def fix_completed_requests():
    """Automatically assign users to completed requests for testing"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    # Get completed requests without assigned users
    completed_requests = PINRequestEntity.query.filter_by(
        requested_by_id=session['user_id'],
        status='completed'
    ).filter(
        (PINRequestEntity.assigned_to_id.is_(None)) & 
        (PINRequestEntity.assigned_by_id.is_(None))
    ).all()
    
    # Find available users
    cv_user = UserEntity.query.filter_by(role='cv', status='active').first()
    csr_user = UserEntity.query.filter_by(role='csrrep', status='active').first()
    
    fixed_count = 0
    for req in completed_requests:
        if cv_user:
            req.assigned_to_id = cv_user.user_id
            fixed_count += 1
            print(f"✅ Assigned CV {cv_user.username} to request {req.request_id}")
    
    if fixed_count > 0:
        db.session.commit()
        session['flash_message'] = f'Fixed {fixed_count} completed requests! You can now give feedback.'
        session['flash_category'] = 'success'
    else:
        session['flash_message'] = 'All completed requests already have assigned users.'
        session['flash_category'] = 'info'
    
    return redirect(url_for('pin_feedback_dashboard'))

# CV REQUEST MANAGEMENT ROUTES
@app.route('/dashboard_cv/accept/<string:request_id>', methods=['POST'])
def accept_request(request_id):
    RequestController.accept_request(request_id)
    return redirect(url_for('dashboard_cv'))

@app.route('/dashboard_cv/reject/<string:request_id>', methods=['POST'])
def reject_request(request_id):
    RequestController.reject_request(request_id)
    return redirect(url_for('dashboard_cv'))

@app.route('/cv/complete/<string:request_id>', methods=['POST'])
def complete_request(request_id):
    RequestController.complete_request(request_id)
    return redirect(url_for('dashboard_cv'))

@app.route('/cv_account_info')
def cv_account_info():
    return display_account_page()

@app.route('/history_cv')
def history_cv():
    return display_history_cv()

@app.route('/view_report')
def view_report():
    return display_report_page()

@app.route('/dashboard_platform_manager')
def dashboard_platform_manager():
    return display_dashboard_platform_manager()

@app.route('/dashboard_admin')
def dashboard_admin():
    return display_dashboard_admin()

# REGISTRATION ROUTES
@app.route('/register_admin', methods=['GET','POST'])
def register_admin():
    return display_register_admin()

@app.route('/register_pin', methods=['GET','POST'])
def register_pin():
    return RegisterController.register_pin()

@app.route('/register_csrrep_or_cv', methods=['GET','POST'])
def register_csrrep_or_cv():
    return RegisterController.register_csrrep_or_cv()

@app.route('/register_info_pin', methods=['GET','POST'])
def registration_info_pin():
    return RegisterController.register_info_pin()

@app.route('/register_info_csrrep', methods=['GET','POST'])
def registration_info_csrrep():
    return RegisterController.register_info_csrrep()

@app.route('/register_info_cv', methods=['GET','POST'])
def registration_info_cv():
    return RegisterController.register_info_cv()

@app.route('/successful_registration', methods=['GET','POST'])
def successful_registration():
    return display_successful_registration()

# ADMIN MANAGEMENT ROUTES
@app.route('/admin/create_csr_rep', methods=['GET', 'POST'])
def admin_create_csr_rep():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        csr_rep = UserEntity(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            role='csrrep',
            fullname=request.form['fullname'],
            email=request.form['email'],
            company=request.form['company'],
            status='active'
        )
        db.session.add(csr_rep)
        db.session.commit()
        return redirect(url_for('dashboard_admin'))

@app.route('/admin/approve_user/<int:user_id>')
def admin_approve_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    user = UserEntity.query.get(user_id)
    if user and user.status == 'pending':
        user.status = 'active'
        db.session.commit()
    
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/reject_user/<int:user_id>')
def admin_reject_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    user = UserEntity.query.get(user_id)
    if user and user.status == 'pending':
        db.session.delete(user)
        db.session.commit()
    
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/suspend_user/<int:user_id>')
def admin_suspend_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    user = UserEntity.query.get(user_id)
    if user and user.status == 'active':
        user.status = 'suspended'
        db.session.commit()
    
    return redirect(url_for('dashboard_admin'))

# UTILITY ROUTES
@app.route('/list_users')
def list_users():
    users = UserEntity.query.all()
    return "<br>".join([f"Username: {u.username} - UserID: {u.user_id} - Full Name: {u.fullname} - Role: {u.role}" for u in users])

@app.route('/logout')
def logout():
    return LogoutController.logout()

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print("📡 Access your web at: http://127.0.0.1:5000")
    app.run(debug=True)