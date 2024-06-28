import logging
from drivematch.models.user import User
from drivematch.models.driver import Driver
from drivematch.models.passenger import Passenger
from drivematch.models.travel import (
    Travel,
    TravelStatus
)
from drivematch.utils.database import (
    Session,
    desc
)

logging.basicConfig(level=logging.INFO)


class UserController:
    session = Session()

    def check_user_exists(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            return user.to_dict()
        else:
            logging.info('Usuário não encontrado.')
            return None

    def create_user(self, user_type, **kwargs):
        if user_type == 'motorista':
            user = Driver(**kwargs)
        else:
            user = Passenger(**kwargs)
        self.session.add(user)
        self.session.commit()
        logging.info(f'{user_type.capitalize()} {user.first_name} criado com sucesso!')

    def update_user(self, user_id, new_username):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.username = new_username
            self.session.commit()
            logging.info(f'Usuário {user.first_name} atualizado com sucesso!')
        else:
            logging.info('Usuário não encontrado.')

    def delete_user(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            logging.info(f'Usuário {user.first_name} deletado com sucesso!')
            return True
        else:
            logging.info('Usuário não encontrado.')

    def edit_user(self, **kwargs):
        user_id = kwargs.get('user_id')
        if kwargs.get('created_at'):
            kwargs.pop('created_at')
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.session.commit()
            logging.info(f'Usuário {user.first_name} editado com sucesso!')
        else:
            logging.info('Usuário não encontrado.')

    def create_travel(self, passenger_id):
        passenger = self.session.query(Passenger).filter_by(id=passenger_id).first()
        if passenger:
            travel = Travel(passenger_id=passenger.id)
            self.session.add(travel)
            self.session.commit()
            logging.info(f'Viagem criada com sucesso para o passageiro {passenger.first_name}.')
            return travel.to_dict()
        else:
            # logging.info("Passageiro não encontrado.")
            return None

    def accept_travel(self, travel_id, driver_id):
        travel = self.session.query(Travel).filter_by(id=travel_id).first()
        driver = self.session.query(Driver).filter_by(id=driver_id).first()
        if travel and driver and travel.status == TravelStatus.REQUESTING:
            travel.driver_id = driver.id
            travel.status = TravelStatus.ACCEPTED
            self.session.commit()
            logging.info(f'Viagem {travel.id} aceita pelo motorista {driver.first_name}.')
            return travel.to_dict()
        else:
            logging.info('Viagem ou motorista não encontrado, ou status inválido.')
            return None

    def cancel_travel(self, travel_id, user_id):
        travel = self.session.query(Travel).filter_by(id=travel_id).first()
        if travel and (travel.passenger_id == user_id or travel.driver_id == user_id):
            travel.status = TravelStatus.CANCELLED
            self.session.commit()
            logging.info(f'Viagem {travel.id} cancelada pelo usuário {user_id}.')
            return travel.to_dict()
        else:
            logging.info('Viagem não encontrada ou usuário não autorizado.')
            return None

    def start_travel(self, travel_id, user_id):
        travel = self.session.query(Travel).filter_by(id=travel_id).first()
        if travel and travel.driver_id == user_id and travel.status == TravelStatus.ACCEPTED:
            travel.status = TravelStatus.IN_PROGRESS
            self.session.commit()
            logging.info(f'Viagem {travel.id} iniciada pelo motorista {user_id}.')
            return travel.to_dict()
        else:
            logging.info('Viagem não encontrada ou status inválido.')
            return None

    def complete_travel(self, travel_id, user_id):
        travel = self.session.query(Travel).filter_by(id=travel_id).first()
        if travel and travel.driver_id == user_id and travel.status == TravelStatus.IN_PROGRESS:
            travel.status = TravelStatus.COMPLETED
            self.session.commit()
            logging.info(f'Viagem {travel.id} concluída pelo motorista {user_id}.')
            return travel.to_dict()
        else:
            logging.info('Viagem não encontrada ou status inválido.')
            return None

    def get_travel(self, user_id):
        travel = self.session.query(Travel).filter(
            (Travel.passenger_id == user_id) | (Travel.driver_id == user_id)
        ).order_by(desc(Travel.created_at)).first()

        if travel:
            return travel.to_dict()
        else:
            logging.info('Viagem não encontrada.')
            return None
