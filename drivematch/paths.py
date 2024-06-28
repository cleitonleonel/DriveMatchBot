import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_NAME = os.path.basename(BASE_DIR)
HANDLER_DIR = os.path.join(BASE_NAME, 'handlers')
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
CLIENTS_DIR = os.path.join(SESSIONS_DIR, 'clients')


def get_session_path(client_id):
    return os.path.join(CLIENTS_DIR, f'{client_id}')


def get_handlers_path():
    return os.path.join('.', HANDLER_DIR)
