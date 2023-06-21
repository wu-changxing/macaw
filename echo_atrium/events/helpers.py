import uuid
from .redis_store import RedisStore

redis_store = RedisStore()

def generate_unique_room_id():
    return str(uuid.uuid4())

def get_username_by_sid(sid):
    users = redis_store.load('users')
    for user in users.values():
        if 'sid' in user and user['sid'] == sid:
            return user['username']  # Now 'username' key exists
    return None


def get_sid_by_username(username):
    users = redis_store.load('users')
    for user in users.values():
        if 'username' in user and user['username'] == username:
            return user['sid']
    return None

async def get_room_users(room_id):
    users = redis_store.load('users')
    room_users = {}
    for username, user_data in users.items():
        if user_data.get('room_id') == room_id:  # Use the get() method to avoid KeyError
            room_users[username] = user_data
    return room_users
