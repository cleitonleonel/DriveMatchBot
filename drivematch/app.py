import sys
import logging
from smartbot.bot import Client as SmartBotClient
from telethon.network import ConnectionTcpFull

from smartbot.config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_IDS,
    config as bot_config
)
from drivematch.controllers.user import UserController
from drivematch.utils.state import State
from drivematch.utils.storage import RedisStorage
from drivematch.utils.session import RedisUserSession

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drivematch.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Client(SmartBotClient):
    """Classe de cliente personalizada para DriveMatch."""
    def __init__(self, **kwargs):
        # Redis URL centrallized in config.toml
        redis_url = bot_config.get('DATABASE', {}).get('REDIS_URL', "redis://localhost:6379/0")
        
        # O SmartBot espera configurações
        kwargs.setdefault('session', 'DriveMatch')
        kwargs.setdefault('api_id', API_ID)
        kwargs.setdefault('api_hash', API_HASH)
        kwargs.setdefault('bot_token', BOT_TOKEN)
        kwargs.setdefault('admin_ids', ADMIN_IDS)
        kwargs.setdefault('connection', ConnectionTcpFull)
        kwargs.setdefault('conversation_state', State)
        
        super().__init__(**kwargs)
        
        # Componentes específicos do DriveMatch
        self.controller = UserController()
        self.state = State
        self.storage = RedisStorage(url=redis_url)
        
        # Sobrescrever a sessão do usuário com a implementação em Redis (Passa a CLASSE, não a instância)
        self.user_session = RedisUserSession
        self._plugins_loaded = False

    def add_event_handler(self, callback, *args, **kwargs):
        """Previne o registro duplicado de handlers no Telethon."""
        try:
            existing = [cb for cb, _ in self.list_event_handlers()]
            if callback in existing:
                logger.info(f"Handler '{getattr(callback, '__name__', str(callback))}' já registrado. Ignorando duplicata.")
                return
        except Exception as e:
            logger.warning(f"Erro ao verificar handlers existentes: {e}")
        
        super().add_event_handler(callback, *args, **kwargs)

    async def run(self):
        """Sobrescreve o método run para incluir inicialização do Redis e evitar acúmulo de handlers."""
        await self.storage.connect()
        logging.info('Base de dados via Storage conectada com sucesso.')
        
        # Chama a implementação base
        await super().run()

    async def start_service(self):
        await self.run()
