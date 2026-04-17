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

    async def run(self):
        """Sobrescreve o método run para incluir inicialização do Redis antes de rodar o bot."""
        await self.storage.connect()
        logging.info('Base de dados via Storage conectada com sucesso.')
        
        # Chama a implementação "inteligente" do SmartBot que:
        # - Inicia a sessão no Telegram
        # - Carrega os PLUGINS (extremamente importante)
        # - Registra os comandos do BotFather
        # - Gerencia o keep_alive e cleanup
        # Importante: A implementação do SmartBot NÃO empilha handlers (evita respostas duplicadas)
        await super().run()

    async def start_service(self):
        await self.run()
