# entities/PINEntity.py
from .UserEntity import UserEntity

class PINEntity(UserEntity):
    __tablename__ = 'pin'
    __mapper_args__ = {'polymorphic_identity': 'pin'}