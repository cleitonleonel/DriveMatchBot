import sys
import asyncio
import logging
from pathlib import Path
from importlib import import_module
from telethon import TelegramClient
from telethon.network import ConnectionTcpFull
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.tl.types import (
    BotCommand,
    BotCommandScopePeer,
    BotCommandScopeDefault,
    InputMediaGeoLive,
    InputGeoPoint,
)
from telethon.tl.functions.bots import (
    SetBotCommandsRequest
)

from .config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_IDS,
    APP_VERSION,
    DEVICE_MODEL,
    SYSTEM_VERSION
)
from .controllers.user import UserController
from .utils.state import State
from .paths import get_handlers_path, get_session_path

logging.basicConfig(level=logging.INFO)


class Client:
    bot = TelegramClient(
        'drivematch/sessions/drive_match',
        API_ID, API_HASH,
        connection=ConnectionTcpFull,
        device_model=DEVICE_MODEL,
        system_version=SYSTEM_VERSION,
        app_version=APP_VERSION

    )
    controller = UserController()
    state = State

    def __init__(self):
        self.conversation_state = {}
        self.runtime_settings = {}
        self.tasks_schedule = {}
        self.messages_ids = {}
        self.users_dict = {}
        self.chats_ids = []
        self.manager = []

    async def send_message(self, chat_id, message='', custom_buttons=None, **kwargs):
        return await self.bot.send_message(chat_id, message, buttons=custom_buttons, **kwargs)

    async def remove_message(self, chat_id, message_id):
        try:
            await self.bot.delete_messages(chat_id, [message_id])
        except MessageDeleteForbiddenError as e:
            logging.error(f'Erro ao excluir mensagem: {e}')

    async def edit_message(self, chat_id, message_id, message, **kwargs):
        try:
            return await self.bot.edit_message(chat_id, message_id, message, **kwargs)
        except Exception as e:
            logging.error(f'Erro ao editar mensagem: {e}')

    async def delete_conversation(self, chat_id):
        if self.conversation_state.get(chat_id):
            del self.conversation_state[chat_id]

    async def check_user(self, param):
        result_user = self.controller.check_user_exists(param)
        return result_user

    async def get_admin_entity(self):
        peer = None
        for entity in ADMIN_IDS:
            try:
                peer = await self.bot.get_input_entity(entity)
            finally:
                if peer:
                    return peer

    async def register_commands(self):
        admin_input_peer = await self.get_admin_entity()
        if not admin_input_peer:
            logging.warning(
                'Nenhum ID de administrador válido ou você não conversou com '
                'o bot ainda. Por favor, envie um /start para o bot e tente novamente. Saindo...'
            )
            return
        admin_commands = []
        commands = [
            BotCommand(
                command='start',
                description='Iniciar ou reiniciar uma conversa.'
            ),
            BotCommand(
                command='unregister',
                description='Remover conta do sistema.'
            ),
        ]
        await self.bot(
            SetBotCommandsRequest(
                scope=BotCommandScopePeer(admin_input_peer),
                lang_code='',
                commands=admin_commands + commands
            )
        )
        await self.bot(
            SetBotCommandsRequest(
                scope=BotCommandScopeDefault(),
                lang_code='',
                commands=commands
            )
        )

    async def send_live_location(self, sender_id, chat_id, proximity_notification_radius=None):
        latitude = self.runtime_settings[sender_id]["address"]["latitude"]
        longitude = self.runtime_settings[sender_id]["address"]["longitude"]
        async with TelegramClient(get_session_path(sender_id), API_ID, API_HASH) as client:
            geo_live = InputMediaGeoLive(
                geo_point=InputGeoPoint(
                    lat=latitude,
                    long=longitude
                ),
                period=60 * 30,  # Período de atualização em segundos
                proximity_notification_radius=proximity_notification_radius
            )

            if not client.is_connected():
                await client.connect()

            await client.send_file(
                chat_id,
                file=geo_live,
                force_document=True
            )

    async def load_handlers(self):
        handlers_path = get_handlers_path()
        for path in sorted(Path(handlers_path).rglob("*.py")):
            module_path = '.'.join(path.parent.parts + (path.stem,))
            if module_path not in sys.modules:
                module = import_module(module_path)
                for name in vars(module).keys():
                    register_function = getattr(module, name)
                    if callable(register_function) and getattr(register_function, 'is_handler', False):
                        logging.info(f'Chamando {name} no módulo: {module_path}')
                        register_function(self.bot, self)
                    await asyncio.sleep(0.1)
                await asyncio.sleep(0.1)

    async def keep_alive(self):
        while True:
            try:
                if not self.bot.is_connected():
                    logging.warning('Bot is not connected. Reconnecting...')
                    await self.bot.connect()
                await asyncio.sleep(60)
            except Exception as e:
                logging.error(f'Error in keep_alive: {e}', exc_info=True)
                await asyncio.sleep(60)

    async def run(self):
        try:
            await self.bot.start(bot_token=BOT_TOKEN)
            await self.register_commands()
            await self.load_handlers()
            logging.info('Iniciando telegram bot!!!')
            await asyncio.gather(
                self.bot.run_until_disconnected(),
                self.keep_alive()
            )
        except ConnectionError:
            logging.error('Falha ao se conectar com Telegram.')
            await asyncio.sleep(5)
            await self.run()

    async def shutdown(self):
        await self.bot.disconnect()
        logging.info('Bot desconectado com sucesso.')

    def start_service(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.run())
        except KeyboardInterrupt:
            logging.info('Bot interrompido pelo usuário.\n'
                         'Desconectando...')
            loop.run_until_complete(self.shutdown())
