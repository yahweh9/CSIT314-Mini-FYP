# entities/PINRequestEntity.py
from .UserEntity import db
from datetime import datetime

class PINRequestEntity(db.Model):
    __tablename__ = 'pin_requests'

    request_id = db.Column(db.String(10), primary_key=True)
    requested_by_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    completed_date = db.Column(db.DateTime) # Date that CV completed the request
    description = db.Column(db.Text)
    
    # Service details - MAKE SURE THESE EXIST
    service_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    urgency = db.Column(db.String(20), default='medium')
    skills_required = db.Column(db.String(200))
    
    # Assignment info
    assigned_to_id = db.Column(db.Integer)
    assigned_by_id = db.Column(db.Integer)
    
    # Tracking metrics  
    status = db.Column(db.String(20), default='pending') # [pending, active, completed]
    view_count = db.Column(db.Integer, default=0)
    shortlist_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        last_request = PINRequestEntity.query.order_by(PINRequestEntity.request_id.desc()).first()
        if last_request:
            num = int(last_request.request_id[1:]) + 1
        else:
            num = 1
        self.request_id = f"r{num:03d}"

    def __repr__(self):
        return f"<PINRequest(id={self.request_id}, title='{self.title}', status='{self.status}')>"