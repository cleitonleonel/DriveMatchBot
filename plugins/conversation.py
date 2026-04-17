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
    user_context = event.client.get_user_data(sender_id, "user")
    if not user_context:
        user_context = await event.client.controller.check_user_exists(sender_id)
        if user_context:
            event.client.set_user_data(sender_id, "user", user_context)

    if not user_context and state != State.START:
        # Tenta recuperar dados do "new_user" se estiver no fluxo de cadastro
        user_context = event.client.get_user_data(sender_id, "new_user")

    if not user_context:
        return

    user_type = user_context.get('type')

    # Gatilhos universais
    if text in ['👋 Inserir Local', '👋 Viajar', '👋 Iniciar Viagem']:
        event.client.set_user_state(sender_id, State.WAIT_MATCH)
        state = State.WAIT_MATCH

    if text in ['👋 Digitar Endereço', '⌨️ Digitar Endereço']:
        prompt = await event.respond(
            '📍 **Por favor, digite seu endereço atual:**\n'
            '__(Rua, Número, Cidade)__'
        )
        # Armazena o ID do prompt para deletar depois
        await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)
        return

    if user_type == 'motorista':
        await handle_driver_conversation(event, sender_id, state, text)
    elif user_type == 'passageiro':
        await handle_passenger_conversation(event, sender_id, state, text)

    await handle_common_conversation(event, sender_id, state, text)


async def handle_driver_conversation(event, sender_id, state, text):
    if state == State.WAIT_INPUT_PIX_KEY:
        await process_pix_key(event, sender_id, text)
    elif state == State.WAIT_INPUT_VEHICLE:
        await process_vehicle_info(event, sender_id, text)
    elif state == State.WAIT_INPUT_PLATE:
        await process_vehicle_plate(event, sender_id, text)
    elif state == State.WAIT_DRIVER_LOCATION:
        await process_driver_location_text(event, sender_id, text)

    user_context = event.client.get_user_data(sender_id, "user")
    if user_context:
        await event.client.controller.edit_user(**user_context)


async def handle_passenger_conversation(event, sender_id, state, text):
    if state == State.WAIT_MATCH:
        await start_match(event, sender_id)
    elif state in [State.WAIT_PASSENGER_LOCATION, State.WAIT_INPUT_ORIGIN]:
        await process_origin(event, sender_id, text)
    elif state == State.WAIT_INPUT_DESTINATION:
        await process_destination(event, sender_id, text)


async def handle_common_conversation(event, sender_id, state, text):
    if state == State.WAIT_CODE_ACTIVATION:
        await process_code_activation(event.client, event, sender_id, text)
    elif state == State.WAIT_TWO_STEPS_VERIFICATION:
        await process_two_steps_verification(event.client, event, sender_id, text)
    elif state == State.WAIT_GET_CONTACT:
        await process_get_contact(event.client, event, sender_id)
    elif event.message.action and isinstance(
            event.message.action, MessageActionGeoProximityReached
    ):
        await handle_proximity_event(event)


async def process_pix_key(event, sender_id, pix_key):
    user_context = event.client.get_user_data(
        sender_id,
        "user",
        event.client.get_user_data(sender_id, "new_user", {})
    )
    user_context["pix_key"] = pix_key
    event.client.set_user_data(sender_id, "user", user_context)
    event.client.set_user_state(sender_id, State.WAIT_INPUT_VEHICLE)
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    prompt = await event.respond('🚗 **Veículo:** Por favor, insira o modelo e a cor do seu veículo:')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_vehicle_info(event, sender_id, type_vehicle):
    user_context = event.client.get_user_data(sender_id, "user", {})
    user_context["type_vehicle"] = type_vehicle
    event.client.set_user_data(sender_id, "user", user_context)
    event.client.set_user_state(sender_id, State.WAIT_INPUT_PLATE)
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    prompt = await event.respond('🚘 **Placa:** Agora, informe a placa do seu veículo:')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_vehicle_plate(event, sender_id, plate):
    user_context = event.client.get_user_data(sender_id, "user", {})
    user_context["plate"] = plate
    event.client.set_user_data(sender_id, "user", user_context)
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    await event.respond(
        f'✨ **CONFIGURAÇÕES CONCLUÍDAS!** ✨\n\n'
        f'👉 Clique no botão abaixo para compartilhar sua localização, '
        f'ficar **Online** e começar a receber chamadas.',
        buttons=[
            [Button.request_location("📡 Ficar Online (GPS)", resize=True)],
            [Button.text("⌨️ Digitar Endereço", resize=True)]
        ]
    )
    event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    await event.client.storage.delete(f"last_prompt:{sender_id}")


async def process_driver_location_text(event, sender_id, location_text):
    latitude, longitude = get_coordinates(location_text)
    if latitude is None or longitude is None:
        return await event.respond('❌ **Erro:** Não consegui localizar este endereço. Tente ser mais específico.')

    full_address = get_full_address(latitude, longitude)
    
    # Em vez de salvar direto, pedimos confirmação
    settings = await event.client.storage.get(f"settings:{sender_id}", {})
    if not isinstance(settings, dict): settings = {}
    
    settings["pending_confirm"] = {
        "address": full_address,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "type": "driver_location"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)
    
    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)
    
    buttons = [
        [Button.inline("✅ Sim, está correto", "address_confirm_yes")],
        [Button.inline("❌ Não, digitar novamente", "address_confirm_no")]
    ]
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    await event.respond(
        f"📍 **ENDEREÇO ENCONTRADO:**\n\n"
        f"__({full_address})__\n\n"
        f"**Confirma este local como sua posição atual?**",
        buttons=buttons
    )
    return


async def process_destination(event, sender_id, destination):
    latitude, longitude = get_coordinates(destination)
    if latitude is None or longitude is None:
        return await event.respond('❌ **Erro:** Não consegui localizar este destino. Verifique o nome da rua e cidade.')

    # Em vez de salvar direto, pedimos confirmação
    settings = await event.client.storage.get(f"settings:{sender_id}", {"address": {}})
    full_address = get_full_address(latitude, longitude) # Opcional: obter nome formatado

    settings["pending_confirm"] = {
        "address": destination, # O texto digitado ou formatado
        "latitude": float(latitude),
        "longitude": float(longitude),
        "type": "destination"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)
    
    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)
    
    buttons = [
        [Button.inline("✅ Sim, está correto", "address_confirm_yes")],
        [Button.inline("❌ Não, digitar novamente", "address_confirm_no")]
    ]
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    await event.respond(
        f"🏁 **DESTINO ENCONTRADO:**\n\n"
        f"__{full_address}__\n\n"
        f"**Confirma este destino para a sua viagem?**",
        buttons=buttons
    )
    return


async def start_match(event, sender_id):
    await event.delete()
    event.client.set_user_state(sender_id, State.WAIT_INPUT_ORIGIN)
    prompt = await event.respond('👉 **Ponto de Partida:** Por favor, digite o local onde você está.')
    await event.client.storage.set(f"last_prompt:{sender_id}", prompt.id)


async def process_origin(event, sender_id, origin):
    latitude, longitude = get_coordinates(origin)
    if latitude is None or longitude is None:
        return await event.respond('❌ **Erro:** Não consegui localizar este endereço de origem.')

    # Em vez de salvar direto, pedimos confirmação
    settings = await event.client.storage.get(f"settings:{sender_id}", {"address": {}})
    full_address = get_full_address(latitude, longitude)

    settings["pending_confirm"] = {
        "address": full_address,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "type": "origin"
    }
    await event.client.storage.set(f"settings:{sender_id}", settings)

    event.client.set_user_state(sender_id, State.WAIT_CONFIRM_ADDRESS)
    
    buttons = [
        [Button.inline("✅ Sim, está correto", "address_confirm_yes")],
        [Button.inline("❌ Não, digitar novamente", "address_confirm_no")]
    ]
    
    # Deletar prompt anterior
    last_prompt_id = await event.client.storage.get(f"last_prompt:{sender_id}")
    if last_prompt_id:
        try: await event.client.delete_messages(sender_id, last_prompt_id)
        except: pass

    await event.respond(
        f"📍 **PONTO DE PARTIDA ENCONTRADO:**\n\n"
        f"__{full_address}_\n\n"
        f"**Confirma este local como origem da viagem?**",
        buttons=buttons
    )
    return


async def handle_proximity_event(event):
    from_user_id, to_user_id, distance = (
        event.message.action.from_id,
        event.message.action.to_id,
        event.message.action.distance
    )
    await event.respond(
        f'🧭 O usuário {from_user_id} está a {distance} metros de {to_user_id}!'
    )
