from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String
)
from drivematch.models.user import User


class Driver(User):
    __tablename__ = 'motoristas'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    pix_key = Column(String, nullable=True)
    type_vehicle = Column(String, nullable=True)
    plate = Column(String, nullable=True)
    qtd_travels = Column(Integer, default=0)

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
            'plate': self.plate,
            'qtd_travels': self.qtd_travels
        })
        return user_dict
