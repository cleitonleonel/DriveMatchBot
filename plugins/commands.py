from telethon import events, Button
from smartbot.utils.handler import ClientHandler
from drivematch.utils.state import State
from decimal import Decimal

client = ClientHandler()


@client.on(events.NewMessage(pattern='/start'))
async def handle_start_command(event):
    sender = await event.get_sender()
    sender_id = sender.id

    # Limpar qualquer conversa anterior
    event.client.reset_user_session(sender_id)

    # Verificar se o usuário existe
    user = await event.client.controller.check_user_exists(sender_id)

    if not user:
        # Novo usuário
        new_user_data = {
            "user_id": sender.id,
            "username": sender.username or "",
            "first_name": sender.first_name or "",
            "last_name": sender.last_name or "",
            "is_active": False
        }
        # Armazenar contexto temporário (usando user_data do SmartBot)
        event.client.set_user_data(sender_id, "new_user", new_user_data)

        buttons = [[
            Button.inline('🚗 Dirigir', 'drive'),
            Button.inline('👋 Viajar', 'travel')
        ]]
        return await event.respond(
            f'Olá {sender.first_name or sender_id}!\n'
            f'✨ **Bem-vindo ao DriveMatch!** ✨\n'
            f'💬 Que bom te ver por aqui!\n'
            f'Como você deseja utilizar o app hoje?\n'
            f'👇 Selecione uma das opções abaixo:',
            buttons=buttons
        )

    # Usuário existente
    event.client.set_user_data(sender_id, "user", user)
    travel = await event.client.controller.get_travel(user['id'])
    user_type = user.get('type')

    if travel and travel.get('status') in ['accepted', 'in_progress', 'requesting']:
        msg = "🔃 **Viagem em andamento!**\n"
        msg += (
            "👉 Use /road para iniciar ou /complete para finalizar."
            if user_type == 'motorista' else "👉 Aguarde o motorista."
        )
        return await event.respond(msg)

    if user_type == 'passageiro':
        await event.respond(
            "✨ **Bem-vindo!**\n"
            "🎈 **Onde vamos hoje?**",
            buttons=[
                [Button.request_location("🧭 Minha Localização", resize=True, single_use=True)],
                [Button.text("👋 Digitar Endereço", resize=True)]
            ]
        )
        event.client.set_user_state(sender_id, State.WAIT_PASSENGER_LOCATION)
    elif user_type == 'motorista':
        await event.respond(
            "🔧 **Painel do Motorista**\nStatus: **Online** ✅\n\n"
            "👉 Clique abaixo para atualizar sua posição e receber chamadas.",
            buttons=[
                [Button.request_location("📡 Ficar Online (GPS)", resize=True)],
                [Button.text("⌨️ Digitar Endereço", resize=True)]
            ]
        )
        event.client.set_user_state(sender_id, State.WAIT_DRIVER_LOCATION)
    else:
        # Se não tiver tipo (erro raro), volta pro início
        buttons = [[
            Button.inline('🚗 Dirigir', 'drive'),
            Button.inline('👋 Viajar', 'travel')
        ]]
        await event.respond("Como você deseja utilizar o app hoje?", buttons=buttons)


@client.on(events.NewMessage(pattern='/wallet'))
async def handle_wallet(event):
    sender_id = event.sender_id
    user = await event.client.controller.check_user_exists(sender_id)
    if not user or user.get('type') != 'motorista':
        return

    balance = user.get('balance', 0.0)
    buttons = []
    if balance >= 20.0:
        buttons.append(
            [Button.inline("💸 Solicitar Saque (PIX)", "request_withdraw")]
        )

    await event.respond(
        f"💰 **Sua Carteira DriveMatch** 💰\n\n"
        f"💵 Saldo disponível para saque: **R$ {balance:.2f}**\n"
        f"🏁 Total de corridas: **{user.get('qtd_travels', 0)}**\n\n"
        f"Os repasses são feitos manualmente após sua solicitação.",
        buttons=buttons if buttons else None
    )


@client.on(events.NewMessage(pattern='/road'))
async def handle_start_travel(event):
    sender_id = event.sender_id
    user = await event.client.controller.check_user_exists(sender_id)
    if not user or user.get('type') != 'motorista':
        return

    travel = await event.client.controller.get_travel(user['id'])
    if not travel or travel.get('status') != 'accepted':
        return await event.respond("🧨 Nenhuma viagem aceita.")

    await event.client.controller.start_travel(travel['id'], user['id'])
    await event.respond("🚀 **Viagem Iniciada!**\nUse /complete ao chegar.")
    await event.client.send_message(
        travel['passenger']["user_id"],
        f"✅ **Seu motorista iniciou o trajeto!**\n"
        f"💆‍♂️ Fique a vontade e aproveite a viagem!"
    )


@client.on(events.NewMessage(pattern='/complete'))
async def handle_complete_travel(event):
    sender_id = event.sender_id
    user = await event.client.controller.check_user_exists(sender_id)

    if not user or user.get('type') != 'motorista':
        return

    travel = await event.client.controller.get_travel(user['id'])
    if not travel or travel.get('status') != 'in_progress':
        return await event.respond("🧨 Viagem não está em andamento.")

    from drivematch.utils.rates import calculate_fare, calculate_percent
    from drivematch.utils.payment import generate_pix_payload

    await event.client.controller.complete_travel(travel['id'], user['id'])
    sys_settings = await event.client.controller.get_system_settings()

    split_percent = user.get('custom_fee_percentage')
    if split_percent is None:
        split_percent = sys_settings.get('default_platform_percentage', 20.0)

    platform_percentage_decimal = Decimal(str(split_percent / 100))
    driver_percentage_show = 100 - split_percent

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

    await event.client.controller.set_travel_financials(
        travel['id'],
        float(total_fare),
        float(driver_share),
        float(platform_fee)
    )
    pix_payload = generate_pix_payload(total_fare, travel['id'], user['id'])

    await event.respond(
        f"🏁 **Viagem concluída!**\n\n"
        f"💰 Valor Total: **R$ {total_fare:.2f}**\n"
        f"💼 Sua parte ({driver_percentage_show:.0f}%): **R$ {driver_share:.2f}**\n\n"
        f"Aguardando pagamento do passageiro..."
    )

    checkout_buttons = [
        [Button.inline("✅ Já paguei", f"confirm_pay_{travel['id']}")],
        [Button.inline("⭐ Avaliar Motorista", f"rate_ask_{travel['id']}")]
    ]

    await event.client.send_message(
        travel['passenger']["user_id"],
        f"🏁 **Chegamos ao destino!**\n\n"
        "🫶 Obrigado por viajar conosco!\n"
        f"💵 Valor Total: **R$ {total_fare:.2f}**\n\n"
        f"💳 **Pagamento via PIX:**\n"
        f"`{pix_payload}`\n\n"
        f"Copie o código acima e pague no app do seu banco. "
        f"Em seguida, clique em confirmar abaixo.",
        buttons=checkout_buttons
    )


@client.on(events.NewMessage(pattern='/cancel'))
async def handle_cancel_travel(event):
    sender_id = event.sender_id
    user = await event.client.controller.check_user_exists(sender_id)
    if not user:
        return

    user_type = user.get('type')

    travel = await event.client.controller.get_travel(user['id'])
    if not travel or travel.get('status') not in ['requesting', 'accepted']:
        return await event.respond("🧨 Não há viagem para cancelar.")

    await event.client.controller.cancel_travel(travel['id'], user['id'])
    # user[sender_id]["num_ratings"] -= 1

    if user_type == 'motorista':
        passenger = travel.get('passenger', {})
        if passenger:
            await event.client.send_message(
                passenger.get('user_id'), "🧨 Viagem cancelada pelo motorista.\n"
            )

    elif user_type == 'passageiro':
        driver = travel.get('driver', {})
        if driver:
            await event.client.send_message(
                driver.get('user_id'), "🧨 Viagem cancelada pelo passageiro.\n"
            )

    await event.respond("❎ **Cancelamento confirmado.**")


@client.on(events.NewMessage(pattern='/unregister'))
async def handle_unregister_account(event):
    sender_id = event.sender_id
    if await event.client.controller.delete_user(sender_id):
        event.client.reset_user_session(sender_id)
        return await event.respond("👋 **Conta removida.**")
    await event.respond("❌ Erro ao remover.")
