from .UserEntity import UserEntity

class CSRRepEntity(UserEntity):
    __tablename__ = 'csr_rep'
    __mapper_args__ = {'polymorphic_identity': 'csrrep'}