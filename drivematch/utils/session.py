import json
import redis
from datetime import datetime, timedelta
from smartbot.bot import UserSession

from smartbot.config import config as bot_config

# Criamos uma conexão global para não abrir pool por usuário
redis_url = bot_config.get('DATABASE', {}).get('REDIS_URL', "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)

class RedisUserSession(UserSession):
    """
    Uma implementação de UserSession que persiste os estados e dados no Redis.
    Segue fielmente a assinatura e comportamento do SmartBot UserSession.
    """
    def __init__(self, user_id: int, state_class):
        self.user_id = user_id
        self.state_class = state_class
        self._prefix = "smartbot:session:"
        self.redis = redis_client
        self.timeout_duration = timedelta(minutes=30)
    
    @property
    def key(self):
        return f"{self._prefix}{self.user_id}"

    def _get_session_data(self):
        data = self.redis.get(self.key)
        if data:
            return json.loads(data)
        return {
            "state": self.state_class.IDLE.value if hasattr(self.state_class.IDLE, 'value') else "idle", 
            "context": {}, 
            "data": {},
            "last_activity": datetime.now().isoformat()
        }

    def _save_session_data(self, session_data):
        session_data["last_activity"] = datetime.now().isoformat()
        self.redis.set(self.key, json.dumps(session_data))

    def set_state(self, state, context=None):
        session_data = self._get_session_data()
        session_data["state"] = state.value if hasattr(state, 'value') else state
        if context:
            session_data["context"].update(context)
        self._save_session_data(session_data)

    def get_state(self):
        session_data = self._get_session_data()
        state_val = session_data.get("state")
        # Tentamos devolver o Enum, senão devolve o raw value
        for s in self.state_class:
            if (hasattr(s, 'value') and s.value == state_val) or (s == state_val):
                return s
        return state_val

    def set_context(self, key: str, value):
        session_data = self._get_session_data()
        session_data["context"][key] = value
        self._save_session_data(session_data)

    def get_context(self, key: str, default=None):
        session_data = self._get_session_data()
        return session_data.get("context", {}).get(key, default)

    def clear_context(self):
        session_data = self._get_session_data()
        session_data["context"] = {}
        self._save_session_data(session_data)

    def clear_user_data(self):
        session_data = self._get_session_data()
        session_data["data"] = {}
        self._save_session_data(session_data)

    def set_data(self, key: str, value):
        session_data = self._get_session_data()
        session_data["data"][key] = value
        self._save_session_data(session_data)

    def get_data(self, key: str, default=None):
        session_data = self._get_session_data()
        return session_data.get("data", {}).get(key, default)

    def is_expired(self) -> bool:
        session_data = self._get_session_data()
        last_str = session_data.get("last_activity")
        if not last_str: return False
        try:
            last_activity = datetime.fromisoformat(last_str)
            return datetime.now() - last_activity > self.timeout_duration
        except:
            return False

    def reset_to_idle(self):
        session_data = self._get_session_data()
        session_data["state"] = self.state_class.IDLE.value if hasattr(self.state_class.IDLE, 'value') else "idle"
        session_data["context"] = {}
        session_data["data"] = {}
        self._save_session_data(session_data)

    def delete_user_session(self, user_id):
        self.redis.delete(self._get_key(user_id))
