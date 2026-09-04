import pytest
import inspect
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import plugins.commands as commands_plugin
import plugins.callback as callback_plugin
import plugins.location as location_plugin

def get_handler(module, func_name):
    """Auxiliar para encontrar handlers marcados pelo SmartBot."""
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and getattr(obj, "is_handler", False) is True:
            if obj.__name__ == func_name:
                return obj
    return None

@pytest.mark.asyncio
async def test_passenger_start_flow(app_client, message_event_factory, callback_event_factory):
    """Testa o fluxo inicial do passageiro: /start -> Selecionar Viajar."""
    
    # Simular o comando /start
    start_event = message_event_factory(sender_id=111, text="/start")
    
    # Localizar o handler de /start
    start_handler = get_handler(commands_plugin, 'handle_start_command')
    assert start_handler is not None
    
    # Executar o handler de /start
    app_client.controller.check_user_exists.return_value = None # Usuário novo
    
    await start_handler(start_event)
    
    # Verificar se o bot respondeu
    assert app_client.controller.check_user_exists.called
    start_event.respond.assert_called()
    args, kwargs = start_event.respond.call_args
    assert "BEM-VINDO AO DRIVEMATCH" in args[0]
    
    # 2. Simular o clique no botão 'Viajar' (callback 'travel')
    travel_event = callback_event_factory(sender_id=111, data="travel")
    
    # Mock do retorno do check_user
    user_data = {'id': 1, 'user_id': 111, 'type': 'passageiro', 'is_active': False}
    # O primeiro retorno é usado pela linha 18 do callback.py (user = await check_user_exists)
    app_client.controller.check_user_exists.side_effect = [user_data, user_data, user_data, user_data, user_data]
    
    # Localizar o handler de CallbackQuery
    callback_handler = get_handler(callback_plugin, 'handle_callback')
    assert callback_handler is not None
    
    # Executar o handler de callback
    await callback_handler(travel_event)
    
    # Verificar se o usuário foi criado como passageiro e se pediu localização
    app_client.controller.create_user.assert_called()
    travel_event.reply.assert_called()
    args, _ = travel_event.reply.call_args
    assert "VAMOS VIAJAR!" in args[0]

@pytest.mark.asyncio
async def test_passenger_location_flow(app_client, location_event_factory):
    """Testa o envio de localização pelo passageiro."""
    
    # Simular estado inicial usando a nova lógica de armazenamento do mock
    sender_id = 111
    user_data = {'id': 1, 'user_id': sender_id, 'type': 'passageiro'}
    app_client.set_user_data(sender_id, "user", user_data)
    app_client.set_user_state(sender_id, app_client.state.WAIT_PASSENGER_LOCATION)
    
    # Patch do get_full_address
    with patch("plugins.location.get_full_address", return_value="Rua Teste, 123"):
        # Localizar handler
        location_handler = get_handler(location_plugin, 'handle_location')
        assert location_handler is not None
        
        # Mock do get_travel
        app_client.controller.get_travel.return_value = None
        
        # Simular evento de localização
        loc_event = location_event_factory(sender_id=sender_id, lat=-20.0, long=-40.0)
        await location_handler(loc_event)
        
        # Verificar se mudou para estado de esperar destino
        # Como o mock persiste, podemos verificar se o estado final no "storage" é o esperado
        assert app_client.get_user_state(sender_id) == app_client.state.WAIT_INPUT_DESTINATION
        loc_event.respond.assert_called_with('👉 **Para onde vamos?** Por favor, digite seu destino.')

@pytest.mark.asyncio
async def test_driver_decline_trip(app_client, callback_event_factory):
    """Testa se o motorista consegue recusar uma proposta de viagem."""
    
    sender_id = 222
    user_data = {'id': 2, 'user_id': sender_id, 'type': 'motorista', 'is_active': True}
    app_client.set_user_data(sender_id, "user", user_data)
    
    decline_event = callback_event_factory(sender_id=sender_id, data="decline_trip_1_111")
    
    # Localizar handler
    callback_handler = get_handler(callback_plugin, 'handle_callback')
    
    await callback_handler(decline_event)
    
    # No handler, data == 'decline_trip' deve chamar event.delete()
    decline_event.delete.assert_called_once()

@pytest.mark.asyncio
async def test_driver_request_withdrawal_integration(app_client, callback_event_factory):
    """Testa a integração do botão de saque com o UserController."""
    
    sender_id = 222
    user_data = {'id': 2, 'user_id': sender_id, 'type': 'motorista', 'is_active': True, 'balance': 50.0}
    app_client.set_user_data(sender_id, "user", user_data)
    app_client.controller.check_user_exists.return_value = user_data
    
    # Mock do retorno do controller
    app_client.controller.request_payout.return_value = (True, "Sucesso!")
    
    withdraw_event = callback_event_factory(sender_id=sender_id, data="request_withdraw")
    callback_handler = get_handler(callback_plugin, 'handle_callback')
    
    await callback_handler(withdraw_event)
    
    # Verificar interações
    app_client.controller.request_payout.assert_called_with(sender_id)
    # Procurar pela chamada com 'Sucesso!'
    withdraw_event.answer.assert_any_call("Sucesso!", alert=True)

@pytest.mark.asyncio
async def test_driver_wallet_markup_fix(app_client, message_event_factory):
    """Garante que /wallet não quebra quando o motorista tem saldo < 20 (markup None)."""
    
    sender_id = 333
    # Saldo baixo
    user_data = {'id': 3, 'user_id': sender_id, 'type': 'motorista', 'balance': 0.0}
    app_client.controller.check_user_exists.return_value = user_data
    # get_user_travels já é um AsyncMock pelo conftest
    app_client.controller.get_user_travels.return_value = []
    
    wallet_event = message_event_factory(sender_id=sender_id, text="/wallet")
    
    # Localizar handler
    wallet_handler = get_handler(commands_plugin, 'handle_wallet')
    
    await wallet_handler(wallet_event)
    
    # Verificar se respondeu sem botões (buttons=None)
    wallet_event.respond.assert_called()
    _, kwargs = wallet_event.respond.call_args
    assert kwargs.get('buttons') is None

@pytest.mark.asyncio
async def test_admin_back_button_fix(app_client, callback_event_factory):
    """Garante que o botão voltar do admin não causa AttributeError e recarrega o menu."""
    import plugins.admin as admin_plugin
    
    sender_id = 1111
    # Patch ADMIN_IDS no módulo do plugin
    with patch.object(admin_plugin, 'ADMIN_IDS', [sender_id]):
        user_data = {'id': 9, 'user_id': sender_id, 'type': 'admin', 'is_admin': True}
        app_client.set_user_data(sender_id, "user", user_data)
        app_client.controller.check_user_exists.return_value = user_data
        
        # Mocks para o controller
        app_client.controller.get_admin_stats.return_value = {
            'users_count': 1, 'drivers_count': 1, 'travels_count': 1,
            'revenue_total': 0, 'revenue_platform': 0, 'revenue_drivers': 0
        }
        app_client.controller.get_system_settings.return_value = {
            'base_fare': 0, 'price_per_km': 0, 'price_per_min': 0, 'service_fee': 0, 'default_platform_percentage': 20
        }
        
        back_event = callback_event_factory(sender_id=sender_id, data=b"admin_back")
        callback_handler = get_handler(admin_plugin, 'admin_callbacks')
        
        await callback_handler(back_event)
        
        assert back_event.respond.called

@pytest.mark.asyncio
async def test_driver_manual_location_flow(app_client, message_event_factory, callback_event_factory):
    """Testa se o motorista consegue ficar online digitando o endereço."""
    import plugins.conversation as conv_plugin
    from drivematch.utils.state import State
    
    sender_id = 444
    app_client.set_user_state(sender_id, app_client.state.WAIT_DRIVER_LOCATION)
    user_data = {'id': 4, 'user_id': sender_id, 'type': 'motorista', 'balance': 0.0}
    app_client.set_user_data(sender_id, "user", user_data)
    app_client.controller.check_user_exists.return_value = user_data
    app_client.controller.get_travel.return_value = None
    
    with patch.object(conv_plugin, "get_coordinates") as mock_coords, \
         patch.object(conv_plugin, "get_full_address") as mock_full:
        
        mock_coords.return_value = ("-23.55", "-46.63")
        mock_full.return_value = "Av. Paulista, 1000, SP"
        
        # 1. Motorista digita o endereço
        location_event = message_event_factory(sender_id=sender_id, text="Av. Paulista, 1000")
        conv_handler = get_handler(conv_plugin, 'handle_conversation')
        
        await conv_handler(location_event)
        
        # Deve estar esperando confirmação agora
        assert app_client.get_user_state(sender_id) == State.WAIT_CONFIRM_ADDRESS
        location_event.respond.assert_called()
        assert "Confirma?" in location_event.respond.call_args[0][0]

    # 2. Simular o clique no botão de confirmação "Sim"
    confirm_event = callback_event_factory(sender_id=sender_id, data="address_confirm_yes")
    callback_handler = get_handler(callback_plugin, 'handle_callback')
    
    await callback_handler(confirm_event)
    
    # Agora sim deve ter chamado o update_user_location no controller
    app_client.controller.update_user_location.assert_called_with(sender_id, -23.55, -46.63)
    confirm_event.delete.assert_called()
    assert "VOCÊ ESTÁ ONLINE!" in confirm_event.respond.call_args[0][0]

@pytest.mark.asyncio
async def test_driver_manual_location_button_prompt(app_client, message_event_factory):
    """Testa se clicar no botão de digitar endereço gera o prompt correto."""
    import plugins.conversation as conv_plugin
    
    sender_id = 555
    user_data = {'id': 5, 'user_id': sender_id, 'type': 'motorista'}
    app_client.set_user_data(sender_id, "user", user_data)
    
    button_event = message_event_factory(sender_id=sender_id, text="⌨️ Digitar Endereço")
    conv_handler = get_handler(conv_plugin, 'handle_conversation')
    
    await conv_handler(button_event)
    button_event.respond.assert_called()
    assert "Por favor, digite seu endereço atual" in button_event.respond.call_args[0][0]


@pytest.mark.asyncio
async def test_edit_pix_flow_autonomy(app_client, message_event_factory):
    """Testa se a edição de chave PIX é autônoma e não avança para solicitação de veículo."""
    import plugins.conversation as conv_plugin
    from drivematch.utils.state import State
    
    sender_id = 666
    app_client.set_user_state(sender_id, State.EDIT_PIX)
    user_data = {'id': 6, 'user_id': sender_id, 'type': 'motorista', 'pix_key': 'old_pix'}
    app_client.set_user_data(sender_id, "user", user_data)
    app_client.controller.check_user_exists.return_value = user_data
    
    event = message_event_factory(sender_id=sender_id, text="nova_chave_pix_123")
    conv_handler = get_handler(conv_plugin, 'handle_conversation')
    
    await conv_handler(event)
    
    # Deve atualizar o usuário com a nova chave e encerrar a edição
    app_client.controller.edit_user.assert_called()
    assert app_client.get_user_state(sender_id) == State.WAIT_DRIVER_LOCATION
    event.respond.assert_called_with('✅ **Chave PIX atualizada com sucesso!**')


@pytest.mark.asyncio
async def test_edit_vehicle_flow_autonomy(app_client, message_event_factory):
    """Testa se a edição do veículo é autônoma e não avança para solicitação de placa."""
    import plugins.conversation as conv_plugin
    from drivematch.utils.state import State
    
    sender_id = 777
    app_client.set_user_state(sender_id, State.EDIT_VEHICLE)
    user_data = {'id': 7, 'user_id': sender_id, 'type': 'motorista', 'type_vehicle': 'Carro Antigo'}
    app_client.set_user_data(sender_id, "user", user_data)
    app_client.controller.check_user_exists.return_value = user_data
    
    event = message_event_factory(sender_id=sender_id, text="Novo Modelo Azul")
    conv_handler = get_handler(conv_plugin, 'handle_conversation')
    
    await conv_handler(event)
    
    # Deve atualizar o veículo e encerrar a edição
    app_client.controller.edit_user.assert_called()
    assert app_client.get_user_state(sender_id) == State.WAIT_DRIVER_LOCATION
    event.respond.assert_called_with('✅ **Informações do veículo atualizadas!**')
