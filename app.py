from flask import Flask, render_template, url_for, request, redirect, session
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ONLY import UserEntity - remove the others!
from entities.UserEntity import db, UserEntity
from controllers.LoginController import LoginController
from controllers.RegisterController import RegisterController

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
    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']

        if LoginController.authenticateUser(input_username, input_password):
            user = LoginController.findUserByUsername(input_username)
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.user_id
            
            # Redirect based on role
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
            return "<script>alert('Wrong username or password!'); window.location.href='/';</script>"
        
    return render_template('login.html')

# FIXED DASHBOARD ROUTES - Use UserEntity with role filter
@app.route('/dashboard_pin')
def dashboard_pin():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='pin').first()
    return render_template('dashboard_pin.html', user=user)

@app.route('/dashboard_csrrep')
def dashboard_csrrep():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='csrrep').first()
    return render_template('dashboard_csrrep.html', user=user)

@app.route('/dashboard_cv')
def dashboard_cv():
    if 'username' not in session:
        return redirect('/')
    user = UserEntity.query.filter_by(username=session['username'], role='cv').first()
    return render_template('dashboard_cv.html', user=user)

@app.route('/dashboard_platform_manager')
def dashboard_platform_manager():
    if 'username' not in session:
        return redirect('/')
    users = UserEntity.query.all()
    total_users = len(users)
    return render_template('dashboard_platform_manager.html', users=users, total_users=total_users)

@app.route('/dashboard_admin')
def dashboard_admin():
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

# Keep your registration routes the same...
@app.route('/register_admin', methods=['GET','POST'])
def register_admin():
    return RegisterController.register_admin()

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
    if request.method == 'POST':
        if 'role' in session and session['role'].lower() == 'pm':
            return redirect(url_for('dashboard_platform_manager'))
        elif 'role' in session and session['role'].lower() == 'admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('login_page'))
    return render_template('successful_registration.html')

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