import re
from telethon import (
    Button,
    TelegramClient
)
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    AuthRestartError
)
from drivematch.app import API_ID, API_HASH
from drivematch.paths import get_session_path


async def create_session_client(instance, event, sender_id):
    client = TelegramClient(get_session_path(sender_id), API_ID, API_HASH)
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        await event.respond(
            '💬 Novo por aqui?\n'
            '📞 Clique no botão abaixo para nos \n'
            'enviar seu número de telefone',
            buttons=[
                Button.request_phone(
                    text=' 📞 Enviar Contato 📞 ',
                    resize=True
                )
            ]
        )
        instance.conversation_state[sender_id] = instance.state.WAIT_GET_CONTACT
    await client.disconnect()


async def process_code_activation(instance, event, sender_id, code):
    code = re.sub(r'[^0-9]', '', code.strip())
    phone_number = instance.runtime_settings[sender_id]["phone"]
    phone_code_hash = instance.runtime_settings[sender_id]["phone_code_hash"]
    if not code.isdigit():
        return
    client = TelegramClient(get_session_path(sender_id), API_ID, API_HASH)
    if not client.is_connected():
        await client.connect()
    try:
        await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
        if await client.is_user_authorized():
            await event.respond('✅ Login realizado com sucesso!')
            buttons = [
                [
                    Button.inline('🚗 Dirigir', 'drive'),
                    Button.inline('👋 Viajar', 'travel')
                ]
            ]
            await event.respond(
                '👇 Selecione uma das opções abaixo:',
                buttons=buttons
            )
            await instance.delete_conversation(sender_id)
        else:
            await event.respond('⚠️ Código de verificação incorreto. Tente novamente.')
    except SessionPasswordNeededError:
        await event.respond('🔐 Sua conta está protegida com senha. Por favor, insira sua senha:')
        instance.conversation_state[sender_id] = instance.state.WAIT_TWO_STEPS_VERIFICATION
    except PhoneCodeInvalidError:
        await event.respond('⚠️ Código de verificação incorreto. Tente novamente.')
    except AuthRestartError:
        await event.respond('🚨 Erro de autenticação. Por favor, tente novamente.')
    await client.disconnect()


async def process_two_steps_verification(instance, event, sender_id, password):
    client = TelegramClient(get_session_path(sender_id), API_ID, API_HASH)
    if not client.is_connected():
        await client.connect()
    try:
        await client.sign_in(password=password)
        if client.is_user_authorized():
            await event.respond('✅ Login realizado com sucesso!')
            buttons = [
                [
                    Button.inline('🚗 Dirigir', 'drive'),
                    Button.inline('👋 Viajar', 'travel')
                ]
            ]
            await event.respond(
                '👇 Selecione uma das opções abaixo:',
                buttons=buttons
            )
            await instance.delete_conversation(sender_id)
        else:
            await event.respond('⚠️ Senha incorreta. Tente novamente.')
    except Exception as e:
        await event.respond(f'🚫 Erro ao tentar fazer login: {str(e)}')
    await client.disconnect()


async def process_get_contact(instance, event, sender_id):
    phone_number = event.contact.phone_number
    instance.runtime_settings[sender_id]["phone"] = phone_number
    await event.respond(
        f'📲 Obrigado por compartilhar seu número: {phone_number}\n'
        f'🔝 Iniciando o processo de login...',
        buttons=Button.clear()
    )
    client = TelegramClient(get_session_path(sender_id), API_ID, API_HASH)
    if not client.is_connected():
        await client.connect()
    try:
        phone_code = await client.send_code_request(phone_number)
        instance.runtime_settings[sender_id]["phone_code_hash"] = phone_code.phone_code_hash
        await event.respond(
            f'⚠️ Enviamos um código de ativação a você.\n'
            f'Confirme o recebimento desse código\n'
            f'e o insira como no exemplo abaixo:\n'
            f'Ex: 1#2#3#4#5\n'
            f'[Visualizar Código](https://t.me/+42777)'
        )
    except AuthRestartError:
        await event.respond('🚫 Erro de autenticação. Por favor, tente novamente.')
    instance.conversation_state[sender_id] = instance.state.WAIT_CODE_ACTIVATION
    instance.controller.edit_user(**instance.users_dict[sender_id])
    await client.disconnect()
