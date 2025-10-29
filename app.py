from flask import Flask, render_template, url_for, request, redirect, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Boundaries
from boundaries.web_boundary import display_login_page, display_register_admin, display_successful_registration
from boundaries.pin_boundary import display_dashboard_pin
from boundaries.csrrep_boundary import display_dashboard_csrrep
from boundaries.cv_boundary import display_dashboard_cv, display_history_cv
from boundaries.admin_boundary import display_dashboard_admin
from boundaries.platform_manager_boundary import display_dashboard_platform_manager

# Controllers
from controllers.LoginController import LoginController
from controllers.RegisterController import RegisterController

# Entities
# ONLY import UserEntity - remove the others!
from entities.UserEntity import db, UserEntity

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

# FIXED DASHBOARD ROUTES - Use UserEntity with role filter
@app.route('/dashboard_pin')
def dashboard_pin():
    return display_dashboard_pin()

@app.route('/dashboard_csrrep')
def dashboard_csrrep():
    return display_dashboard_csrrep()

@app.route('/dashboard_cv')
def dashboard_cv():
    return display_dashboard_cv()

@app.route('/history_cv')
def history_cv():
    return display_history_cv()

@app.route('/dashboard_platform_manager')
def dashboard_platform_manager():
    return display_dashboard_platform_manager()

@app.route('/dashboard_admin')
def dashboard_admin():
    return display_dashboard_admin()

# Keep your registration routes the same...
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

@app.route('/admin/create_csr_rep', methods=['GET', 'POST'])
def admin_create_csr_rep():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect('/')
    
    if request.method == 'POST':
        # Simple CSR Rep creation without using RegisterController
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

@app.route('/list_users')
def list_users():
    users = UserEntity.query.all()
    return "<br>".join([f"Username: {u.username} - UserID: {u.user_id} - Full Name: {u.fullname} - Role: {u.role}" for u in users])

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('user_id', None)
    return redirect('/')

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print("📡 Access your web at: http://127.0.0.1:5000")
    app.run(debug=True)