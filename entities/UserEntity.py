# entities/UserEntity.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserEntity(db.Model):
    __tablename__ = 'users'  # Changed to single table 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) # Hashed Password (Not plain)
    role = db.Column(db.String(20), nullable=False)  # 'pm', 'admin', 'pin', 'csrrep', 'cv'
    fullname = db.Column(db.String(80))
    email = db.Column(db.String(80))
    status = db.Column(db.String(20), default='active')  # 'active', 'pending', 'suspended'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional fields depending on role
    address = db.Column(db.String(100))  # for PINs
    phone = db.Column(db.String(20))     # for PINs
    company = db.Column(db.String(100))  # for CSRRep or CVs
    department = db.Column(db.String(100))  # for CVs

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}', status='{self.status}')>"
    
    # Helper methods for role checking
    def is_platform_manager(self):
        return self.role == 'pm'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_pin(self):
        return self.role == 'pin'
    
    def is_csr_rep(self):
        return self.role == 'csrrep'
    
    def is_corporate_volunteer(self):
        return self.role == 'cv'
    
    def requires_approval(self):
        # PIN and CV accounts require admin approval
        return self.role in ['pin', 'cv'] and self.status == 'pending'

