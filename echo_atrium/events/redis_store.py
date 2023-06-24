import redis
import json

class RedisStore:
    def __init__(self, host='localhost', port=6379):
        self.db = redis.Redis(host=host, port=port, decode_responses=True)

    def save(self, key, value):
        print(f"Saving: {key} {value}")
        with self.db.pipeline() as pipe:
            if not value:
                # Handle the case of an empty dictionary separately
                print(f"Deleting key: {key}")
                pipe.delete(key)
            else:
                print(f"Setting key: {key} to {value}")
                pipe.hset(key, mapping={k: json.dumps(v) for k, v in value.items()})
            pipe.execute()

    def load(self, key):
        data = self.db.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()}
