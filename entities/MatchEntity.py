# entities/MatchEntity.py
from datetime import datetime
from entities.UserEntity import db


class MatchEntity(db.Model):
    __tablename__ = 'matches'
    match_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pin_request_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    assigned_by_id = db.Column(db.Integer, nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='confirmed')

    def __repr__(self):
        return f"<Match #{self.match_id} pin={self.pin_request_id} user={self.user_id} status={self.status}>"
