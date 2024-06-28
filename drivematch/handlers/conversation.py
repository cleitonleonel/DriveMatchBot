from decimal import Decimal
from telethon import (
    events,
    Button
)
from telethon.tl.types import MessageActionGeoProximityReached

from drivematch.utils.location import (
    get_address_info,
    get_coordinates,
    add_minutes_to_current_time
)
from drivematch.utils.authentication import (
    process_get_contact,
    process_code_activation,
    process_two_steps_verification
)
from drivematch.utils.decorators import handler
from drivematch.utils.rates import calculate_fare


@handler
def register_conversation_handlers(bot, instance):
    @bot.on(events.NewMessage(pattern=r'^(?!\/).*'))
    async def handle_conversation(event):
        sender = await event.get_sender()
        sender_id = sender.id
        text = event.raw_text
        state = instance.conversation_state.get(sender_id)
        if not instance.users_dict.get(sender_id):
            return
        user_type = instance.users_dict[sender_id].get('type')

        if text == '👋 Inserir Local' or text == '👋 Viajar':
            instance.conversation_state[sender_id] = instance.state.WAIT_MATCH
            state = instance.conversation_state.get(sender_id)

        if user_type == 'motorista':
            await handle_driver_conversation(event, sender_id, state, text)

        elif user_type == 'passageiro':
            await handle_passenger_conversation(event, sender_id, state, text)

        await handle_common_conversation(event, sender_id, state, text)

    async def handle_driver_conversation(event, sender_id, state, text):
        if state == instance.state.WAIT_INPUT_PIX_KEY:
            await process_pix_key(event, sender_id, text)
        elif state == instance.state.WAIT_INPUT_VEHICLE:
            await process_vehicle_info(event, sender_id, text)
        elif state == instance.state.WAIT_INPUT_PLATE:
            await process_vehicle_plate(event, sender_id, text)

        instance.controller.edit_user(**instance.users_dict[sender_id])

    async def handle_passenger_conversation(event, sender_id, state, text):
        if state == instance.state.WAIT_MATCH:
            await start_match(event, sender_id)
        elif state == instance.state.WAIT_INPUT_ORIGIN:
            await process_origin(event, sender_id, text)
        elif state == instance.state.WAIT_INPUT_DESTINATION:
            await process_destination(event, sender_id, text)

    async def handle_common_conversation(event, sender_id, state, text):
        if state == instance.state.WAIT_CODE_ACTIVATION:
            await process_code_activation(instance, event, sender_id, text)
        elif state == instance.state.WAIT_TWO_STEPS_VERIFICATION:
            await process_two_steps_verification(instance, event, sender_id, text)
        elif state == instance.state.WAIT_GET_CONTACT:
            await process_get_contact(instance, event, sender_id)

        # Adicionando verificação para eventos de proximidade
        elif event.message.action and isinstance(event.message.action, MessageActionGeoProximityReached):
            await handle_proximity_event(event)

    async def process_pix_key(event, sender_id, pix_key):
        instance.users_dict[sender_id]["pix_key"] = pix_key
        instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_VEHICLE
        await event.respond('🚗 Insira agora informações sobre seu veículo: ')

    async def process_vehicle_info(event, sender_id, type_vehicle):
        instance.users_dict[sender_id]["type_vehicle"] = type_vehicle
        instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_PLATE
        await event.respond('🚘 Insira também a placa de seu veículo: ')

    async def process_vehicle_plate(event, sender_id, plate):
        instance.users_dict[sender_id]["plate"] = plate
        await event.respond(
            f'✨ Configurações concluídas com sucesso!\n'
            f'⏳ Agora é só aguardar por corridas.\n'
            f'🗣️ Avisaremos se algum passageiro solicitar.'
        )
        await instance.delete_conversation(sender_id)

    async def process_destination(event, sender_id, destination):
        instance.runtime_settings[sender_id]["address"]["destination"] = destination
        await event.respond(
            '🛣️ Ok, aguarde enquanto buscamos informações sobre o trajeto.',
            buttons=Button.clear()
        )
        origin = instance.runtime_settings[sender_id]["address"]["origin"]
        locantion_dict = get_address_info(origin, destination)
        if not locantion_dict:
            return await event.respond(
                '🚨 Não consegui encontrar seu endereço.\n'
                '🔄 Verifique o endereço e tente novamente.'
            )

        distance = locantion_dict.get('distance')
        travel_time = locantion_dict.get('time')
        distance_km = float(distance.split()[0].replace(',', '.'))
        time_min = float(travel_time.split()[0].replace(',', '.'))
        location_url = locantion_dict.get('url')
        instance.runtime_settings[sender_id]["address"]["distance"] = distance
        instance.runtime_settings[sender_id]["address"]["time"] = travel_time
        instance.runtime_settings[sender_id]["address"]["url"] = location_url
        buttons = create_buttons(location_url)
        tax_amount = calculate_fare(
            base_fare=2.00,
            cost_per_km=0.71,
            cost_per_minute=0.42,
            service_fee=0.75,
            distance_km=distance_km,
            time_min=time_min,
            surge_multiplier=1.0
        )
        new_time = add_minutes_to_current_time(time_min + 6)
        await event.respond(
            f'🔛 A distância entre o seu local e o seu destino\n'
            f'é de {distance} e o tempo de viagem é de {travel_time}.\n'
            f'Com previsão de chegada às {new_time.strftime("%H:%M")} .\n'
            f'💸 O valor dessa corrida é de R$ {Decimal(tax_amount):.2f}\n'
            f'💰 Pague via PIX agora mesmo.\n'
            f'💠 Chave: 1234567890987654321',  # Chave Pix Fake
            buttons=buttons
        )

    def create_buttons(location_url):
        return [
            [Button.inline('🔎 Buscar motorista', data='search_driver')],
            [Button.url('🗺️ Visualizar mapa', url=location_url)],
            [Button.inline('⬅️ Voltar', data='return')]
        ]

    async def start_match(event, sender_id):
        await instance.remove_message(event.sender_id, event.id)
        instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_ORIGIN
        await event.respond('👉 Insira o local de partida.')

    async def process_origin(event, sender_id, origin):
        instance.runtime_settings[sender_id]["address"]["origin"] = origin
        latitude, longitude = get_coordinates(origin)
        instance.runtime_settings[sender_id]["address"]["latitude"] = latitude
        instance.runtime_settings[sender_id]["address"]["longitude"] = longitude
        instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_DESTINATION
        await event.respond('👉 Para onde vamos?')

    async def handle_proximity_event(event):
        from_user_id = event.message.action.from_id
        to_user_id = event.message.action.to_id
        distance = event.message.action.distance
        await event.respond(
            f'🧭 O usuário {from_user_id} está a {distance} metros de {to_user_id}!'
        )
