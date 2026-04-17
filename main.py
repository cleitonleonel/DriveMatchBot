import os
import asyncio
import logging
import pyfiglet
from smartbot.paths import SESSIONS_DIR
from smartbot.config import APP_NAME, APP_AUTHOR, APP_VERSION
from drivematch.app import Client
from drivematch.constants import ADMIN_COMMANDS, DEFAULT_COMMANDS

# Metadados e Estética
__app_name__ = APP_NAME
__author__ = APP_AUTHOR
__version__ = APP_VERSION

logger = logging.getLogger(__name__)

custom_font = pyfiglet.Figlet(font="src/fonts/ANSI_Shadow", justify="justify", width=100)
ascii_art = custom_font.renderText(__app_name__)
art_effect = f"{ascii_art}\nAutor: {__author__} \nVersão: {__version__}\nSuporte: cleiton.leonel@gmail.com\n"
print(art_effect)
print('🚗✨')

SESSION_PATH: str = os.path.join(
    SESSIONS_DIR,
    APP_NAME
)

# Configuração de Plugins (SmartBot Pattern)
plugins: dict = {
    "root": "plugins",
    "include": ["commands", "callback", "location", "conversation", "admin"]
}

# Configuração de Comandos
commands: dict = {
    "admin_commands": ADMIN_COMMANDS,
    "default_commands": DEFAULT_COMMANDS
}

# Perfil do Bot
profile: dict = {
    "name": __app_name__,
    "logo": "src/media/logo.png",
    "lang": "pt",
    "description": "🚗 Plataforma de corridas e transportes via Telegram.",
    "about": "🚗 Bot oficial DriveMatch para motoristas e passageiros."
}

# Instanciação do Cliente
client = Client(
    plugins=plugins,
    commands=commands,
    config=profile,
    session=SESSION_PATH,
)


async def main():
    await client.start_service()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Bot interrompido pelo usuário.')
