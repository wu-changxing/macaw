import redis
import json
class RedisStore:
    def __init__(self, host='localhost', port=6379):
        self.db = redis.Redis(host=host, port=port, decode_responses=True)

    def save(self, key, value):
        print(f"Saving: {key} {value}")
        try:
            with self.db.pipeline() as pipe:
                if value:
                    print(f"Setting key: {key} to {value}")
                    for k, v in value.items():
                        pipe.hset(key, k, json.dumps(v))
                pipe.execute()
        except Exception as e:
            print(f"Error saving data to Redis: {e}")

    def delete(self, key, field=None):
        try:
            with self.db.pipeline() as pipe:
                if field is None:
                    print(f"Deleting key: {key}")
                    pipe.delete(key)
                else:
                    print(f"Deleting field: {field} from key: {key}")
                    pipe.hdel(key, field)
                pipe.execute()
        except Exception as e:
            print(f"Error deleting data from Redis: {e}")

    def load(self, key):
        data = self.db.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()}
