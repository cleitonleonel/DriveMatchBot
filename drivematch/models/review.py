from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)
from drivematch.utils.database import Base
from datetime import datetime


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    travel_id = Column(Integer, ForeignKey('travels.id'), nullable=False)
    rater_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Review(id={self.id}, travel_id={self.travel_id}, "
            f"rating={self.rating})>"
        )

    def to_dict(self):
        return {
            'id': self.id,
            'travel_id': self.travel_id,
            'rater_id': self.rater_id,
            'target_id': self.target_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
