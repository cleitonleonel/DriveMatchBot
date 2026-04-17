import logging
import asyncio
from decimal import Decimal
from telethon import events, Button
from smartbot.utils.handler import ClientHandler
from drivematch.utils.payment import verify_payment_status
from drivematch.utils.state import State
from drivematch.utils.location import (
    update_time,
    reformat_distance,
    get_address_info,
    add_minutes_to_current_time
)
from drivematch.utils.rates import calculate_fare, calculate_percent

client = ClientHandler()


@client.on(events.CallbackQuery)
async def handle_callback(event):
    data = event.data.decode()
    sender_id = event.sender_id

    user = await event.client.controller.check_user_exists(sender_id)
    if user and user.get('is_active'):
        event.client.set_user_data(sender_id, "user", user)

    if data == 'travel' or data == 'drive':
        return await handle_start(event, sender_id, data)

    if data == 'return':
        await event.respond('👌 Ok, até a próxima.')
        return await event.delete()

    # Cadastro e Roles
    if data == 'drive':
        await handle_drive(event, sender_id)
    elif data == 'travel':
        await handle_travel(event, sender_id)

    # Pagamentos
    elif data.startswith('confirm_pay_'):
        await handle_confirm_payment(event, sender_id, data)
    elif data.startswith('driver_ack_'):
        await handle_driver_acknowledgment(event, sender_id, data)

    # Avaliações
    elif data.startswith('rate_ask_'):
        await handle_rate_ask(event, sender_id, data)
    elif data.startswith('rate_'):
        await handle_rating(event, sender_id, data)

    # Confirmação de Endereço
    elif data == 'address_confirm_yes':
        await handle_address_confirm_yes(event, sender_id)
    elif data == 'address_confirm_no':
        await handle_address_confirm_no(event, sender_id)

    # Lógica baseada no tipo de usuário
    user_context = event.client.get_user_data(sender_id, "user", {})
    if not user_context and user:
        user_context = user

    user_type = user_context.get('type')

    if user_type == 'motorista':
        await handle_driver_callback(event, user_context, sender_id, data)
    elif user_type == 'passageiro':
        await handle_passenger_callback(event, sender_id, data)
    else:
        await event.answer()


async def handle_start(event, sender_id, data):
    sender = await event.get_sender()
    if data == 'drive':
        user_data = {
            'user_id': sender_id,
            'first_name': sender.first_name,
            'username': sender.username,
            'type': 'motorista'
        }
        await event.client.controller.create_user(user_data['type'], **user_data)
        event.client.set_user_data(sender_id, "new_user", user_data)
        event.client.set_user_state(sender_id, State.WAIT_INPUT_PIX_KEY)
        await event.respond('💸 **Qual é a sua chave PIX?**')
        await event.delete()
    elif data == 'travel':
        user_data = {
            'user_id': sender_id,
            'first_name': sender.first_name,
            'username': sender.username,
            'type': 'passageiro'
        }
        await event.client.controller.create_user(user_data['type'], **user_data)
        event.client.set_user_data(sender_id, "user", user_data)
        await event.reply(
            '🚀 **Vamos viajar!**\nEnvia tua localização ou digita o endereço aí embaixo.',
            buttons=[
                [Button.request_location('🧭 Minha Localização', resize=True)],
                [Button.text('⌨️ Digitar Endereço', resize=True)],
                [Button.text('🔙 Voltar', resize=True)]
            ]
        )
        await event.delete()


async def handle_drive(event, sender_id):
    user_data = event.client.get_user_data(sender_id, "new_user", {})
    existing_user = await event.client.controller.check_user_exists(sender_id)
    if not existing_user:
        new_user = await event.client.controller.create_user('motorista', **user_data)
        event.client.set_user_data(sender_id, "user", new_user)

    await event.respond('✨ **Bem-vindo, Motorista!** ✨\n\n💠 **Qual a sua chave PIX?**')
    event.client.set_user_state(sender_id, State.WAIT_INPUT_PIX_KEY)
    from telethon.tl.functions.bots import SetBotCommandsRequest
    from telethon.tl.types import BotCommandScopePeer, BotCommandScopeChat
    from drivematch.constants import DRIVER_COMMANDS
    await event.client(SetBotCommandsRequest(
        scope=BotCommandScopeChat(peer=sender_id),
        lang_code='',
        commands=DRIVER_COMMANDS
    ))


async def handle_travel(event, sender_id):
    user_data = event.client.get_user_data(sender_id, "new_user", {})
    existing_user = await event.client.controller.check_user_exists(sender_id)
    if not existing_user:
        new_user = await event.client.controller.create_user('passageiro', **user_data)
        event.client.set_user_data(sender_id, "user", new_user)

    await event.reply("🎉 **Vamos viajar!**\n\n🧭 Compartilhe sua localização.", buttons=[
        [Button.request_location('🧭 Localização', resize=True, single_use=True)],
        [Button.text('👋 Digitar Endereço', resize=True)]
    ])
    event.client.set_user_state(sender_id, State.WAIT_PASSENGER_LOCATION)


async def handle_confirm_payment(event, sender_id, data):
    travel_id = int(data.split('_')[2])
    if verify_payment_status(travel_id):
        travel = await event.client.controller.confirm_payment(travel_id)
        if travel:
            await event.edit(
                "✅ **Pagamento Identificado!**\n"
                "A plataforma confirmou o seu pagamento. "
                "Sua viagem foi concluída com sucesso!"
            )
            driver_user_id = travel['driver']['user_id']
            buttons = [
                [Button.inline("✅ Confirmar Recebimento", f"driver_ack_{travel_id}")]
            ]
            await event.client.send_message(
                driver_user_id,
                f"💰 **Dinheiro na Conta!**\n\n"
                f"O pagamento da viagem #{travel_id} foi validado e creditado.\n"
                f"Valor: **R$ {travel['driver_amount']:.2f}**\n\n"
                f"Por favor, confira seu saldo e confirme abaixo.",
                buttons=buttons
            )
        else:
            await event.respond("❌ Esta viagem já foi processada ou não existe.")
    else:
        await event.answer(
            "⏳ Pagamento ainda não identificado. Tente novamente em instantes.",
            alert=True
        )


async def handle_driver_acknowledgment(event, sender_id, data):
    int(data.split('_')[2])
    await event.edit(
        f"✅ **Recebimento Conferido!**\n\n"
        f"O valor desta viagem já consta no seu saldo acumulado.\n"
        f"Use /wallet para acompanhar seu saldo atual."
    )


async def handle_rate_ask(event, sender_id, data):
    try:
        travel_id = int(data.split('_')[2])
        travel = await event.client.controller.get_travel_by_id(travel_id)
        if not travel:
            return await event.answer("🧨 Viagem não encontrada.", alert=True)

        user_db_id = event.client.get_user_data(sender_id, "user", {}).get('id')
        if not user_db_id:
            user = await event.client.controller.check_user_exists(sender_id)
            user_db_id = user.get('id')

        target_db_id = (
            travel['driver']['id']
            if user_db_id == travel['passenger']['id']
            else travel['passenger']['id']
        )

        buttons = [
            [
                Button.inline("⭐", f"rate_1_{travel_id}_{target_db_id}"),
                Button.inline("⭐⭐", f"rate_2_{travel_id}_{target_db_id}"),
                Button.inline("⭐⭐⭐", f"rate_3_{travel_id}_{target_db_id}"),
            ],
            [
                Button.inline("⭐⭐⭐⭐", f"rate_4_{travel_id}_{target_db_id}"),
                Button.inline("⭐⭐⭐⭐⭐", f"rate_5_{travel_id}_{target_db_id}"),
            ],
            [Button.inline("🔙 Cancelar", "return")]
        ]
        await event.edit(
            "🌟 **Como foi sua experiência?**\n"
            "Selecione uma nota de 1 a 5 estrelas:",
            buttons=buttons
        )
    except Exception as e:
        logging.error(f"Erro em handle_rate_ask: {e}")
        await event.answer("🧨 Erro ao abrir menu de avaliação.", alert=True)


async def handle_rating(event, sender_id, data):
    try:
        parts = data.split('_')
        stars = int(parts[1])
        travel_id = int(parts[2])
        target_db_id = int(parts[3])
        rater_db_id = event.client.get_user_data(sender_id, "user", {}).get('id')

        await event.client.controller.add_review(travel_id, rater_db_id, target_db_id, stars)
        await event.edit(
            f"🌟 **Avaliação de {stars} estrelas registrada!**\n"
            f"Obrigado por seu feedback."
        )
    except Exception as e:
        logging.error(f"Erro em handle_rating: {e}")
        await event.answer("🧨 Erro ao registrar avaliação.", alert=True)


async def handle_driver_callback(event, user, sender_id, data):
    if data.startswith('accept_'):
        await handle_accept_travel(event, user, sender_id, data)
    elif data == 'decline_trip':
        await event.delete()
        # PRECISO MELHORAR ISSO...
        # NOTIFICAR PASSAGEIRO SE O NÚMERO DE
        # MOTORISTAS FOR 0.
    elif data == 'request_withdraw':
        success, msg = await event.client.controller.request_payout(sender_id)
        await event.answer(msg, alert=True)
        if success:
            from smartbot.config import ADMIN_IDS
            admin_msg = (
                f"🔔 **Nova Solicitação de Saque**\n"
                f"👤 {user.get('first_name')}\n"
                f"💰 Valor: R$ {user.get('balance', 0.0):.2f}"
            )
            for admin_id in ADMIN_IDS:
                await event.client.send_message(admin_id, admin_msg)



async def handle_accept_travel(event, user, sender_id, data):
    try:
        passenger_id = int(data.split('_')[1])
        passenger = await event.client.controller.check_user_exists(passenger_id)

        if not passenger:
            return await event.respond('🧨 Passageiro não encontrado.')

        travel = await event.client.controller.get_travel(passenger['id'])
        if not travel or travel.get('status') != 'requesting':
            return await event.respond('🧨 Solicitação indisponível ou já aceita.')

        user_name = (
            f'@{user["username"]}' if user["username"]
            else f'{user["first_name"]} {user["last_name"] or ""}'
        )

        await event.client.controller.accept_travel(travel['id'], user['id'])

        await event.client.send_message(
            passenger_id,
            f'✅ Seu pedido de corrida foi aceito!\n'
            f'🧑‍✈️ Motorista: {user_name}\n'
            f'🚗 Carro: {user["type_vehicle"]}\n'
            f'🚘 Placa: {user["plate"]}\n\n'
            f'__**Para cancelar a viagem \n'
            f'digite o comando**__ /cancel\n'
        )

        await event.respond(
            '📲 Envie sua localização para o passageiro acompanhar.',
            buttons=[Button.request_location('🧭 Compartilhar GPS', resize=True)]
        )
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    except Exception as e:
        logging.error(f"Erro ao aceitar viagem: {e}")
        await event.respond('🧨 Ocorreu um erro ao processar o aceite.')


async def handle_passenger_callback(event, sender_id, data):
    await event.delete()
    if data == 'search_driver':
        await search_driver(event, sender_id)
    elif data == 'cancel_driver':
        await event.respond("❎ **Busca cancelada.**")


async def search_driver(event, sender_id):
    try:
        status_msg = await event.respond('🕵️‍♂️ **Buscando motoristas próximos (10km)...**')
        settings = await event.client.storage.get(f"settings:{sender_id}", {})

        origin = settings.get("address").get("origin")
        destination = settings.get("address").get("destination")
        origin_lat = settings.get("address", {}).get("latitude")
        origin_lon = settings.get("address", {}).get("longitude")
        travel_distance = settings.get("address", {}).get("distance")
        travel_time = settings.get("address", {}).get("time")
        location_url = settings.get("address", {}).get("url")

        user = await event.client.controller.check_user_exists(sender_id)
        drivers = await event.client.controller.find_nearby_drivers(
            origin_lat, origin_lon, radius_km=10.0
        )

        if not drivers:
            return await status_msg.edit('😔 Nenhum motorista disponível no momento nesta região.')

        passenger = event.client.get_user_data(sender_id, "user", {})
        if not passenger or not passenger.get('id'):
            passenger = await event.client.controller.check_user_exists(sender_id)
            event.client.set_user_data(sender_id, "user", passenger)

        travel = await event.client.controller.create_travel(passenger["id"])

        notified_count = 0
        for d in drivers:
            sys_settings = await event.client.controller.get_system_settings()

            split_percent = user.get('custom_fee_percentage')
            if split_percent is None:
                split_percent = sys_settings.get('default_platform_percentage', 20.0)

            platform_percentage_decimal = Decimal(str(split_percent / 100))

            settings = await event.client.storage.get(f"settings:{travel['passenger']['user_id']}", {})
            dist_str = settings.get("address", {}).get("distance", "0 km")
            time_str = settings.get("address", {}).get("time", "0 min")
            dist_km = float(dist_str.split()[0].replace(',', '.'))
            time_min = float(time_str.split()[0].replace(',', '.'))

            total_fare = calculate_fare(
                sys_settings['base_fare'],
                sys_settings['price_per_km'],
                sys_settings['price_per_min'],
                sys_settings['service_fee'],
                dist_km,
                time_min
            )

            platform_fee = calculate_percent(total_fare, platform_percentage_decimal)
            driver_share = total_fare - platform_fee

            if d['user_id'] != sender_id:
                buttons = [
                    [Button.inline('✅ Aceitar', f'accept_{sender_id}')],
                    [Button.inline('❌ Recusar', 'decline_trip')]
                ]
                await event.client.send_message(
                    d['user_id'],
                    f"🎫 __**Nova Solicitação de Viagem**__\n"
                    f"🧔‍♂️ Passageiro: {user.get('username') or user.get('first_name')}\n"
                    f"▶️ Origem: {origin}\n"
                    f"⏹️ Destino: {destination}\n"
                    f"📏 Distância: {reformat_distance(travel_distance, 500)}\n"
                    f"🧭 Tempo: {update_time(travel_time, 500)}\n"
                    f"💰 Você recebe: **R$ {driver_share:.2f}**\n"
                    f"🛣️ Trajeto: [Confira aqui o trajeto]({location_url})\n",
                    buttons=buttons
                )
                notified_count += 1
            await asyncio.sleep(5)

        if notified_count > 0:
            await status_msg.edit(
                f'📡 **Solicitação enviada para {notified_count} motorista(s)!**',
                buttons=[
                    [Button.inline('❌ Cancelar', 'cancel_driver')]
                ]
            )
        else:
            await status_msg.edit('😔 Nenhum motorista online disponível.')
    except Exception as e:
        logging.error(f"Erro em search_driver: {e}")
        await event.respond('🧨 Erro ao buscar motoristas. Tente novamente.')


async def handle_address_confirm_no(event, sender_id):
    settings = await event.client.storage.get(f"settings:{sender_id}", {})
    pending = settings.get("pending_confirm", {})
    p_type = pending.get("type")

    if p_type == "driver_location":
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    elif p_type == "origin":
        event.client.set_user_state(sender_id, State.WAIT_INPUT_ORIGIN)
    elif p_type == "destination":
        event.client.set_user_state(sender_id, State.WAIT_INPUT_DESTINATION)

    settings.pop("pending_confirm", None)
    await event.client.storage.set(f"settings:{sender_id}", settings)

    await event.edit("❌ **Entendido.** Por favor, digite o endereço novamente de forma mais clara:")


async def handle_address_confirm_yes(event, sender_id):
    settings = await event.client.storage.get(f"settings:{sender_id}", {})
    pending = settings.get("pending_confirm", {})
    if not pending:
        return await event.answer("🧨 Dados expirados ou não encontrados.", alert=True)

    p_type = pending.get("type")
    lat = pending.get("latitude")
    lon = pending.get("longitude")
    addr = pending.get("address")

    settings.pop("pending_confirm", None)
    if "address" not in settings: settings["address"] = {}

    if p_type == "driver_location":
        await event.client.controller.update_user_location(sender_id, lat, lon)
        settings["address"].update({
            "origin": addr,
            "latitude": lat,
            "longitude": lon
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)

        user_context = event.client.get_user_data(sender_id, "user", {})
        if not user_context:
            user_context = await event.client.controller.check_user_exists(sender_id)

        user_context['is_active'] = True
        event.client.set_user_data(sender_id, "user", user_context)
        await event.client.controller.edit_user(**user_context)

        # Se estiver em viagem, notifica passageiro
        travel = await event.client.controller.get_travel(user_context.get('id'))
        if travel and travel.get('passenger') and travel.get('status') in ['accepted', 'in_progress']:
            passenger_id = travel['passenger']["user_id"]
            await event.edit(
                f"✅ **Localização Confirmada!**\n"
                f"Seu local atual é **{addr}**\n\n"
                f"👉 Clique em /road quando seu passageiro embarcar.\n"
                f"__**Para cancelar a viagem \n"
                f"digite o comando**__ /cancel\n"
            )
            await event.client.send_live_location(passenger_id, float(lat), float(lon), 100)
            await event.client.send_message(passenger_id, f"📍 **O motorista informou sua localização:**\n{addr}")
        else:
            await event.edit(f"📡 **Você está Online!**\n🧭 Posição: **{addr}**")

    elif p_type == "origin":
        settings["address"].update({
            "origin": addr,
            "latitude": lat,
            "longitude": lon
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)
        event.client.set_user_state(sender_id, State.WAIT_INPUT_DESTINATION)
        await event.edit(f"✅ **Ponto de partida definido!**\n📍 {addr}")
        await event.respond("👉 Para onde vamos?")

    elif p_type == "destination":
        settings["address"].update({
            "destination": addr,
            "destination_lat": lat,
            "destination_lon": lon
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)

        await event.edit(f"🏁 **Destino definido!**\n📍 {addr}")
        status_msg = await event.respond('🛣️ Ok, aguarde enquanto buscamos informações sobre o trajeto...')

        origin = settings["address"].get("origin")
        location_dict = get_address_info(origin, addr) if origin else {}

        if not location_dict:
            return await status_msg.edit('🚨 Não consegui calcular a rota. Tente /start novamente.')

        dist_str, time_str = location_dict['distance'], location_dict['time']
        dist_km = float(dist_str.split()[0].replace(',', '.'))
        time_min = float(time_str.split()[0].replace(',', '.'))

        # Configurações do sistema para cálculo de taxa
        sys_settings = await event.client.controller.get_system_settings()

        tax_amount = calculate_fare(
            sys_settings['base_fare'],
            sys_settings['price_per_km'],
            sys_settings['price_per_min'],
            sys_settings['service_fee'],
            dist_km,
            time_min
        )

        settings.update({
            "address": {
                **settings["address"],
                "distance": dist_str,
                "time": time_str,
                "url": location_dict['url']
            },
            "offer_amount": float(tax_amount)
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)

        buttons = [
            [Button.inline('🔎 Buscar motorista', data='search_driver')],
            [Button.url('🗺️ Visualizar mapa', url=location_dict['url'])],
            [Button.inline('⬅️ Voltar', data='return')]
        ]

        new_time = add_minutes_to_current_time(time_min + 6)
        await status_msg.edit(
            f'🔛 A distância entre o seu local e o seu \n'
            f'destino é de {dist_str} e o tempo de viagem é de {time_str}.\n'
            f'Com previsão de chegada às {new_time.strftime("%H:%M")} .\n'
            f'💸 O valor dessa corrida é de R$ {Decimal(tax_amount):.2f}\n'
            f'💰 Pague via PIX agora mesmo.\n'
            f'💠 Chave: cleiton.leonel@gmail.com',
            buttons=buttons
        )

    await event.answer()
