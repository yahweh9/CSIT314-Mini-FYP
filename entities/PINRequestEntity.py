#entity/PINRequestEntity.py

from entities.UserEntity import db
from datetime import datetime

class PINRequestEntity(db.Model):
    __tablename__ = 'pin_requests'

    request_id = db.Column(db.String(10), primary_key=True)
    requested_by_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)

    assigned_to_id = db.Column(db.Integer)
    assigned_by_id = db.Column(db.Integer)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending') # Statuses:[pending, active, completed, expired]]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        last_request = db.session.query(PINRequestEntity).order_by(PINRequestEntity.request_id.desc()).first()
        if last_request:
            num = int(last_request.request_id[1:]) + 1
        else:
            num = 1
        self.request_id = f"r{num:03d}"

    def __repr__(self):
        return f"<PINRequest(id={self.request_id}, title='{self.title}', status='{self.status}')>"

