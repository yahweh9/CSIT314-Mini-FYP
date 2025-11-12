# entities/RequestViewEntity.py
from .UserEntity import db
from datetime import datetime

class RequestViewEntity(db.Model):
    __tablename__ = 'request_views'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(10), db.ForeignKey('pin_requests.request_id'), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
