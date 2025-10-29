# DO NOT USE!

'''# Entities
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserEntity(db.Model):
    __tablename__ = 'user_entity'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'pin', 'csrrep', 'cv'
    fullname = db.Column(db.String(80))
    email = db.Column(db.String(80))

    # Optional fields depending on role
    address = db.Column(db.String(100))  # for PINs
    org = db.Column(db.String(100))      # for CSRRep or CVs

    def __repr__(self):
        return f"<UserEntity(id={self.user_id}, username='{self.username}', role='{self.role}')>"

class PlatformManagerEntity(UserEntity):
    __tablename__ = 'platform_manager'

class AdminEntity(UserEntity):
    __tablename__ = 'admin'

class PINEntity(UserEntity):
    __tablename__ = 'pin'

class CSRRepEntity(UserEntity):
    __tablename__ = 'csr_rep'

class CorporateVolunteerEntity(UserEntity):
    __tablename__ = 'corporate_volunteer'


'''