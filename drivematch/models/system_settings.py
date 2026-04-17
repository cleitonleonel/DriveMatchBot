from sqlalchemy import Column, Integer, Float
from drivematch.utils.database import Base


class SystemSettings(Base):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True)

    # Taxas de Corrida
    base_fare = Column(Float, default=2.0)
    price_per_km = Column(Float, default=0.71)
    price_per_min = Column(Float, default=0.42)
    service_fee = Column(Float, default=0.75)

    # Divisão de Ganhos
    default_platform_percentage = Column(Float, default=20.0)  # ex: 20%

    # Outras Configurações
    search_radius_km = Column(Float, default=10.0)

    def to_dict(self):
        return {
            'base_fare': self.base_fare,
            'price_per_km': self.price_per_km,
            'price_per_min': self.price_per_min,
            'service_fee': self.service_fee,
            'default_platform_percentage': self.default_platform_percentage,
            'search_radius_km': self.search_radius_km
        }
