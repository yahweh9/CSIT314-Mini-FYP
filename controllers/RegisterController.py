from flask import render_template, request, session
from werkzeug.security import generate_password_hash

#from test import db
from entities.UserEntity import db

from entities.UserEntity import UserEntity
from entities.AdminEntity import AdminEntity
from entities.PlatformManagerEntity import PlatformManagerEntity
from entities.PINEntity import PINEntity
from entities.CSRRepEntity import CSRRepEntity
from entities.CorporateVolunteerEntity import CorporateVolunteerEntity

class RegisterController:

    @staticmethod
    def register_admin():
        register_username = request.form['username']
        register_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(register_username) < 5 or len(register_password) < 5:
            return "<script>alert('Username and password must be at least 5 characters long!'); window.location.href='/register_admin';</script>"
        
        if register_password != confirm_password:
            return "<script>alert('Passwords do not match!'); window.location.href='/register_admin';</script>"

        existing_user = UserEntity.query.filter_by(username=register_username).first()
        if existing_user:
            return "<script>alert('Username already exists!'); window.location.href='/register_admin';</script>"
        
        hashed_pw = generate_password_hash(register_password, method='pbkdf2:sha256')
        new_admin = UserEntity(username=register_username, password=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        return True



    @staticmethod
    def register_pin():
        if request.method == 'POST':
            register_username = request.form['username']
            register_password = request.form['password']
            confirm_password = request.form['confirm_password']

            if len(register_username) < 5 or len(register_password) < 5:
                return "<script>alert('Username and password must be at least 5 characters long!'); window.location.href='/register_pin';</script>"
            
            if register_password != confirm_password:
                return "<script>alert('Passwords do not match!'); window.location.href='/register_pin';</script>"

            existing_user = UserEntity.query.filter_by(username=register_username).first()
            if existing_user:
                return "<script>alert('Username already exists!'); window.location.href='/register_pin';</script>"

            hashed_pw = generate_password_hash(register_password, method='pbkdf2:sha256')
            session['temp_username'] = register_username
            session['temp_role'] = 'pin'
            session['temp_password'] = hashed_pw
            return render_template('register_info_pin.html')
        return render_template('register_pin.html')

    @staticmethod
    def register_csrrep_or_cv():
        if request.method == 'POST':
            register_username = request.form['username']
            register_password = request.form['password']
            confirm_password = request.form['confirm_password']

            if len(register_username) < 5 or len(register_password) < 5:
                return "<script>alert('Username and password must be at least 5 characters long!'); window.location.href='/register_csrrep_or_cv';</script>"
            
            if register_password != confirm_password:
                return "<script>alert('Passwords do not match!'); window.location.href='/register_csrrep_or_cv';</script>"

            existing_user = UserEntity.query.filter_by(username=register_username).first()
            if existing_user:
                return "<script>alert('Username already exists!'); window.location.href='/register_csrrep_or_cv';</script>"

            hashed_pw = generate_password_hash(register_password, method='pbkdf2:sha256')
            register_role = request.form['role']
            session['temp_username'] = register_username
            session['temp_role'] = register_role
            session['temp_password'] = hashed_pw

            if register_role.lower() == 'csrrep':
                return render_template('register_info_csrrep.html')
            elif register_role.lower() == 'cv':
                return render_template('register_info_cv.html')
        return render_template('register_csrrep_or_cv.html')

    @staticmethod
    def register_info_platform_manager(pmUsername, pmPassword):
        existing_admin = UserEntity.query.filter_by(username=pmUsername).first()
        if existing_admin:
            print(f"Platform Manager {pmUsername} already exists.")
            return None

        new_pm = UserEntity(
            username=pmUsername,
            password=generate_password_hash(pmPassword, method='pbkdf2:sha256'),
            role='pm'
        )
        db.session.add(new_pm)
        db.session.commit()
        return new_pm

    @staticmethod
    def register_info_cv():
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            org = request.form['org']

            if '@' not in email or '.' not in email:
                return "<script>alert('Please enter a valid email!'); window.location.href='/register_info_cv';</script>"

            new_user = CorporateVolunteerEntity(
                username=session['temp_username'],
                password=session['temp_password'],
                role=session['temp_role'],
                fullname=fullname,
                email=email,
                org=org
            )
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

            new_user = CSRRepEntity(
                username=session['temp_username'],
                password=session['temp_password'],
                role=session['temp_role'],
                fullname=fullname,
                email=email,
                org=org
            )
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

            new_user = PINEntity(
                username=session['temp_username'],
                password=session['temp_password'],
                role=session['temp_role'],
                fullname=fullname,
                email=email,
                address=address
            )
            db.session.add(new_user)
            db.session.commit()
            return render_template('successful_registration.html')
        return render_template('register_info_pin.html')
