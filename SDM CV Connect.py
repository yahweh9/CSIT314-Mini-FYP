from flask import Flask, render_template, url_for, request, redirect, session
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, AdminEntity, UserEntity, PINEntity, CSRRepEntity, CorporateVolunteerEntity
from controllers import LoginController, RegisterController

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db.init_app(app)

app.secret_key = 'fj39fj_29f9@1nfa91'

with app.app_context():
    db.create_all()

@app.route('/', methods=['POST', 'GET'])                                         
def login_page():

    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']

        if LoginController.authenticateUser(input_username, input_password):
            user = LoginController.findUserByUsername(input_username)

            session['username'] = user.username
            session['role'] = user.role
            print(session['role'])
            if user.role.lower() == 'pm':  
                return redirect(url_for('dashboard_platform_manager'))
            elif user.role.lower() == 'admin':
                return redirect(url_for('dashboard_admin'))
            elif user.role.lower() == 'pin':
                return redirect(url_for('dashboard_pin'))
            elif user.role.lower() == 'csrrep':
                return redirect(url_for('dashboard_csrrep'))
            elif user.role.lower() == 'cv':
                return redirect(url_for('dashboard_cv'))
        else:
            return "<script>alert('Wrong username or password!'); window.location.href='/';</script>"
        
    return render_template('login.html')

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
        
    # for GET request
    return render_template('successful_registration.html')

@app.route('/list_users')
def list_users():
    users = UserEntity.query.all()

    return "<br>".join([f"Username: {u.username} - UserID: {u.user_id} - Full Name: {u.fullname} - Role: {u.role}" for u in users])

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')



@app.route('/dashboard_platform_manager')
def dashboard_platform_manager():
    if 'username' not in session:
        return redirect('/')
    
    # Example: Fetch data to show on dashboard
    users = UserEntity.query.all()
    total_users = len(users)

    # Pass it to the template
    return render_template('dashboard_platform_manager.html', users=users, total_users=total_users)
 

@app.route('/dashboard_admin')
def dashboard_admin():
    if 'username' not in session:
        return redirect('/')
    
    # Example: Fetch data to show on dashboard
    users = UserEntity.query.all()
    total_users = len(users)

    # Pass it to the template
    return render_template('dashboard_admin.html', users=users, total_users=total_users)
    #return render_template('dashboard_admin.html')

@app.route('/dashboard_pin')
def dashboard_pin():
    if 'username' not in session:
        return redirect('/')
    user = PINEntity.query.filter_by(username=session['username']).first()
    return render_template('dashboard_pin.html', user=user)

@app.route('/dashboard_csrrep')
def dashboard_csrrep():
    if 'username' not in session:
        return redirect('/')
    user = CSRRepEntity.query.filter_by(username=session['username']).first()
    return render_template('dashboard_csrrep.html', user=user)

@app.route('/dashboard_cv')
def dashboard_cv():
    if 'username' not in session:
        return redirect('/')
    user = CorporateVolunteerEntity.query.filter_by(username=session['username']).first()
    return render_template('dashboard_cv.html', user=user)


if __name__ == "__main__":
    with app.app_context():
        PM1 = RegisterController.register_info_platform_manager('pm001', 'password')
    app.run(debug=True)