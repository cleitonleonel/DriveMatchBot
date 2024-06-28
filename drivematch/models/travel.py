from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.orm import (
    relationship
)
from drivematch.utils.database import Base
from datetime import datetime
import enum


class TravelStatus(enum.Enum):
    REQUESTING = "requesting"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Travel(Base):
    __tablename__ = 'travels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    passenger_id = Column(Integer, ForeignKey('users.id'))
    driver_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(Enum(TravelStatus), default=TravelStatus.REQUESTING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    passenger = relationship('Passenger', foreign_keys=[passenger_id], backref='travels')
    driver = relationship('Driver', foreign_keys=[driver_id], backref='travels')

    def __repr__(self):
        return (
            f"<Travel(id={self.id}, passenger_id={self.passenger_id}, "
            f"driver_id={self.driver_id}, status={self.status.value})>"
        )

    def to_dict(self):
        return {
            'id': self.id,
            'passenger': self.passenger.to_dict() if self.passenger else None,
            'driver': self.driver.to_dict() if self.driver else None,
            'created_at': (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status.value
        }
