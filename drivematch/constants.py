from telethon.tl.types import BotCommand

ADMIN_COMMANDS = [
    BotCommand(command='admin', description='👑 Acessar Painel Administrativo'),
]

DEFAULT_COMMANDS = [
    BotCommand(command='start', description='👋 Iniciar ou reiniciar uma conversa.'),
    BotCommand(command='cancel', description='🧨 Cancelar viagem em andamento.'),
    BotCommand(command='unregister', description='❌ Removê-lo do sistema.'),
]

DRIVER_COMMANDS = [
    BotCommand(command='road', description='🛣️ Iniciar o trajeto da viagem.'),
    BotCommand(command='complete', description='✅ Finalizar a viagem e cobrar.'),
    BotCommand(command='wallet', description='💰 Ver saldo e histórico de viagens.'),
]
