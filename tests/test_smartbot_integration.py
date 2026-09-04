import pytest
from unittest.mock import AsyncMock, MagicMock
from smartbot.utils.handler import ClientHandler
from drivematch.app import Client
from drivematch.utils.state import State

@pytest.mark.asyncio
async def test_plugin_loading(app_client):
    """Verifica se o Client configurou corretamente o plugin loader do SmartBot."""
    # O Client do SmartBot carrega plugins no __init__
    # Verificamos se o dicionário de plugins está presente e correto
    assert "root" in app_client.plugins
    assert app_client.plugins["root"] == "plugins"
    assert "commands" in app_client.plugins["include"]

@pytest.mark.asyncio
async def test_redis_session_persistence(app_client):
    """Verifica se o RedisUserSession está sendo usado para armazenar estados."""
    sender_id = 999
    
    # Simular set_user_state (que deve chamar o mock_user_session configurado no conftest)
    app_client.set_user_state(sender_id, State.WAIT_MATCH)
    
    # Verificar se o mock_user_session foi chamado
    app_client.user_session.set_user_state.assert_called_with(sender_id, State.WAIT_MATCH, None)
    
    # Simular get_user_state
    app_client.user_session.get_user_state.return_value = State.WAIT_MATCH
    state = app_client.get_user_state(sender_id)
    
    assert state == State.WAIT_MATCH

@pytest.mark.asyncio
async def test_handler_registration(app_client):
    """
    Verifica se os handlers nos plugins estão acessíveis.
    """
    import plugins.commands as commands_plugin
    import inspect
    
    # Verificar se existem funções marcadas como handler no módulo de comandos
    handlers = [obj for name, obj in inspect.getmembers(commands_plugin) 
               if getattr(obj, "is_handler", False)]
    
    assert len(handlers) > 0
    
    # Verificar se o handler de /start está presente
    assert any(h.__name__ == 'handle_start_command' for h in handlers)


@pytest.mark.asyncio
async def test_duplicate_handler_prevention(app_client):
    """Verifica se a tentativa de registrar o mesmo handler múltiplas vezes é bloqueada."""
    dummy_handler = lambda e: None
    
    # Registra a primeira vez
    app_client.add_event_handler(dummy_handler)
    initial_count = len(app_client.list_event_handlers())
    
    # Tenta registrar o mesmo handler novamente
    app_client.add_event_handler(dummy_handler)
    new_count = len(app_client.list_event_handlers())
    
    # A contagem de handlers não deve mudar
    assert new_count == initial_count
