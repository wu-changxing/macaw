from datetime import datetime, timezone
from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users
from .redis_store import RedisStore
from . import sio

redis_store = RedisStore()

# Socket.IO Events related to Room management

@sio.event
async def join_room(sid, data):
    username = data.get('username', None)
    room_id = data['room_id']
    peer_id = data['peer_id']

    handle_user_joining(sid, username, room_id, peer_id)
    await broadcast_room_update(sid, room_id, username, peer_id)

@sio.event
async def leave(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)

    handle_user_leaving(sid, username, room_id)
    await broadcast_user_left(sid, room_id, username)

@sio.event
async def create_room(sid, data):
    username = get_username_by_sid(sid)
    room_name = data['room_name']
    room_id = handle_room_creation(sid, username, room_name)

    await sio.emit('your_room_id', {'room_id': room_id}, room=sid)
    await broadcast_room_creation(sid)

@sio.event
async def list_rooms(sid):
    rooms = redis_store.load('rooms')
    await sio.emit('rooms', {'rooms': rooms})

@sio.event
async def fetch_peer_ids(sid, data):
    room_id = data['room_id']
    await update_peer_ids(sid, room_id)

@sio.event
async def fetch_users(sid, data):
    room_id = data['room_id']
    await update_users(sid, room_id)

def handle_user_joining(sid, username, room_id, peer_id):
    sio.enter_room(sid, room_id)
    update_users_data(username, room_id, peer_id)
    update_rooms_data(username, room_id)

def handle_user_leaving(sid, username, room_id):
    update_users_data(username, delete=True)
    update_rooms_data(username, room_id, delete=True)
    sio.leave_room(sid, room_id)

def handle_room_creation(sid, username, room_name):
    room_id = generate_unique_room_id()
    creation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    rooms = redis_store.load('rooms')
    rooms[room_id] = {
        'name': room_name,
        'creator': sid,
        'admin': username,
        'created_at': creation_time,
        'members': [username]
    }
    redis_store.save('rooms', rooms)
    return room_id

def update_users_data(username, room_id=None, peer_id=None, delete=False):
    users = redis_store.load('users')
    last_seen = datetime.utcnow().isoformat()
    if delete:
        del users[username]
    else:
        users[username].update({'room_id': room_id, 'peer_id': peer_id, 'last_seen': last_seen})
    redis_store.save('users', users)

def update_rooms_data(username, room_id, delete=False):
    rooms = redis_store.load('rooms')

    if delete:
        if room_id in rooms:
            rooms[room_id]['members'].remove(username)
            if len(rooms[room_id]['members']) == 0:
                redis_store.delete('rooms', room_id)
    else:
        # Use a list but ensure it behaves like a set by not adding duplicates
        if username not in rooms[room_id].setdefault('members', []):
            rooms[room_id]['members'].append(username)
            redis_store.save('rooms', rooms)



async def broadcast_room_update(sid, room_id, username, peer_id):
    room_users = await get_room_users(room_id)
    await sio.emit('exist_users', {'users': room_users}, room=sid)
    await sio.emit('user_joined', {
        'new_user': {'sid': sid, 'username': username, 'peer_id': peer_id},
        'users': room_users,
        'users_num': len(room_users)
    }, room=room_id, skip_sid=sid)

async def broadcast_user_left(sid, room_id, username):
    await sio.emit('user_left', {'sid': sid, 'user': username}, room=room_id)

async def broadcast_room_creation(sid):
    rooms = redis_store.load('rooms')
    await sio.emit('rooms', {'rooms': rooms}, room=sid)

async def update_peer_ids(sid, room_id):
    room_users = await get_room_users(room_id)
    peer_ids = [user_data['peer_id'] for user_data in room_users.values()]
    await sio.emit('update_peer_ids', {'peer_ids': peer_ids}, room=sid)

async def update_users(sid, room_id):
    room_users = await get_room_users(room_id)
    user_data = [{'sid': user_sid, **user_info} for user_sid, user_info in room_users.items()]
    await sio.emit('update_users', {'users': user_data}, room=sid)
