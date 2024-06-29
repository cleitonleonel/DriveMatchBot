import asyncio
from decimal import Decimal
from telethon import (
    events,
    Button,
    TelegramClient
)
from telethon.tl.types import InputGeoPoint
from telethon.tl.functions.contacts import GetLocatedRequest
from drivematch.utils.location import (
    format_distance,
    reformat_distance,
    update_time
)
from drivematch.app import API_ID, API_HASH
from drivematch.paths import get_session_path
from drivematch.utils.decorators import handler
from drivematch.utils.authentication import request_contact
from drivematch.utils.rates import calculate_fare, calculate_percent


@handler
def register_callback_handlers(bot, instance):
    @bot.on(events.CallbackQuery)
    async def handle_callback(event):
        user = await event.get_sender()
        data = event.data.decode('utf-8')
        sender_id = event.sender_id
        message_id = event.query.msg_id

        if data == 'return':
            await event.respond('👌 Ok, até a próxima.')
            return await instance.remove_message(sender_id, message_id)

        elif data == 'drive':
            if not instance.users_dict[sender_id]["is_active"]:
                await instance.remove_message(sender_id, message_id)
                return await request_contact(instance, event, sender_id, is_new=False)
            await handle_drive(event, sender_id)

        elif data == 'travel':
            if not instance.users_dict[sender_id]["is_active"]:
                await instance.remove_message(sender_id, message_id)
                return await request_contact(instance, event, sender_id, is_new=False)
            await handle_travel(event, sender_id)

        instance.users_dict[sender_id] = await instance.check_user(sender_id)
        user_type = instance.users_dict[sender_id].get('type')

        if user_type == 'motorista':
            await instance.edit_message(sender_id, message_id, None, buttons=None)
            await handle_driver_callback(event, user, sender_id, data)

        elif user_type == 'passageiro':
            await instance.edit_message(sender_id, message_id, None, buttons=None)
            await handle_passenger_callback(event, sender_id, data)

        await event.answer(alert=True)

    async def handle_drive(event, sender_id):
        instance.controller.create_user('motorista', **instance.users_dict[sender_id])
        await event.respond(
            '✨ Bem vindo motorista!\n'
            'Vamos configurar agora \n'
            'alguns detalhes sobre \n'
            'sua conta e de seu veículo.'
        )
        instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_PIX_KEY
        await event.respond('💠 Insira uma chave pix: ')

    async def handle_travel(event, sender_id):
        instance.controller.create_user('passageiro', **instance.users_dict[sender_id])
        await event.respond(
            '🎉 Bem vindo passageiro!',
            buttons=[
                [
                    Button.request_location(
                        '🧭 Enviar Localização',
                        resize=True,
                        single_use=True
                    )
                ],
                [
                    Button.text(
                        '👋 Digitar Local',
                        resize=True
                    )
                ]
            ]
        )

    async def handle_driver_callback(event, user, sender_id, data):
        if data == 'enter_pix_key':
            instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_PIX_KEY
            await event.respond('💠 Insira uma chave pix:')

        elif data == 'enter_type_vehicle':
            instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_VEHICLE
            await event.respond('🚗 Insira o tipo de veículo:')

        elif data == 'enter_plate':
            instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_PLATE
            await event.respond('🚘 Insira a placa de seu veículo:')

        elif data.startswith('accept_'):
            await handle_accept_travel(event, user, sender_id, data)

    async def handle_accept_travel(event, user, sender_id, data):
        async with TelegramClient(get_session_path(sender_id), API_ID, API_HASH) as client:
            if not client.is_connected():
                await client.connect()
            if client and await client.is_user_authorized():
                passenger_id = int(data.split('_')[1])
                passenger = await instance.check_user(passenger_id)
                user_name = (
                    f'@{user.username}' if user.username
                    else f'{user.first_name} {user.last_name or ""}'
                )
                travel = instance.controller.get_travel(passenger['id'])
                driver = instance.users_dict[sender_id]

                if not travel or travel.get('status') in ['cancelled', 'complete']:
                    return await instance.send_message(sender_id, '🧨 Nenhuma viagem solicitada.\n')
                elif travel.get('status') in ['in_progress']:
                    return await instance.send_message(sender_id, '🔃 Viagem já está em andamento.\n')

                if passenger_id in instance.chats_ids:
                    instance.controller.accept_travel(travel['id'], driver['id'])
                    await instance.send_message(
                        passenger_id,
                        f'✅ Seu pedido de corrida foi aceito!\n'
                        f'🧑‍✈️ Motorista: {user_name}\n'
                        f'🚗 Carro: {driver["type_vehicle"]}\n'
                        f'🚘 Placa: {driver["plate"]}\n\n'
                        f'__**Para cancelar a viagem \n'
                        f'digite o comando**__ /cancel\n'
                    )
                    await event.reply(
                        '📲 Envie sua localização para o passageiro.',
                        buttons=[
                            Button.request_location(
                                '🧭 Enviar Localização',
                                resize=True,
                                single_use=True
                            )
                        ]
                    )
                    instance.conversation_state[sender_id] = instance.state.WAIT_DRIVER_LOCATION
                else:
                    await event.reply('🤦‍♂️ Passageiro não encontrado.')

    async def handle_passenger_callback(event, sender_id, data):
        if data == 'search_driver':
            await search_driver(event, sender_id)

    async def search_driver(event, sender_id):
        async with TelegramClient(get_session_path(sender_id), API_ID, API_HASH) as client:
            if not client.is_connected():
                await client.connect()

            if client and await client.is_user_authorized():
                proximity_drivers = asyncio.create_task(
                    get_proximity_drivers(
                        event,
                        sender_id,
                        client
                    )
                )

            if len(await proximity_drivers) < 1:
                return await event.answer(alert=True)

        passenger = instance.users_dict[sender_id]
        instance.controller.create_travel(passenger["id"])

    async def get_proximity_drivers(event, sender_id, client):
        drivers = []
        await event.reply('🕵️‍♂️ Vou buscar motoristas mais próximos...')
        full_address = instance.runtime_settings[sender_id]["address"]["origin"]
        latitude = instance.runtime_settings[sender_id]["address"]["latitude"]
        longitude = instance.runtime_settings[sender_id]["address"]["longitude"]
        if not latitude or not longitude:
            await asyncio.sleep(2)
            return await event.reply(
                '🤦‍♂️ Nenhum motorista disponível no momento.\n'
                '🎭 Tente novamente em alguns minutos.'
            )
        destination = instance.runtime_settings[sender_id]["address"]["destination"]
        location_url = instance.runtime_settings[sender_id]["address"]["url"]
        _distance = instance.runtime_settings[sender_id]["address"]["distance"]
        travel_time = instance.runtime_settings[sender_id]["address"]["time"]
        distance_km = float(_distance.split()[0].replace(',', '.'))
        time_min = float(travel_time.split()[0].replace(',', '.'))
        geo_point = InputGeoPoint(float(latitude), float(longitude), 10)
        result = await client(GetLocatedRequest(geo_point))
        response = 'Chats e pessoas próximas:\n'
        peers = result.updates[0].peers
        for location in peers:
            if hasattr(location, 'peer'):
                if hasattr(location.peer, 'chat_id'):
                    chat = await client.get_entity(int(location.peer.chat_id))
                    formatted_distance = format_distance(location.distance)
                    response += f'Chat: {chat.title} {formatted_distance} (ID: {chat.id})\n'
                elif hasattr(location.peer, 'user_id'):
                    user = await client.get_entity(int(location.peer.user_id))
                    formatted_distance = format_distance(location.distance)
                    response += (f'Usuário: {user.username or user.first_name} '
                                 f'Distância:{formatted_distance} (ID: {user.id})\n')
                    driver = await instance.check_user(user.id)
                    if driver:
                        drivers.append(driver)
                    # print(user.username)
            await asyncio.sleep(1)
        # print(drivers)

        tax_amount = calculate_fare(
            base_fare=2.00,
            cost_per_km=0.71,
            cost_per_minute=0.42,
            service_fee=0.75,
            distance_km=distance_km,
            time_min=time_min,
            surge_multiplier=1.0
        )
        percent_amount = calculate_percent(tax_amount)
        receive_amount = Decimal(tax_amount - percent_amount)

        user = await client.get_me()
        if len(drivers) > 0:
            for driver in drivers:
                driver_id = driver['user_id']
                await instance.send_message(
                    driver_id,
                    f'__**Nova Solicitação de Viagem**__\n'
                    f'🧔‍♂️ Passageiro: {user.username or user.first_name}\n'
                    f'▶️ Origem: {full_address}\n'
                    f'⏹️ Destino: {destination}\n'
                    f'📏 Distância: {reformat_distance(_distance, 500)}\n'
                    f'🧭 Tempo: {update_time(travel_time, 500)}\n'
                    f'💰 Você recebe R$ {receive_amount:.2f}\n'
                    f'🛣️ Trajeto: [Confira aqui o trajeto]({location_url})\n',
                    custom_buttons=[
                        [
                            Button.inline(
                                '✅ Aceitar corrida',
                                data=f'accept_{sender_id}'
                            ),
                            Button.inline(
                                '❎ Cancelar',
                                data='return'
                            )
                        ]
                    ]
                )
                await asyncio.sleep(5)
        else:
            await event.reply(
                '🤦‍♂️ Nenhum motorista disponível no momento.'
            )

        await instance.delete_conversation(sender_id)
        await client.disconnect()
        return drivers
