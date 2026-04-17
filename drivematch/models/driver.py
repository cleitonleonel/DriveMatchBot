from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Float
)
from drivematch.models.user import User


class Driver(User):
    __tablename__ = 'motoristas'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    pix_key = Column(String, nullable=True)
    type_vehicle = Column(String, nullable=True)
    plate = Column(String, nullable=True)

    # Taxa customizada para este motorista (ex: 15.0). Se None, usa o padrão do sistema.
    custom_fee_percentage = Column(Float, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'motorista',
    }

    def __repr__(self):
        return (
            f"<Motorista(id={self.id}, username={self.username}, "
            f"type_vehicle={self.type_vehicle})>"
        )

    def to_dict(self):
        user_dict = super().to_dict()
        user_dict.update({
            'pix_key': self.pix_key,
            'type_vehicle': self.type_vehicle,
            'plate': self.plate
        })
        return user_dict
