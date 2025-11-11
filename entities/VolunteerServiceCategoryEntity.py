# entities/VolunteerServiceCategoryEntity.py
from .UserEntity import db
from datetime import datetime

class VolunteerServiceCategoryEntity(db.Model):
    __tablename__ = "volunteer_service_categories"

    id = db.Column(db.Integer, primary_key=True)
    # unique (case-insensitive handled in controller)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<VolunteerServiceCategory(id={self.id}, name='{self.name}', active={self.is_active})>"
