import logging
from telethon import events
from smartbot.utils.handler import ClientHandler
from drivematch.utils.location import get_full_address, calculate_distance
from drivematch.utils.state import State

client = ClientHandler()


@client.on(events.NewMessage(func=lambda e: e.geo))
async def handle_location(event):
    sender_id = event.sender_id

    if event.message.geo:
        latitude, longitude = event.message.geo.lat, event.message.geo.long
        logging.info(f"📍 Localização recebida do usuário {sender_id}: {latitude}, {longitude}")
        full_address = get_full_address(latitude, longitude)
        if not full_address:
            logging.error(f"Falha ao obter endereço para a localização {latitude}, {longitude}")
            full_address = "Endereço desconhecido"

        try:
            # Atualizar cache Redis (usando storage do bot)
            await update_user_runtime_settings(event.client, sender_id, latitude, longitude, full_address)
            # Atualizar Banco de Dados (PostGIS)
            await event.client.controller.update_user_location(sender_id, latitude, longitude)

            user = event.client.get_user_data(sender_id, "user")
            if not user:
                user = await event.client.controller.check_user_exists(sender_id)

            if user:
                user['is_active'] = True
                event.client.set_user_data(sender_id, "user", user)
                await event.client.controller.edit_user(**user)
            else:
                return await event.respond('❌ **Erro:** Usuário não encontrado no sistema.')
        except Exception as e:
            logging.error(f"Erro ao processar localização do usuário {sender_id}: {e}")
            return await event.respond('❌ **Erro:** Ocorreu um problema ao processar sua localização.')

        user_type = user.get('type')
        state = event.client.get_user_state(sender_id)

        if user_type == 'motorista' and state == State.WAIT_DRIVER_LOCATION:
            travel = await event.client.controller.get_travel(user.get('id'))
            if travel and travel.get('passenger') and travel.get('status') in ['accepted', 'in_progress']:
                await event.reply(
                    f"✅ **PEDIDO ACEITO!**\n\n"
                    f"Seu local atual é: __({full_address})__\n\n"
                    f"👉 Utilize o comando /road quando seu passageiro embarcar.\n"
                    f"⚠️ **Para cancelar a viagem, utilize o comando:** /cancel"
                )
                passenger_id = travel['passenger']["user_id"]

                # Lógica de Proximidade
                p_settings = await event.client.storage.get(f"settings:{passenger_id}", {})
                p_lat = p_settings.get("address", {}).get("latitude")
                p_lon = p_settings.get("address", {}).get("longitude")

                if p_lat and p_lon:
                    dist = calculate_distance(latitude, longitude, p_lat, p_lon)
                    m_settings = await event.client.storage.get(f"settings:{sender_id}", {})
                    notified = m_settings.get("arrival_notified")

                    if dist < 200 and not notified:
                        await event.client.send_message(
                            passenger_id,
                            "🚖 **O motorista está chegando!**\n\n"
                            f"Ele está a cerca de **{int(dist)} metros** de você. Prepare-se!"
                        )
                        m_settings["arrival_notified"] = True
                        await event.client.storage.set(f"settings:{sender_id}", m_settings)

                return await handle_confirm_location(event.client, sender_id, p_lat, p_lon, passenger_id)
            else:
                return await event.reply(
                    f"📡 **VOCÊ ESTÁ ONLINE!**\n\n"
                    f"🧭 Posição capturada:\n__({full_address})__\n\n"
                    "📳 Você será notificado assim que novas viagens surgirem.\n"
                    "💆‍♂️ Fique à vontade e aguarde chamadas."
                )

        elif user_type == 'passageiro' and state == State.WAIT_PASSENGER_LOCATION:
            travel = await event.client.controller.get_travel(user.get('id'))
            if travel and travel.get('driver') and travel.get('status') in ['accepted', 'in_progress']:
                await event.reply(f'🧭 Sua localização atual é: \n{full_address}')
                driver_id = travel['driver']["user_id"]
                return await handle_confirm_location(event.client, sender_id, latitude, longitude, driver_id)

            # Localização de ORIGEM
            first_name = user.get('first_name', 'Passageiro')
            await event.reply(
                f'✅ **Tudo certo, {first_name}!**\n\n'
                f'🧭 Sua localização capturada:\n__({full_address})__'
            )
            event.client.set_user_state(sender_id, State.WAIT_INPUT_DESTINATION)
            return await event.respond('👉 **Para onde vamos?** Por favor, digite seu destino.')

    return await event.respond('⚠️ **Aviso:** Não consegui obter sua localização.')


async def update_user_runtime_settings(tg_client, sender_id, latitude, longitude, full_address):
    settings = await tg_client.storage.get(f"settings:{sender_id}", {"address": {}})
    if "address" not in settings: settings["address"] = {}
    settings["address"].update({
        "origin": full_address,
        "latitude": latitude,
        "longitude": longitude
    })
    await tg_client.storage.set(f"settings:{sender_id}", settings)


async def handle_confirm_location(tg_client, sender_id, latitude, longitude, chat_id):
    live_location_message = await tg_client.send_live_location(chat_id, float(latitude), float(longitude), 100)
    settings = await tg_client.storage.get(f"settings:{sender_id}", {"address": {}})
    if "address" not in settings: settings["address"] = {}
    settings["address"]["live_location_message"] = (
        live_location_message.id if hasattr(live_location_message, 'id') else live_location_message
    )
    await tg_client.storage.set(f"settings:{sender_id}", settings)
