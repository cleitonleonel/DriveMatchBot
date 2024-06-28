import pyfiglet
from drivematch.app import Client

__author__ = "Cleiton Leonel Creton"
__version__ = "1.0.0"

__message__ = f"""
Suporte: cleiton.leonel@gmail.com ou +55 (27) 9 9577-2291
"""

custom_font = pyfiglet.Figlet(
    font="src/fonts/ANSI_Shadow",
    justify="justify",
    width=100
)
ascii_art = custom_font.renderText("Drive-Match")
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
