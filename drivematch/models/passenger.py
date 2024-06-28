from sqlalchemy import (
    Column,
    Integer,
    ForeignKey
)
from drivematch.models.user import User


class Passenger(User):
    __tablename__ = 'passageiros'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    qtd_travels = Column(Integer, default=0)

    __mapper_args__ = {
        'polymorphic_identity': 'passageiro',
    }

    def __repr__(self):
        return (
            f"<Passageiro(id={self.id}, username={self.username}, "
            f"qtd_travels={self.qtd_travels})>"
        )

    def to_dict(self):
        user_dict = super().to_dict()
        user_dict.update({
            'qtd_travels': self.qtd_travels
        })
        return user_dict
