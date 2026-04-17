import logging
import asyncio
from datetime import datetime
from drivematch.models.user import User
from drivematch.models.driver import Driver
from drivematch.models.passenger import Passenger
from drivematch.models.payout_request import PayoutRequest, PayoutStatus
from drivematch.models.review import Review
from drivematch.models.system_settings import SystemSettings
from drivematch.models.travel import (
    Travel,
    TravelStatus
)
from drivematch.utils.database import (
    session_scope
)
from sqlalchemy import desc, func
import sqlalchemy as sa
from geoalchemy2 import Geography

logging.basicConfig(level=logging.INFO)


class UserController:
    async def update_user_location(self, user_id, lat, lon):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                # O PostGIS usa (Longitude, Latitude) no WKT POINT
                try:
                    user.location = f'SRID=4326;POINT({lon} {lat})'
                    session.commit()
                    session.refresh(user)
                    logging.info(f'Localização do usuário {user_id} atualizada no BD.')
                except Exception as e:
                    logging.error(f"Erro ao atualizar localização no BD: {e}")

    async def find_nearby_drivers(self, lat, lon, radius_km=10.0):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        if lat is None or lon is None:
            return []

        with session_scope() as session:
            try:
                # Ponto de referência WKT - SRID 4326
                point = f'SRID=4326;POINT({lon} {lat})'

                # Query usando ST_DWithin (distância em metros)
                # Convertemos para Geography para garantir precisão em metros no SRID 4326

                drivers = session.query(Driver).filter(
                    Driver.is_active == True,
                    User.type == 'motorista',
                    func.ST_DWithin(
                        func.ST_GeographyFromText(point),
                        sa.cast(Driver.location, Geography),
                        radius_km * 1000
                    )
                ).order_by(
                    func.ST_Distance(
                        sa.cast(Driver.location, Geography),
                        func.ST_GeographyFromText(point)
                    )
                ).limit(5).all()  # Pega apenas os 5 mais perto

                return [d.to_dict() for d in drivers]
            except Exception as e:
                logging.error(f"Erro ao buscar motoristas próximos: {e}")
                return []

    async def check_user_exists(self, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                return user.to_dict()
            return None

    async def get_driver_by_id(self, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            driver = session.query(Driver).filter_by(id=user_id).first()
            if driver:
                return driver.to_dict()
            return None

    async def create_user(self, user_type, **kwargs):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            if user_type == 'motorista':
                user = Driver(**kwargs)
            else:
                user = Passenger(**kwargs)
            session.add(user)
            session.commit()
            logging.info(f'{user_type.capitalize()} {user.first_name} criado no banco.')
            return user.to_dict()

    async def update_user(self, user_id, new_username):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.username = new_username
                session.commit()
                logging.info(f'Usuário {user.first_name} atualizado com sucesso!')
            else:
                logging.info('Usuário não encontrado.')

    async def delete_user(self, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        from sqlalchemy import or_
        with session_scope() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                # Remoção em Cascata Manual para evitar Foreign Key Constraint Violation (Reviews, PayoutRequests, Travels)
                session.query(Review).filter(
                    or_(Review.rater_id == user.id, Review.target_id == user.id)
                ).delete(synchronize_session=False)

                session.query(PayoutRequest).filter_by(driver_id=user.id).delete(synchronize_session=False)

                session.query(Travel).filter(
                    or_(Travel.passenger_id == user.id, Travel.driver_id == user.id)
                ).delete(synchronize_session=False)

                session.delete(user)
                session.commit()
                logging.info(f'Usuário {user.first_name} deletado com sucesso!')
                return True
            else:
                logging.info('Usuário não encontrado.')
                return False

    async def edit_user(self, **kwargs):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            user_id = kwargs.get('user_id')
            if kwargs.get('created_at'):
                kwargs.pop('created_at')
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.commit()
                logging.info(f'Usuário {user.first_name} editado com sucesso!')
            else:
                logging.info('Usuário não encontrado.')

    async def create_travel(self, passenger_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            passenger = session.query(Passenger).filter_by(id=passenger_id).first()
            if passenger:
                travel = Travel(passenger_id=passenger.id)
                session.add(travel)
                session.commit()
                logging.info(f'Viagem criada com sucesso para o passageiro {passenger.first_name}.')
                return travel.to_dict()
            else:
                # logging.info("Passageiro não encontrado.")
                return None

    async def accept_travel(self, travel_id, driver_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            driver = session.query(Driver).filter_by(id=driver_id).first()
            if travel and driver and travel.status == TravelStatus.REQUESTING:
                travel.driver_id = driver.id
                travel.status = TravelStatus.ACCEPTED
                session.commit()
                logging.info(f'Viagem {travel.id} aceita pelo motorista {driver.first_name}.')
                return travel.to_dict()
            else:
                logging.info('Viagem ou motorista não encontrado, ou status inválido.')
                return None

    async def cancel_travel(self, travel_id, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel and (travel.passenger_id == user_id or travel.driver_id == user_id):
                travel.status = TravelStatus.CANCELLED
                session.commit()
                logging.info(f'Viagem {travel.id} cancelada pelo usuário {user_id}.')
                return travel.to_dict()
            else:
                logging.info('Viagem não encontrada ou usuário não autorizado.')
                return None

    async def start_travel(self, travel_id, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel and travel.driver_id == user_id and travel.status == TravelStatus.ACCEPTED:
                travel.status = TravelStatus.IN_PROGRESS
                session.commit()
                logging.info(f'Viagem {travel.id} iniciada pelo motorista {user_id}.')
                return travel.to_dict()
            else:
                logging.info('Viagem não encontrada ou status inválido.')
                return None

    async def complete_travel(self, travel_id, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel and travel.driver_id == user_id and travel.status == TravelStatus.IN_PROGRESS:
                travel.status = TravelStatus.COMPLETED
                session.commit()
                logging.info(f'Viagem {travel.id} concluída pelo motorista {user_id}.')
                return travel.to_dict()
            else:
                logging.info('Viagem não encontrada ou status inválido.')
                return None

    async def set_travel_financials(self, travel_id, total, driver_share, platform_share):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel:
                travel.total_amount = total
                travel.driver_amount = driver_share
                travel.platform_amount = platform_share
                session.commit()
                logging.info(
                    f"AUDIT FINANCE: Viagem {travel_id} definida: Total R$ {total}, Motorista R$ {driver_share}")

    async def confirm_payment(self, travel_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel and travel.payment_status == 'pending':
                travel.payment_status = 'paid'

                # Creditar ao motorista e incrementar contadores
                driver = session.query(User).filter_by(id=travel.driver_id).first()
                passenger = session.query(User).filter_by(id=travel.passenger_id).first()

                if driver:
                    driver.balance = (driver.balance or 0.0) + (travel.driver_amount or 0.0)
                    driver.qtd_travels = (driver.qtd_travels or 0) + 1

                if passenger:
                    passenger.qtd_travels = (passenger.qtd_travels or 0) + 1

                session.commit()
                return travel.to_dict()
        return None

    async def get_travel(self, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter(
                (Travel.passenger_id == user_id) | (Travel.driver_id == user_id)
            ).order_by(desc(Travel.created_at)).first()

            if travel:
                return travel.to_dict()
            else:
                logging.info('Viagem não encontrada.')
                return None

    async def get_travel_by_id(self, travel_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            travel = session.query(Travel).filter_by(id=travel_id).first()
            if travel:
                return travel.to_dict()
            return None

    async def add_review(self, travel_id, rater_id, target_id, rating, comment=None):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            # 1. Salvar a Review
            review = Review(
                travel_id=travel_id,
                rater_id=rater_id,
                target_id=target_id,
                rating=rating,
                comment=comment
            )
            session.add(review)

            # 2. Atualizar a média do usuário alvo
            target_user = session.query(User).filter_by(id=target_id).first()
            if target_user:
                target_user.rate(rating)
                logging.info(f"Usuário {target_id} avaliado com nota {rating}.")

            session.commit()
            return review.to_dict()

    # --- Métodos Administrativos ---

    async def get_system_settings(self):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            settings = session.query(SystemSettings).first()
            if not settings:
                # Cria configurações padrão se não existirem
                settings = SystemSettings()
                session.add(settings)
                session.commit()
            return settings.to_dict()

    async def update_system_settings(self, **kwargs):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            settings = session.query(SystemSettings).first()
            if not settings:
                settings = SystemSettings()
                session.add(settings)

            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            session.commit()
            logging.info("Configurações do sistema atualizadas pelo Administrador.")
            return settings.to_dict()

    async def get_admin_stats(self):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            total_users = session.query(func.count(User.id)).scalar()
            total_drivers = session.query(func.count(Driver.id)).scalar()
            total_travels = session.query(func.count(Travel.id)).scalar()

            # Ganhos Totais (Plataforma vs Motoristas)
            financials = session.query(
                func.sum(Travel.total_amount).label('total'),
                func.sum(Travel.platform_amount).label('platform'),
                func.sum(Travel.driver_amount).label('drivers')
            ).filter(Travel.status == TravelStatus.COMPLETED).first()

            return {
                'users_count': total_users,
                'drivers_count': total_drivers,
                'travels_count': total_travels,
                'revenue_total': float(financials.total or 0),
                'revenue_platform': float(financials.platform or 0),
                'revenue_drivers': float(financials.drivers or 0)
            }

    async def get_all_users(self, limit=50, offset=0):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            users = session.query(User).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
            return [u.to_dict() for u in users]

    async def set_driver_custom_fee(self, user_id, percentage):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            driver = session.query(Driver).filter_by(user_id=user_id).first()
            if driver:
                driver.custom_fee_percentage = float(percentage)
                session.commit()
                return True
            return False

    # --- Gestão de Saques (Payouts) ---

    async def request_payout(self, user_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            driver = session.query(Driver).filter_by(user_id=user_id).first()
            if not driver or (driver.balance or 0.0) < 20.0:
                return False, "Saldo insuficiente (Mínimo R$ 20,00)."

            # Verifica se já existe um pedido pendente
            existing = session.query(PayoutRequest).filter_by(
                driver_id=driver.id, status=PayoutStatus.PENDING
            ).first()
            if existing:
                return False, "Você já possui uma solicitação em análise."

            request = PayoutRequest(
                driver_id=driver.id,
                amount=driver.balance,
                pix_key=driver.pix_key or "Não informada"
            )
            session.add(request)
            session.commit()
            return True, f"Solicitação de R$ {driver.balance:.2f} enviada com sucesso!"

    async def list_pending_payouts(self):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            requests = session.query(PayoutRequest).filter_by(status=PayoutStatus.PENDING).all()
            return [r.to_dict() for r in requests]

    async def confirm_payout(self, request_id):
        await asyncio.sleep(0)  # Yield explicitly to event loop since SQLAlchemy is sync
        with session_scope() as session:
            request = session.query(PayoutRequest).filter_by(id=request_id).first()
            if request and request.status == PayoutStatus.PENDING:
                driver = session.query(User).filter_by(id=request.driver_id).first()
                if driver:
                    # Deduz o saldo apenas na confirmação do pagamento
                    driver.balance = (driver.balance or 0.0) - request.amount
                    request.status = PayoutStatus.PAID
                    request.processed_at = datetime.utcnow()
                    session.commit()
                    return True, driver.user_id
            return False, None
