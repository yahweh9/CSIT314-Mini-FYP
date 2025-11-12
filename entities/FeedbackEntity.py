# entities/FeedbackEntity.py
from datetime import datetime
from .UserEntity import db

class FeedbackEntity(db.Model):
    __tablename__ = 'feedbacks'
    
    feedback_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(10), nullable=False)
    pin_id = db.Column(db.Integer, nullable=False)
    rated_user_id = db.Column(db.Integer, nullable=False)
    rated_user_role = db.Column(db.String(10), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, request_id, pin_id, rated_user_id, rated_user_role, rating, comments):
        self.request_id = request_id
        self.pin_id = pin_id
        self.rated_user_id = rated_user_id
        self.rated_user_role = rated_user_role
        self.rating = rating
        self.comments = comments

    def __repr__(self):
        return f"<Feedback {self.feedback_id} for request {self.request_id}>"
    
    @classmethod
    def get_feedback_rating(cls, request_id):
        """Return the rating for a given request_id, or None if no feedback exists."""
        feedback = cls.query.filter_by(request_id=request_id).first()
        return feedback.rating if feedback else None