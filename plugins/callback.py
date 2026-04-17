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
        await event.respond('👌 **Entendido.** Até a próxima!')
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
    elif data.startswith('tag_'):
        await event.answer("Obrigado pelo seu feedback!", alert=True)
        await event.delete()

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
    # Perfil / Edição
    elif data == 'edit_pix':
        event.client.set_user_state(sender_id, State.WAIT_INPUT_PIX_KEY)
        await event.respond('💸 **Qual é a sua nova chave PIX?**')
        await event.delete()
    elif data == 'edit_vehicle':
        event.client.set_user_state(sender_id, State.WAIT_INPUT_VEHICLE)
        await event.respond('🚗 **Veículo:** Por favor, insira o novo modelo e cor:')
        await event.delete()

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
            '🚀 **VAMOS VIAJAR!**\n\n'
            'Envie sua localização ou digite o endereço desejado abaixo.',
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

    await event.respond('✨ **BEM-VINDO, MOTORISTA!** ✨\n\n💠 **Por favor, informe sua chave PIX para repasses:**')
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

    await event.reply("🎉 **VAMOS VIAJAR!**\n\n🧭 **Por favor, compartilhe sua localização atual.**", buttons=[
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
                "✅ **PAGAMENTO IDENTIFICADO!**\n\n"
                "A plataforma confirmou o seu pagamento. "
                "Sua viagem foi concluída com sucesso!"
            )
            await event.respond("🫶 Obrigado por viajar com a __**Drivematch**__ !")
            driver_user_id = travel['driver']['user_id']
            buttons = [
                [Button.inline("✅ Confirmar Recebimento", f"driver_ack_{travel_id}")]
            ]
            await event.client.send_message(
                driver_user_id,
                f"💰 **DINHEIRO NA CONTA!**\n\n"
                f"O pagamento da viagem `#{travel_id}` foi validado e creditado.\n\n"
                f"💵 Valor: **R$ {travel['driver_amount']:.2f}**\n\n"
                f"💡 Por favor, confira seu saldo e confirme o recebimento abaixo.",
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
        f"✅ **RECEBIMENTO CONFERIDO!**\n\n"
        f"O valor desta viagem já foi adicionado ao seu saldo acumulado.\n"
        f"Utilize o comando /wallet para acompanhar seu saldo atual."
    )


async def handle_rate_ask(event, sender_id, data):
    try:
        travel_id = int(data.split('_')[2])
        travel = await event.client.controller.get_travel_by_id(travel_id)
        if not travel:
            return await event.answer("⚠️ **Aviso:** Viagem não encontrada.", alert=True)

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
            [
                Button.inline("Cordialidade 🤝", f"tag_cordial_{travel_id}"),
                Button.inline("Limpeza 🧼", f"tag_clean_{travel_id}"),
            ],
            [
                Button.inline("Direção Segura 🛡️", f"tag_safe_{travel_id}"),
                Button.inline("Rapidez ⚡", f"tag_fast_{travel_id}"),
            ],
            [Button.inline("🔙 Fechar", "return")]
        ]
        await event.edit(
            "🌟 **AVALIE SUA EXPERIÊNCIA**\n\n"
            "Como foi sua viagem? Selecione uma nota abaixo:",
            buttons=buttons
        )
    except Exception as e:
        logging.error(f"Erro em handle_rate_ask: {e}")
        await event.answer("❌ **Erro:** Não foi possível abrir o menu de avaliação.", alert=True)


async def handle_rating(event, sender_id, data):
    try:
        parts = data.split('_')
        stars = int(parts[1])
        travel_id = int(parts[2])
        target_db_id = int(parts[3])
        rater_db_id = event.client.get_user_data(sender_id, "user", {}).get('id')

        await event.client.controller.add_review(travel_id, rater_db_id, target_db_id, stars)
        await event.edit(
            f"🌟 **AVALIAÇÃO REGISTRADA!**\n\n"
            f"Você atribuiu **{stars} estrelas**. Obrigado pelo seu feedback!"
        )
    except Exception as e:
        logging.error(f"Erro em handle_rating: {e}")
        await event.answer("❌ **Erro:** Não foi possível registrar sua avaliação.", alert=True)


async def handle_driver_callback(event, user, sender_id, data):
    if data.startswith('accept_'):
        await handle_accept_travel(event, user, sender_id, data)
    elif data.startswith('decline_trip_'):
        await handle_decline_trip(event, sender_id, data)
    elif data == 'request_withdraw':
        success, msg = await event.client.controller.request_payout(sender_id)
        await event.answer(msg, alert=True)
        if success:
            from smartbot.config import ADMIN_IDS
            admin_msg = (
                f"🔔 **SOLICITAÇÃO DE SAQUE**\n\n"
                f"👤 **Motorista:** {user.get('first_name')}\n"
                f"💰 **Valor:** R$ {user.get('balance', 0.0):.2f}"
            )
            for admin_id in ADMIN_IDS:
                await event.client.send_message(admin_id, admin_msg)


async def handle_accept_travel(event, user, sender_id, data):
    try:
        passenger_id = int(data.split('_')[1])
        passenger = await event.client.controller.check_user_exists(passenger_id)

        if not passenger:
            return await event.respond('❌ **Erro:** Passageiro não encontrado.')

        travel = await event.client.controller.get_travel(passenger['id'])
        if not travel or travel.get('status') != 'requesting':
            return await event.respond('⚠️ **Aviso:** Esta solicitação não está mais disponível.')

        user_name = (
            f'@{user["username"]}' if user["username"]
            else f'{user["first_name"]} {user["last_name"] or ""}'
        )

        logging.info(f"Viagem {travel['id']} aceita pelo motorista {user_name} (ID DB: {user['id']})")
        success_travel = await event.client.controller.accept_travel(travel['id'], user['id'])
        if not success_travel:
            return await event.respond('❌ **Erro:** Não foi possível vincular você a esta viagem. Ela pode ter sido cancelada.')

        # Deletar status_msg do passageiro (Buscando motoristas...)
        p_status_msg_id = await event.client.storage.get(f"status_msg:{passenger_id}")
        logging.info(f"Tentando deletar msg {p_status_msg_id} do passageiro {passenger_id}")
        if p_status_msg_id:
            try: await event.client.delete_messages(passenger_id, p_status_msg_id)
            except: pass
        await event.client.storage.delete(f"status_msg:{passenger_id}")

        await event.client.send_message(
            passenger_id,
            f'✅ **SEU PEDIDO FOI ACEITO!**\n\n'
            f'🧑‍✈️ **Motorista:** {user_name}\n'
            f'🚗 **Veículo:** {user["type_vehicle"]}\n'
            f'🚘 **Placa:** {user["plate"]}\n\n'
            f'⚠️ **Para cancelar a viagem, utilize o comando:** /cancel'
        )

        await event.delete() # Deleta a mensagem de "Nova Solicitação de Viagem"
        await event.respond(
            '📲 **Por favor, envie sua localização para o passageiro acompanhar.**',
            buttons=[Button.request_location('🧭 Compartilhar GPS', resize=True)]
        )
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    except Exception as e:
        import traceback
        logging.error(f"Erro ao aceitar viagem: {e}")
        logging.error(traceback.format_exc())
        await event.respond('❌ **Erro:** Ocorreu um problema ao processar o aceite da viagem.')


async def handle_decline_trip(event, sender_id, data):
    try:
        parts = data.split('_')
        travel_id = int(parts[2])
        passenger_user_id = int(parts[3])

        await event.delete()
        
        # Incrementar contador de recusas
        declines = await event.client.storage.get(f"declines:{travel_id}", 0)
        declines += 1
        await event.client.storage.set(f"declines:{travel_id}", declines)

        notified = await event.client.storage.get(f"notified_count:{travel_id}", 0)
        
        if declines >= notified:
            await event.client.send_message(
                passenger_user_id,
                "⚠️ **AVISO DE DISPONIBILIDADE**\n\n"
                "Infelizmente, todos os motoristas próximos recusaram a sua solicitação no momento. "
                "Tente novamente em alguns minutos ou em outra localização."
            )

            # Cancelar viagem no banco de dados para liberar o passageiro para novas buscas
            travel = await event.client.controller.get_travel_by_id(travel_id)
            await event.client.controller.cancel_travel(travel_id, travel['passenger']['id'])

            # Limpar status_msg do passageiro
            p_status_msg_id = await event.client.storage.get(f"status_msg:{passenger_user_id}")
            if p_status_msg_id:
                try: await event.client.delete_messages(passenger_user_id, p_status_msg_id)
                except: pass
            await event.client.storage.delete(f"status_msg:{passenger_user_id}")

    except Exception as e:
        import traceback
        logging.error(f"Erro ao recusar viagem: {e}")
        logging.error(traceback.format_exc())


async def handle_passenger_callback(event, sender_id, data):
    await event.delete()
    if data == 'search_driver':
        await search_driver(event, sender_id)
    elif data == 'cancel_driver':
        await event.respond("✅ **Busca cancelada.**")


async def search_driver(event, sender_id):
    try:
        status_msg = await event.respond('🕵️‍♂️ **Buscando motoristas disponíveis (10km)...**')
        await event.client.storage.set(f"status_msg:{sender_id}", status_msg.id)
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

        # Se não encontrar motoristas, deletar msg de busca
        if not drivers:
            await status_msg.delete()
            return await event.respond('⚠️ **Aviso:** Nenhum motorista disponível nesta região no momento.')

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
                    [Button.inline('❌ Recusar', f'decline_trip_{travel["id"]}_{sender_id}')]
                ]
                await event.client.send_message(
                    d['user_id'],
                    f"🎫 **NOVA SOLICITAÇÃO DE VIAGEM**\n\n"
                    f"🧔‍♂️ **Passageiro:** {user.get('username') or user.get('first_name')}\n"
                    f"▶️ **Origem:** __({origin})__\n"
                    f"⏹️ **Destino:** __({destination})__\n"
                    f"📏 **Distância:** {reformat_distance(travel_distance, 500)}\n"
                    f"⏱️ **Tempo:** {update_time(travel_time, 500)}\n\n"
                    f"💰 **Você recebe:** **R$ {driver_share:.2f}**\n\n"
                    f"🛣️ **Trajeto:** [Clique para ver no mapa]({location_url})\n",
                    buttons=buttons
                )
                notified_count += 1
            await asyncio.sleep(5)

        await event.client.storage.set(f"notified_count:{travel['id']}", notified_count)

        if notified_count > 0:
            await status_msg.edit(
                f'📡 **Solicitação enviada para {notified_count} motorista(s)!**\n'
                f'Aguarde enquanto alguém aceita sua corrida.',
                buttons=[
                    [Button.inline('❌ Cancelar Busca', 'cancel_driver')]
                ]
            )
            # Iniciar timeout em background
            asyncio.create_task(travel_timeout_check(event.client, travel['id'], sender_id))
        else:
            await status_msg.edit('⚠️ **Aviso:** Nenhum motorista online no momento.')
    except Exception as e:
        logging.error(f"Erro em search_driver: {e}")
        try: await status_msg.delete()
        except: pass
        await event.respond('❌ **Erro:** Não foi possível buscar motoristas. Tente novamente em instantes.')


async def travel_timeout_check(client, travel_id, passenger_user_id):
    await asyncio.sleep(300) # 5 minutos
    travel = await client.controller.get_travel_by_id(travel_id)
    if travel and travel['status'] == 'requesting':
        await client.controller.cancel_travel(travel_id, passenger_user_id)
        await client.send_message(
            passenger_user_id,
            "⏰ **TIMEOUT DE BUSCA**\n\n"
            "Não conseguimos encontrar um motorista para você nos últimos 5 minutos. "
            "Sua solicitação foi encerrada. Tente novamente mais tarde."
        )
        # Limpar status_msg se ainda existir
        p_status_msg_id = await client.storage.get(f"status_msg:{passenger_user_id}")
        if p_status_msg_id:
            try: await client.delete_messages(passenger_user_id, p_status_msg_id)
            except: pass
        await client.storage.delete(f"status_msg:{passenger_user_id}")


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

    await event.edit("✅ **Entendido.** Por favor, informe o endereço novamente com mais detalhes:")


async def handle_address_confirm_yes(event, sender_id):
    settings = await event.client.storage.get(f"settings:{sender_id}", {})
    pending = settings.get("pending_confirm", {})
    if not pending:
        return await event.answer("⚠️ **Aviso:** Dados expirados. Por favor, tente novamente.", alert=True)

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
            await event.delete() # Deleta menu de confirmação
            await event.respond(
                f"✅ **LOCALIZAÇÃO CONFIRMADA!**\n\n"
                f"Seu local atual é: __{addr}__\n\n"
                f"👉 Utilize o comando /road quando seu passageiro embarcar.\n"
                f"⚠️ **Para cancelar a viagem, utilize o comando:** /cancel"
            )
            await event.client.send_live_location(passenger_id, float(lat), float(lon), 100)
            await event.client.send_message(passenger_id, f"📍 **O motorista informou sua localização:**\n{addr}")
        else:
            await event.delete() # Deleta menu de confirmação
            await event.respond(f"📡 **VOCÊ ESTÁ ONLINE!**\n\n🧭 Posição: __({addr})__")

    elif p_type == "origin":
        settings["address"].update({
            "origin": addr,
            "latitude": lat,
            "longitude": lon
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)
        event.client.set_user_state(sender_id, State.WAIT_INPUT_DESTINATION)
        await event.delete() # Deleta menu de confirmação
        await event.respond(f"✅ **PONTO DE PARTIDA DEFINIDO!**\n\n📍 __{addr}__")
        prompt = await event.respond("👉 **Para onde vamos?**")
        await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)

    elif p_type == "destination":
        settings["address"].update({
            "destination": addr,
            "destination_lat": lat,
            "destination_lon": lon
        })
        await event.client.storage.set(f"settings:{sender_id}", settings)

        await event.delete() # Deleta menu de confirmação
        await event.respond(f"🏁 **DESTINO DEFINIDO!**\n\n📍 __{addr}__")
        status_msg = await event.respond('🛣️ **Calculando rota...** Por favor, aguarde.')

        origin = settings["address"].get("origin")
        location_dict = get_address_info(origin, addr) if origin else {}

        if not location_dict:
            return await status_msg.edit('⚠️ **Aviso:** Não consegui calcular a rota. Verifique os endereços e tente novamente.')

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
            f'🗺️ **INFORMAÇÕES DO TRAJETO**\n\n'
            f'📏 **Distância:** {dist_str}\n'
            f'⏱️ **Tempo de viagem:** {time_str}\n'
            f'🏁 **Previsão de chegada:** {new_time.strftime("%H:%M")}\n\n'
            f'💵 **VALOR ESTIMADO: R$ {Decimal(tax_amount):.2f}**\n\n'
            f'💡 O pagamento é feito via PIX direto para o motorista ao final da viagem.',
            buttons=buttons
        )
        # Deletar status_msg após o passageiro buscar motorista ou voltar? 
        # Vamos manter por enquanto pois tem botões úteis.

    await event.answer()
