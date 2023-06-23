# room.py
import datetime
from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users
from .redis_store import RedisStore
from . import sio

redis_store = RedisStore()

# Socket.IO Events related to Room management

# Event for joining a room
@sio.event
async def join_room(sid, data):
    room_id = data['room_id']
    peer_id = data['peer_id']
    username = data.get('username', None)

    sio.enter_room(sid, room_id)

    # Load users from Redis
    users = redis_store.load('users')
    users[username].update({'room_id': room_id, 'peer_id': peer_id})

    # Save back to Redis
    redis_store.save('users', users)

    room_users = await get_room_users(room_id)

    await sio.emit('exist_users', {'users': room_users}, room=sid)

    length = len(room_users)
    await sio.emit('user_joined', {
        'new_user': {'sid': sid, 'username': username, 'peer_id': peer_id},
        'users': room_users,
        'users_num': length
    }, room=room_id, skip_sid=sid)

# Event for leaving a room
@sio.event
async def leave(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)

    # Load users and rooms from Redis
    users = redis_store.load('users')
    rooms = redis_store.load('rooms')

    if username in users:
        del users[username]
        redis_store.save('users', users)

    await sio.emit('user_left', {'sid': sid, 'user': username}, room=room_id)

    room_users = await get_room_users(room_id)
    if not room_users:
        if room_id in rooms:
            del rooms[room_id]
            redis_store.save('rooms', rooms)

    await sio.leave_room(sid, room_id)

# Event to check if a user is the admin of a room
@sio.event
async def is_room_admin(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)

    # Load rooms from Redis
    rooms = redis_store.load('rooms')

    if room_id in rooms:
        is_admin = rooms[room_id]['admin'] == username
        await sio.emit('is_admin', {'is_admin': is_admin}, room=sid)
    else:
        await sio.emit('is_admin', {'is_admin': False}, room=sid)

# Event for creating a room
@sio.event
async def create_room(sid, data):
    room_name = data['room_name']
    username = get_username_by_sid(sid)
    room_id = generate_unique_room_id()
    creation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Load rooms from Redis
    rooms = redis_store.load('rooms')

    rooms[room_id] = {'name': room_name, 'creator': sid, 'admin': username, 'created_at': creation_time}
    redis_store.save('rooms', rooms)

    await sio.emit('rooms', {'rooms': rooms}, room=sid)
    await sio.emit('room_created', {'room_id': room_id, 'room_name': room_name, 'is_admin': True, 'created_at': creation_time})
    await sio.emit('is_admin', {'is_admin': True}, room=sid)
    await sio.emit('your_room_id', {'room_id': room_id}, room=sid)

# Event for listing rooms
@sio.event
async def list_rooms(sid):
    # Load rooms from Redis
    rooms = redis_store.load('rooms')

    await sio.emit('rooms', {'rooms': rooms})
@sio.event
async def fetch_peer_ids(sid, data):
    room_id = data['room_id']
    room_users = await get_room_users(room_id)
    sio.logger.info(f"  --------->>fetch peer ids : {room_users}")
    peer_ids = [user_data['peer_id'] for user_data in room_users.values()]
    await sio.emit('update_peer_ids', {'peer_ids': peer_ids}, room=sid)


@sio.event
async def fetch_users(sid, data):
    room_id = data['room_id']
    room_users = await get_room_users(room_id)
    sio.logger.info(f"  --------->>fetch users : {room_users}")
    user_data = [{'sid': user_sid, **user_info} for user_sid, user_info in room_users.items()]
    await sio.emit('update_users', {'users': user_data}, room=sid)