from telethon import events
from drivematch.utils.decorators import handler
from drivematch.utils.location import get_full_address


@handler
def register_locations_handlers(bot, instance):
    @bot.on(events.NewMessage(func=lambda e: e.geo))
    async def handle_location(event):
        sender_id = event.sender_id

        if event.message.geo:
            latitude, longitude = event.message.geo.lat, event.message.geo.long
            full_address = get_full_address(latitude, longitude)

            update_user_runtime_settings(instance, sender_id, latitude, longitude, full_address)

            user_type = instance.users_dict[sender_id].get('type')
            state = instance.conversation_state.get(sender_id)
            user = instance.users_dict[sender_id]

            if user_type == 'motorista' and state == instance.state.WAIT_DRIVER_LOCATION:
                await event.reply(
                    f"✅ Você aceitou o pedido de corrida.\n"
                    f"Seu local atual é {full_address}\n\n"
                    f"👉 Clique em /road quando seu passageiro embarcar.\n"
                    f"__**Para cancelar a viagem \n"
                    f"digite o comando**__ /cancel\n"
                )
                travel = instance.controller.get_travel(user['id'])
                passenger_id = travel['passenger']["user_id"]
                return await handle_confirm_location(instance, sender_id, passenger_id)
            elif user_type == 'passageiro' and state == instance.state.WAIT_PASSENGER_LOCATION:
                await event.reply(
                    f'🧭 Sua localização atual é: \n{full_address}'
                )
                travel = instance.controller.get_travel(user['id'])
                driver_id = travel['driver']["user_id"]
                return await handle_confirm_location(instance, sender_id, driver_id)

            instance.conversation_state[sender_id] = instance.state.WAIT_INPUT_DESTINATION
            return await event.respond('👉 Insira o local de destino.')

        return await event.respond('🧨 Não consegui obter sua localização.')


def update_user_runtime_settings(instance, sender_id, latitude, longitude, full_address):
    if sender_id not in instance.runtime_settings:
        instance.runtime_settings[sender_id] = {"address": {}}
    instance.runtime_settings[sender_id]["address"]["origin"] = full_address
    instance.runtime_settings[sender_id]["address"]["latitude"] = latitude
    instance.runtime_settings[sender_id]["address"]["longitude"] = longitude


async def handle_confirm_location(instance, sender_id, chat_id):
    await instance.send_live_location(
        sender_id,
        chat_id
    )
