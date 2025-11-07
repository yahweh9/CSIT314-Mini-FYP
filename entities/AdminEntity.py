from .UserEntity import UserEntity

class AdminEntity(UserEntity):
    __tablename__ = 'admin'
    __mapper_args__ = {'polymorphic_identity': 'admin'}