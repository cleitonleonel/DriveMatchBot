import logging
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommandScopePeer
from smartbot.config import ADMIN_IDS
from drivematch.constants import DEFAULT_COMMANDS, DRIVER_COMMANDS, ADMIN_COMMANDS

logger = logging.getLogger(__name__)


async def setup_user_commands(client, sender_id: int, user_type: str = None):
    """
    Configura o menu de comandos (botão /) no Telegram de forma personalizada por usuário.
    - Motoristas veem comandos de motorista (/road, /complete, /wallet, /profile, etc.)
    - Passageiros veem comandos de passageiro (/start, /profile, /cancel, etc.)
    - Admins recebem adicionalmente o comando /admin
    """
    try:
        if user_type == 'motorista':
            commands = list(DRIVER_COMMANDS)
        else:
            commands = list(DEFAULT_COMMANDS)

        if sender_id in ADMIN_IDS:
            cmd_names = {c.command for c in commands}
            for ac in ADMIN_COMMANDS:
                if ac.command not in cmd_names:
                    commands.append(ac)

        try:
            peer = await client.get_input_entity(sender_id)
        except Exception:
            peer = sender_id

        await client(SetBotCommandsRequest(
            scope=BotCommandScopePeer(peer=peer),
            lang_code='',
            commands=commands
        ))
    except Exception as e:
        logger.warning(f"Não foi possível atualizar comandos para o usuário {sender_id}: {e}")
