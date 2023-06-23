import redis
import json

class RedisStore:
    def __init__(self, host='localhost', port=6379):
        self.db = redis.Redis(host=host, port=port, decode_responses=True)

    def save(self, key, value):
        if not value:
            # Handle the case of an empty dictionary separately
            self.db.delete(key)
        else:
            self.db.hmset(key, {k: json.dumps(v) for k, v in value.items()})

    def load(self, key):
        data = self.db.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()}
