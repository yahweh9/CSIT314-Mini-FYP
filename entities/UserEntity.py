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
