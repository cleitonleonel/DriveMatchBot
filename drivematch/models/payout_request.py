from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum as SqlEnum
from drivematch.utils.database import Base
from datetime import datetime
import enum


class PayoutStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PayoutRequest(Base):
    __tablename__ = 'payout_requests'

    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    pix_key = Column(String, nullable=False)
    status = Column(SqlEnum(PayoutStatus), default=PayoutStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'amount': self.amount,
            'pix_key': self.pix_key,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
