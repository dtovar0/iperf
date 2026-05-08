import redis
import os
from flask import current_app

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self.connect()
        return self._client

    def connect(self):
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True # Para obtener strings en lugar de bytes
            )
            # Test connection
            self._client.ping()
        except Exception as e:
            print(f" [!] Redis Connection Error: {e}")
            self._client = None

    def set(self, key, value, ex=None):
        if self.client:
            return self.client.set(key, value, ex=ex)
        return False

    def get(self, key):
        if self.client:
            return self.client.get(key)
        return None

    def delete(self, key):
        if self.client:
            return self.client.delete(key)
        return False

# Instancia global
registry = RedisClient()
