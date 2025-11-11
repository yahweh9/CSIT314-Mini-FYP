# entities/ShortlistEntity.py
from .UserEntity import db
from datetime import datetime

class ShortlistEntity(db.Model):
    """Store CSR Rep's shortlisted opportunities"""
    __tablename__ = 'shortlist'
    
    shortlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.String(10), db.ForeignKey('pin_requests.request_id'), nullable=False)
    csrrep_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate shortlists
    __table_args__ = (
        db.UniqueConstraint('request_id', 'csrrep_id', name='unique_shortlist'),
    )
    
    def __repr__(self):
        return f"<Shortlist(request={self.request_id}, csrrep={self.csrrep_id})>"