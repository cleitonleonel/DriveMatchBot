import pyfiglet
from drivematch import config
from drivematch.app import Client

__app_name__ = config.APP_NAME
__author__ = config.APP_AUTHOR
__version__ = config.APP_VERSION

__message__ = f"""
Suporte: cleiton.leonel@gmail.com ou +55 (27) 9 9577-2291
"""

custom_font = pyfiglet.Figlet(
    font="src/fonts/ANSI_Shadow",
    justify="justify",
    width=100
)
ascii_art = custom_font.renderText(__app_name__)
art_effect = f"""{ascii_art}
Autor: {__author__} 
Versão: {__version__}
{__message__}
"""

print(art_effect)
print('🚗✨')

if __name__ == "__main__":
    client = Client()
    start_service = client.start_service()
