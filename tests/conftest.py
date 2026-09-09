import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock mercadopago ANTES de importar qualquer coisa que possa usá-lo
sys.modules["mercadopago"] = MagicMock()

import pytest

# Mock da database e do SmartBot ANTES de importar qualquer coisa do drivematch
mock_engine = MagicMock()
mock_session = MagicMock()

# Mock do SmartBotClient para evitar que o construtor tente conectar ao Telegram
class MockSmartBotClient:
    def __init__(self, **kwargs):
        self.bot = AsyncMock()
        self.plugins = kwargs.get('plugins', {})
        self.config = kwargs.get('config', {})
        self.commands = kwargs.get('commands', {})
        
        # Armazenamento interno para o mock de sessão
        self._states = {}
        self._data = {}
        
        self.user_session = MagicMock()
        
        # Métodos mockados que refletem o estado interno do mock
        self.get_user_session = MagicMock(return_value=self.user_session)
        self.get_user_state = MagicMock(side_effect=lambda uid: self._states.get(uid))
        self.set_user_state = MagicMock(side_effect=lambda uid, s, ctx=None: self._states.update({uid: s}))
        self.get_user_data = MagicMock(side_effect=lambda uid, k, d=None: self._data.get(uid, {}).get(k, d))
        self.set_user_data = MagicMock(side_effect=lambda uid, k, v: self._data.setdefault(uid, {}).update({k: v}))
        
        # Métodos de compatibilidade
        self.start = AsyncMock()
        self.disconnect = AsyncMock()
        self.send_message = AsyncMock()
        self._event_handlers = []

    def add_event_handler(self, callback, *args, **kwargs):
        self._event_handlers.append((callback, args))

    def list_event_handlers(self):
        return self._event_handlers

with patch("sqlalchemy.create_engine", return_value=mock_engine), \
     patch("sqlalchemy.orm.sessionmaker", return_value=mock_session), \
     patch("sqlalchemy.orm.declarative_base", return_value=MagicMock()), \
     patch("smartbot.bot.Client", MockSmartBotClient):
    from drivematch.app import Client

@pytest.fixture
def mock_bot():
    """Mock do TelegramClient do Telethon com registro de handlers."""
    bot = AsyncMock()
    bot.handlers = []
    
    def on_decorator(event_filter):
        def decorator(func):
            bot.handlers.append((event_filter, func))
            return func
        return decorator
    
    bot.on = MagicMock(side_effect=on_decorator)
    return bot

@pytest.fixture
def app_client(mock_bot, monkeypatch):
    """Instância do Client da aplicação configurada para testes com isolamento total."""
    # Armazenamento compartilhado para o mock de sessão neste teste
    test_session_states = {}
    test_session_data = {}

    # 1. Mock do UserController
    mock_controller = MagicMock()
    methods = [
        'check_user_exists', 'get_travel', 'create_user', 'edit_user', 
        'update_user_location', 'request_payout', 'get_admin_stats', 
        'get_system_settings', 'update_system_settings', 'get_all_users',
        'list_pending_payouts', 'confirm_payout', 'get_travel_by_id', 'add_review',
        'accept_travel', 'find_nearby_drivers', 'create_travel', 'get_user_travels',
        'count_active_drivers', 'cancel_travel'
    ]
    for method in methods:
        setattr(mock_controller, method, AsyncMock(return_value=None))
    
    mock_controller.count_active_drivers.return_value = {"total_active_system": 1, "in_radius": 1}
    
    # 2. Injetando mock do controller na CLASSE para que o Client() ao ser chamado o use
    monkeypatch.setattr("drivematch.app.UserController", lambda: mock_controller)
    
    # 3. Mock do RedisStorage
    mock_storage = AsyncMock()
    mock_storage_vals = {}
    mock_storage.get = AsyncMock(side_effect=lambda k, d=None: mock_storage_vals.get(k, d))
    mock_storage.set = AsyncMock(side_effect=lambda k, v: mock_storage_vals.update({k: v}))
    mock_storage.connect = AsyncMock()
    
    # 4. Mock do RedisUserSession
    mock_user_session = MagicMock()
    mock_user_session.get_user_state = MagicMock(side_effect=lambda uid: test_session_states.get(uid))
    mock_user_session.set_user_state = MagicMock(side_effect=lambda uid, s, ctx=None: test_session_states.update({uid: s}))
    mock_user_session.get_user_data = MagicMock(side_effect=lambda uid, k, d=None: test_session_data.get(uid, {}).get(k, d))
    mock_user_session.set_user_data = MagicMock(side_effect=lambda uid, k, v: test_session_data.setdefault(uid, {}).update({k: v}))
    mock_user_session.reset_to_idle = MagicMock(side_effect=lambda uid: test_session_states.update({uid: None}))
    
    monkeypatch.setattr("drivematch.app.RedisUserSession", lambda url: mock_user_session)
    
    # 5. Instanciando o Client
    client = Client(
        plugins={"root": "plugins", "include": ["commands"]},
        config={"name": "DriveMatch"}
    )
    
    # 6. Forçando os mocks na instância (garantia dupla)
    client.bot = mock_bot 
    client.controller = mock_controller
    client.storage = mock_storage
    client.user_session = mock_user_session
    
    # 7. Mockar métodos da classe base do SmartBot para usar o mock_user_session
    client.get_user_state = MagicMock(side_effect=lambda uid: mock_user_session.get_user_state(uid))
    client.set_user_state = MagicMock(side_effect=lambda uid, s, ctx=None: mock_user_session.set_user_state(uid, s, ctx))
    client.get_user_data = MagicMock(side_effect=lambda uid, k, d=None: mock_user_session.get_user_data(uid, k, d))
    client.set_user_data = MagicMock(side_effect=lambda uid, k, v: mock_user_session.set_user_data(uid, k, v))
    client.reset_user_session = MagicMock(side_effect=lambda uid: mock_user_session.reset_to_idle(uid))
    
    # 8. Outros métodos de conveniência
    client.send_message = AsyncMock()
    client.get_admin_entity = AsyncMock()
    client.register_commands = AsyncMock()
    
    return client

class MockEvent:
    def __init__(self, sender_id, data=None, text=None, geo=None, client=None):
        self.sender_id = sender_id
        if data:
            self.data = data.encode() if isinstance(data, str) else data
        else:
            self.data = b""
        self.text = text
        self.raw_text = text
        self.message = MagicMock()
        self.message.geo = geo
        self.geo = geo
        self.message.media = geo
        self.query = MagicMock(msg_id=123)
        self.answer = AsyncMock()
        self.respond = AsyncMock()
        self.reply = AsyncMock()
        self.edit = AsyncMock()
        self.delete = AsyncMock()
        self.client = client
        
    async def get_sender(self):
        return MagicMock(id=self.sender_id, username=f"user_{self.sender_id}", first_name="Test")

@pytest.fixture
def location_event_factory(app_client):
    def _create(sender_id, lat, long):
        geo = MagicMock(lat=lat, long=long)
        return MockEvent(sender_id, geo=geo, client=app_client)
    return _create

@pytest.fixture
def callback_event_factory(app_client):
    def _create(sender_id, data):
        return MockEvent(sender_id, data=data, client=app_client)
    return _create

@pytest.fixture
def message_event_factory(app_client):
    def _create(sender_id, text):
        return MockEvent(sender_id, text=text, client=app_client)
    return _create
