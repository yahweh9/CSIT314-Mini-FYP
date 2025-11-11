# entities/PlatformInfo.py
from .UserEntity import db

class PlatformInfo(db.Model):
    __tablename__ = 'platform_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    csrPurpose = db.Column(db.String(500), nullable=False)
    features = db.Column(db.String(500), nullable=False)
    roles = db.Column(db.String(500), nullable=False)
    impactStories = db.Column(db.String(1000), nullable=True)

    def __repr__(self):
        return f"<PlatformInfo(id={self.id}, purpose='{self.csrPurpose[:30]}...')>"