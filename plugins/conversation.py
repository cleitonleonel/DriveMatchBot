from decimal import Decimal
from telethon import events, Button
from telethon.tl.types import MessageActionGeoProximityReached
from smartbot.utils.handler import ClientHandler
from drivematch.utils.location import (
    get_address_info,
    get_coordinates,
    get_full_address,
    add_minutes_to_current_time
)
from drivematch.utils.authentication import (
    process_get_contact,
    process_code_activation,
    process_two_steps_verification
)
from drivematch.utils.rates import calculate_fare
from drivematch.utils.state import State

client = ClientHandler()


@client.on(events.NewMessage(pattern=r'^(?!\/).*'))
async def handle_conversation(event):
    BUTTON_BLACKLIST = ["🧭 Minha Localização", "📡 Ficar Online (GPS)", "🧭 Localização"]
    if event.geo or event.message.media or event.raw_text in BUTTON_BLACKLIST:
        return

    sender_id = event.sender_id
    text = event.raw_text

    state = event.client.get_user_state(sender_id)
    # Normaliza o estado para string para evitar erros de comparação com Enum
    state_str = state.value if hasattr(state, 'value') else str(state)

    user_context = event.client.get_user_data(sender_id, "user")
    if not user_context:
        user_context = await event.client.controller.check_user_exists(sender_id)
        if user_context:
            event.client.set_user_data(sender_id, "user", user_context)

    if not user_context and state_str != "start":
        user_context = event.client.get_user_data(sender_id, "new_user")

    if not user_context:
        return

    user_type = user_context.get('type')

    if text in ['👋 Inserir Local', '👋 Viajar', '👋 Iniciar Viagem']:
        event.client.set_user_state(sender_id, State.WAIT_MATCH)
        state_str = "wait_match"

    if text in ['👋 Digitar Endereço', '⌨️ Digitar Endereço']:
        prompt = await event.respond(
            '📍 **Por favor, digite seu endereço atual:**\n'
            '__(Rua, Número, Cidade)__'
        )
        await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)
        return

    if user_type == 'motorista':
        await handle_driver_conversation(event, sender_id, state_str, text)
    elif user_type == 'passageiro':
        await handle_passenger_conversation(event, sender_id, state_str, text)

    await handle_common_conversation(event, sender_id, state_str, text)


async def handle_driver_conversation(event, sender_id, state, text):
    if state in ["wait_input_pix_key", "edit_pix"]:
        await process_pix_key(event, sender_id, text)
    elif state in ["wait_input_vehicle", "edit_vehicle"]:
        await process_vehicle_info(event, sender_id, text)
    elif state == "wait_input_plate":
        await process_vehicle_plate(event, sender_id, text)
    elif state == "wait_driver_location":
        await process_driver_location_text(event, sender_id, text)

    user_context = event.client.get_user_data(sender_id, "user")
    if user_context:
        await event.client.controller.edit_user(**user_context)


async def handle_passenger_conversation(event, sender_id, state, text):
    if state == "wait_match":
        await start_match(event, sender_id)
    elif state in ["wait_passenger_location", "wait_input_origin"]:
        await process_origin(event, sender_id, text)
    elif state == "wait_input_destination":
        await process_destination(event, sender_id, text)


async def handle_common_conversation(event, sender_id, state, text):
    action = getattr(event.message, "action", None)
    if state == "wait_code_activation":
        await process_code_activation(event.client, event, sender_id, text)
    elif state == "wait_two_steps_verification":
        await process_two_steps_verification(event.client, event, sender_id, text)
    elif state == "wait_get_contact":
        await process_get_contact(event.client, event, sender_id)
    elif isinstance(action, MessageActionGeoProximityReached):
        await handle_proximity_event(event)


async def process_pix_key(event, sender_id, pix_key):
    user_context = event.client.get_user_data(
        sender_id, "user",
        event.client.get_user_data(sender_id, "new_user", {})
    )
    user_context["pix_key"] = pix_key
    event.client.set_user_data(sender_id, "user", user_context)

    state = event.client.get_user_state(sender_id)
    state_str = state.value if hasattr(state, 'value') else str(state)

    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try:
            await event.client.delete_messages(sender_id, last_prompt_id)
        except:
            pass

    if state_str == "edit_pix":
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
        await event.client.controller.edit_user(**user_context)
        return await event.respond('✅ **Chave PIX atualizada com sucesso!**')

    event.client.set_user_state(sender_id, State.WAIT_INPUT_VEHICLE)
    prompt = await event.respond('🚗 **Veículo:** Por favor, insira o modelo e a cor do seu veículo:')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_vehicle_info(event, sender_id, type_vehicle):
    user_context = event.client.get_user_data(sender_id, "user", {})
    user_context["type_vehicle"] = type_vehicle
    event.client.set_user_data(sender_id, "user", user_context)

    state = event.client.get_user_state(sender_id)
    state_str = state.value if hasattr(state, 'value') else str(state)

    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try:
            await event.client.delete_messages(sender_id, last_prompt_id)
        except:
            pass

    if state_str == "edit_vehicle":
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
        await event.client.controller.edit_user(**user_context)
        return await event.respond('✅ **Informações do veículo atualizadas!**')

    event.client.set_user_state(sender_id, State.WAIT_INPUT_PLATE)
    prompt = await event.respond('🚘 **Placa:** Agora, informe a placa do seu veículo:')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_vehicle_plate(event, sender_id, plate):
    user_context = event.client.get_user_data(sender_id, "user", {})
    user_context["plate"] = plate
    event.client.set_user_data(sender_id, "user", user_context)

    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try:
            await event.client.delete_messages(sender_id, last_prompt_id)
        except:
            pass

    await event.respond(
        f'✨ **CONFIGURAÇÕES CONCLUÍDAS!** ✨\n\n'
        f'👉 Clique no botão abaixo para compartilhar sua localização e ficar **Online**.',
        buttons=[
            [Button.request_location("📡 Ficar Online (GPS)", resize=True)],
            [Button.text("⌨️ Digitar Endereço", resize=True)]
        ]
    )
    event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    await event.client.storage.delete(f"last_prompt:{sender_id}")


async def process_driver_location_text(event, sender_id, location_text):
    latitude, longitude = get_coordinates(location_text)
    if latitude is None:
        return await event.respond('❌ **Erro:** Não consegui localizar este endereço.')

    full_address = get_full_address(latitude, longitude)
    settings = await event.client.storage.get(f"settings:{sender_id}", {})
    settings["pending_confirm"] = {
        "address": full_address, "latitude": float(latitude), "longitude": float(longitude), "type": "driver_location"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)
    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)

    buttons = [[Button.inline("✅ Sim", "address_confirm_yes"), Button.inline("❌ Não", "address_confirm_no")]]
    await event.respond(f"📍 **LOCAL ENCONTRADO:**\n__{full_address}__\n\n**Confirma?**", buttons=buttons)


async def process_destination(event, sender_id, destination):
    latitude, longitude = get_coordinates(destination)
    if latitude is None:
        return await event.respond('❌ **Erro:** Destino não encontrado.')

    full_address = get_full_address(latitude, longitude)
    settings = await event.client.storage.get(f"settings:{sender_id}", {"address": {}})
    settings["pending_confirm"] = {
        "address": full_address, "latitude": float(latitude), "longitude": float(longitude), "type": "destination"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)
    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)

    buttons = [[Button.inline("✅ Sim", "address_confirm_yes"), Button.inline("❌ Não", "address_confirm_no")]]
    await event.respond(f"🏁 **DESTINO:**\n__{full_address}__\n\n**Confirma?**", buttons=buttons)


async def start_match(event, sender_id):
    await event.delete()
    event.client.set_user_state(sender_id, State.WAIT_INPUT_ORIGIN)
    prompt = await event.respond('👉 **Ponto de Partida:** Onde você está?')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_origin(event, sender_id, origin):
    latitude, longitude = get_coordinates(origin)
    if latitude is None:
        return await event.respond('❌ **Erro:** Local não encontrado.')

    full_address = get_full_address(latitude, longitude)
    settings = await event.client.storage.get(f"settings:{sender_id}", {"address": {}})
    settings["pending_confirm"] = {
        "address": full_address, "latitude": float(latitude), "longitude": float(longitude), "type": "origin"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)
    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)

    buttons = [[Button.inline("✅ Sim", "address_confirm_yes"), Button.inline("❌ Não", "address_confirm_no")]]
    await event.respond(f"📍 **ORIGEM:**\n__{full_address}__\n\n**Confirma?**", buttons=buttons)


async def handle_proximity_event(event):
    # await event.respond('🧭 Proximidade alcançada!')
    from_user_id, to_user_id, distance = (
        event.message.action.from_id,
        event.message.action.to_id,
        event.message.action.distance
    )
    await event.respond(
        f'🧭 O usuário {from_user_id} está a {distance} metros de {to_user_id}!'
    )
