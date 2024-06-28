from telethon import (
    events,
    Button
)
from pathlib import Path
from drivematch.app import BOT_TOKEN
from drivematch.paths import get_session_path
from drivematch.utils.decorators import handler
from drivematch.utils.authentication import create_session_client


@handler
def register_commands_handlers(bot, instance):
    @bot.on(events.NewMessage(pattern='/start'))
    async def handle_start_command(event):
        sender = await event.get_sender()
        sender_id = sender.id
        if sender_id != int(BOT_TOKEN.split(":")[0]):
            await process_new_user(event, instance, sender_id)

    @bot.on(events.NewMessage(pattern='/road'))
    async def handle_start_travel(event):
        sender_id = event.sender_id
        if not instance.users_dict.get(sender_id):
            return
        user_type = instance.users_dict[sender_id].get('type')
        if user_type == 'motorista':
            await start_travel(event, instance, sender_id)

    @bot.on(events.NewMessage(pattern='/complete'))
    async def handle_complete_travel(event):
        sender_id = event.sender_id
        if not instance.users_dict.get(sender_id):
            return
        user_type = instance.users_dict[sender_id].get('type')
        if user_type == 'motorista':
            await complete_travel(event, instance, sender_id)

    @bot.on(events.NewMessage(pattern='/cancel'))
    async def handle_cancel_travel(event):
        sender_id = event.sender_id
        if not instance.users_dict.get(sender_id):
            return
        user_type = instance.users_dict[sender_id].get('type')
        await cancel_travel(event, instance, sender_id, user_type)

    @bot.on(events.NewMessage(pattern='/unregister'))
    async def handle_cancel_travel(event):
        sender_id = event.sender_id
        if not instance.users_dict.get(sender_id):
            return
        user_type = instance.users_dict[sender_id].get('type')
        await unregister_account(event, instance, sender_id, user_type)


async def process_new_user(event, instance, sender_id):
    sender = await event.get_sender()
    manager = None

    if sender_id in instance.chats_ids:
        manager = instance.manager.pop(instance.chats_ids.index(sender_id))
        instance.chats_ids.remove(sender_id)
    else:
        instance.users_dict[sender_id] = {}
        instance.runtime_settings[sender_id] = {"address": {}, "phone": None, "phone_code_hash": None}

    if not await instance.check_user(sender_id):
        instance.users_dict[sender_id] = {
            "user_id": sender.id,
            "username": sender.username or "",
            "first_name": sender.first_name or "",
            "last_name": sender.last_name or "",
            # "email": f"teste{sender.id}@gmail.com"
        }

        session_path = Path(f"{get_session_path(sender_id)}.session")
        if not session_path.exists():
            return await create_session_client(instance, event, sender_id)
        buttons = [
            [
                Button.inline('🚗 Dirigir', 'drive'),
                Button.inline('👋 Viajar', 'travel')
            ]
        ]
        return await event.respond(
            f'Olá {sender.username or sender_id}\n'
            '💬 Que bom te ver por aqui!\n'
            '👇 Selecione uma das opções abaixo:',
            buttons=buttons
        )

    instance.users_dict[sender_id] = await instance.check_user(sender_id)
    instance.chats_ids.append(sender_id)
    instance.manager.append(manager)
    user_type = instance.users_dict[sender_id].get('type')

    if user_type == 'passageiro':
        await event.reply(
            "✨ Bem-vindo!",
            buttons=[
                [
                    Button.request_location("🧭 Localização", resize=True, single_use=True)
                ],
                [
                    Button.text("👋 Inserir Local", resize=True)
                ]
            ]
        )
        instance.conversation_state[sender_id] = instance.state.WAIT_PASSENGER_LOCATION

    elif user_type == 'motorista':
        await event.respond(
            "✨ Bem-vindo!\n"
            "📳 Você será notificado quando novas viagens surgirem.\n"
            "💆‍♂️ Fique a vontade."
        )
    instance.conversation_state[sender_id] = instance.state.START


async def start_travel(event, instance, sender_id):
    driver = instance.users_dict[sender_id]
    travel = instance.controller.get_travel(driver['id'])

    if not travel or travel.get('status') in ['cancelled', 'complete']:
        return await instance.send_message(sender_id, "🧨 Nenhuma viagem solicitada.\n")
    elif travel.get('status') in ['in_progress']:
        return await instance.send_message(sender_id, "🔃 Viagem já está em andamento.\n")

    instance.controller.start_travel(travel['id'], driver['id'])
    instance.controller.edit_user(**instance.users_dict[sender_id])
    passenger_id = travel['passenger']["user_id"]
    await event.respond(
        "✅ Viagem iniciada com sucesso!\n"
        "👉 Clique em /complete quando terminar a corrida.\n"
    )
    await instance.send_message(
        passenger_id,
        "✅ Trajeto iniciado.\n"
        "💆‍♂️ Fique a vontade e aproveite a viagem!"
    )


async def complete_travel(event, instance, sender_id):
    driver = instance.users_dict[sender_id]
    travel = instance.controller.get_travel(driver['id'])

    if not travel or travel.get('status') in ['cancelled', 'complete']:
        return await instance.send_message(sender_id, "🧨 Nenhuma viagem solicitada.\n")
    elif travel.get('status') in ['accepted', 'requesting']:
        return await instance.send_message(sender_id, "🧨 Não é possível concluir uma viagem não iniciada.\n")

    instance.controller.complete_travel(travel['id'], driver['id'])
    instance.users_dict[sender_id]["qtd_travels"] += 1
    instance.controller.edit_user(**instance.users_dict[sender_id])
    passenger_id = travel['passenger']["user_id"]
    await event.respond("✅ Viagem concluída com sucesso!")
    await instance.send_message(
        passenger_id,
        "🏁 Chegamos ao nosso destino.\n"
        "🫶 Obrigado por viajar conosco!"
    )


async def cancel_travel(event, instance, sender_id, user_type):
    user = instance.users_dict[sender_id]
    travel = instance.controller.get_travel(user['id'])

    if not travel or travel.get('status') in ['cancelled', 'complete']:
        return await instance.send_message(sender_id, "🧨 Nenhuma viagem em andamento.\n")
    elif travel.get('status') in ['in_progress']:
        return await instance.send_message(sender_id, "🧨 Não é possível cancelar uma viagem já iniciada.\n")

    if user_type == 'motorista':
        instance.users_dict[sender_id]["num_ratings"] -= 1
        passenger_id = travel['passenger']["user_id"]
        instance.controller.cancel_travel(travel['id'], user['id'])
        await instance.send_message(passenger_id, "🧨 Viagem cancelada pelo motorista.\n")

    elif user_type == 'passageiro':
        instance.users_dict[sender_id]["num_ratings"] -= 1
        driver_id = travel['driver']["user_id"]
        instance.controller.cancel_travel(travel['id'], user['id'])
        await instance.send_message(driver_id, "🧨 Viagem cancelada pelo passageiro.\n")

    instance.controller.edit_user(**instance.users_dict[sender_id])
    await event.respond("❎ Viagem cancelada com sucesso!\n")


async def unregister_account(event, instance, sender_id, user_type):
    user = instance.users_dict[sender_id]
    result_dict = instance.controller.delete_user(user['user_id'])
    if result_dict:
        session_path = Path(f"{get_session_path(sender_id)}.session")
        if session_path.exists():
            pass
            # session_path.unlink()
        return await event.respond(
            f"🫶 Seu registro como {user_type} foi removido\n"
            f"Quando decidir {'viajar' if user_type == 'passageiro' else 'dirigir'} "
            f"conosco novamente,\nbasta digitar /start ."
        )
    return await event.respond(
        "Não foi possível localizar seu registro no momento."
    )
