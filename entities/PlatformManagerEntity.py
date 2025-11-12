# entity/PlatformManagerEntity.py
from .UserEntity import UserEntity

class PlatformManagerEntity(UserEntity):
    __tablename__ = 'platform_manager'
    __mapper_args__ = {'polymorphic_identity': 'pm'}