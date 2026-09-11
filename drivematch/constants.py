from telethon.tl.types import BotCommand

ADMIN_COMMANDS = [
    BotCommand(command='admin', description='👑 Acessar Painel Administrativo'),
]

DEFAULT_COMMANDS = [
    BotCommand(command='start', description='👋 Iniciar / Solicitar Viagem'),
    BotCommand(command='profile', description='👤 Ver meu perfil'),
    BotCommand(command='cancel', description='🧨 Cancelar viagem em andamento'),
    BotCommand(command='unregister', description='❌ Excluir minha conta'),
]

DRIVER_COMMANDS = [
    BotCommand(command='start', description='👋 Iniciar / Painel do Motorista'),
    BotCommand(command='road', description='🛣️ Iniciar trajeto da viagem'),
    BotCommand(command='complete', description='✅ Finalizar viagem e cobrar'),
    BotCommand(command='wallet', description='💰 Ver saldo e saques'),
    BotCommand(command='profile', description='👤 Meu perfil e veículo'),
    BotCommand(command='cancel', description='🧨 Cancelar viagem em andamento'),
    BotCommand(command='unregister', description='❌ Excluir minha conta'),
]
