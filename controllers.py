# Controllers
from flask import Flask, render_template, url_for, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, AdminEntity, UserEntity, PINEntity, CSRRepEntity, CorporateVolunteerEntity

class LoginController:
    @staticmethod
    def findUserByUsername(username):
        user = (
            CSRRepEntity.query.filter_by(username=username).first()
            or PINEntity.query.filter_by(username=username).first()
            or CorporateVolunteerEntity.query.filter_by(username=username).first()
            or AdminEntity.query.filter_by(username=username).first()
        )
        return user
    
    @staticmethod
    def authenticateUser(input_username, input_password):
        # Temporarily for admins
        
        if not input_username.strip() or not input_password.strip():
            return False
        
        # check credentials here
        user = LoginController.findUserByUsername(input_username)
        print("User found:", user)  # Debug line
        print("Input password:", input_password) # Debug line
        
        if user and check_password_hash(user.password, input_password):
            return True

class RegisterController:
    @staticmethod
    def register():
        if request.method == 'POST':
            register_username = request.form['username']
            register_password = request.form['password']
            confirm_password = request.form['confirm_password']

            if len(register_username) < 5 or len(register_password) < 5:
                return "<script>alert('Username and password must be at least 5 characters long!'); window.location.href='/register';</script>"
            
            if register_password != confirm_password:
                return "<script>alert('Passwords do not match!'); window.location.href='/register';</script>"

            # check if username already exists
            existing_user = UserEntity.query.filter_by(username=register_username).first()


            if existing_user:
                return "<script>alert('Username already exists!'); window.location.href='/register';</script>"
            
            hashed_pw = generate_password_hash(register_password, method='pbkdf2:sha256')
            register_role = request.form['role']  # get selected role from dropdown
            print('Registered Role:', register_role)

            session['temp_username'] = register_username
            session['temp_role'] = register_role
            session['temp_password'] = hashed_pw

            if register_role.lower() == 'pin':
                return render_template('register_info_pin.html')
            
            elif register_role.lower() == 'csrrep':
                return render_template('register_info_csrrep.html')
            
            elif register_role.lower() == 'cv':
                return render_template('register_info_cv.html')

        return render_template('register.html')

    @staticmethod
    def register_info_admin(adminUsername, adminPassword):
        # Check if username already exists
        existing_admin = UserEntity.query.filter_by(username=adminUsername).first()
        if existing_admin:
            print("Admin already exists.")
            return None

        # Create new admin user
        new_admin = UserEntity(
            username=adminUsername,
            password=generate_password_hash(adminPassword, method='pbkdf2:sha256'),
            role='admin',
            fullname='Admin',        
            email='admin@cvconnect.com'  
        )

        db.session.add(new_admin)
        db.session.commit()
        print("Admin created successfully.")
        return new_admin



    @staticmethod
    def register_info_cv():
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            org = request.form['org']

            if '@' not in email or '.' not in email:
                return "<script>alert('Please enter a valid email!'); window.location.href='/register_info_cv';</script>"
            if len(org) < 2:
                return "<script>alert('Organisation too short!'); window.location.href='/register_info_cv';</script>"
            elif len(org) > 40:
                return "<script>alert('Organisation too long!'); window.location.href='/register_info_cv';</script>"

            register_username = session['temp_username']
            hashed_password = session['temp_password']
            register_role = session['temp_role']

            new_user = CorporateVolunteerEntity(
                username = register_username, 
                password = hashed_password, 
                role = register_role, 
                fullname = fullname,
                email = email,
                org = org)

            db.session.add(new_user)
            db.session.commit()
    
            return render_template('successful_registration.html')
        return render_template('register_info_cv.html')
    
    @staticmethod
    def register_info_csrrep():
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            org = request.form['org']

            if '@' not in email or '.' not in email:
                return "<script>alert('Please enter a valid email!'); window.location.href='/register_info_csrrep';</script>"
            if len(org) < 2:
                return "<script>alert('Organisation too short!'); window.location.href='/register_info_csrrep';</script>"
            elif len(org) > 40:
                return "<script>alert('Organisation too long!'); window.location.href='/register_info_csrrep';</script>"

            register_username = session['temp_username']
            hashed_password = session['temp_password']
            register_role = session['temp_role']

            new_user = CSRRepEntity(
                username = register_username, 
                password = hashed_password, 
                role = register_role, 
                fullname = fullname,
                email = email,
                org = org)

            db.session.add(new_user)
            db.session.commit()
    
            return render_template('successful_registration.html')
        return render_template('register_info_csrrep.html')
    
    @staticmethod
    def register_info_pin():
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            address = request.form['address']

            if '@' not in email or '.' not in email:
                return "<script>alert('Please enter a valid email!'); window.location.href='/register_info_pin';</script>"
            elif len(address) < 3:
                return "<script>alert('Address is too short!'); window.location.href='/register_info_pin';</script>"
            elif len(address) > 60:
                return "<script>alert('Address is too long!'); window.location.href='/register_info_pin';</script>"
            
            register_username = session['temp_username']
            hashed_password = session['temp_password']
            register_role = session['temp_role']

            new_user = PINEntity(
                username = register_username, 
                password = hashed_password, 
                role = register_role, 
                fullname = fullname,
                email = email,
                address = address
                )

            db.session.add(new_user)
            db.session.commit()
    
            return render_template('successful_registration.html')
        return render_template('register_info_pin.html')