import json
import redis.asyncio as redis
import logging
import os


class RedisStorage:
    def __init__(self, url=None, host='localhost', port=6379, db=0, password=None):
        self.url = url or os.getenv('REDIS_URL')
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.redis = None

    async def connect(self):
        if not self.redis:
            if self.url:
                self.redis = redis.from_url(
                    self.url,
                    decode_responses=True
                )
            else:
                self.redis = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True
                )
            try:
                await self.redis.ping()
                logging.info(f"Conectado ao Redis em {self.url or f'{self.host}:{self.port}'}")
            except Exception as e:
                logging.error(f"Falha ao conectar ao Redis: {e}")
                raise

    async def get(self, key, default=None):
        if not self.redis:
            await self.connect()
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return default

    async def set(self, key, value, ex=None):
        if not self.redis:
            await self.connect()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.set(key, value, ex=ex)

    async def delete(self, key):
        if not self.redis:
            await self.connect()
        await self.redis.delete(key)

    async def hset(self, name, key, value):
        if not self.redis:
            await self.connect()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.hset(name, key, value)

    async def hget(self, name, key, default=None):
        if not self.redis:
            await self.connect()
        data = await self.redis.hget(name, key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return default

    async def hdel(self, name, key):
        if not self.redis:
            await self.connect()
        await self.redis.hdel(name, key)

    async def hgetall(self, name):
        if not self.redis:
            await self.connect()
        data = await self.redis.hgetall(name)
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v
        return result
