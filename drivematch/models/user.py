from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float
)
from drivematch.utils.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, unique=False, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    average_rating = Column(Float, default=0)
    num_ratings = Column(Integer, default=0)

    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __repr__(self):
        return (
            f"<User(id={self.id}, username={self.username}, "
            f"first_name={self.first_name}, last_name={self.last_name})>"
        )

    def rate(self, rating):
        total = self.average_rating * self.num_ratings
        self.num_ratings += 1
        self.average_rating = (total + rating) / self.num_ratings

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'average_rating': self.average_rating,
            'num_ratings': self.num_ratings,
            'type': self.type
        }
