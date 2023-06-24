from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users, get_sid_by_username
from .redis_store import RedisStore
from . import sio

redis_store = RedisStore()


@sio.event
async def kick_user(sid, data):
    room_id = data['room_id']
    username_to_kick = data['user']
    username_requesting = get_username_by_sid(sid)

    rooms = redis_store.load('rooms')
    users = redis_store.load('users')

    if room_id in rooms and rooms[room_id]['admin'] == username_requesting:
        user_data_to_kick = None
        for username, user_data in users.items():
            if username == username_to_kick and user_data.get('room_id') == room_id:
                user_data_to_kick = user_data
                break

        if user_data_to_kick:
            await sio.emit('user_kicked', {'user': username_to_kick}, room=room_id)
            infom_sid = get_sid_by_username(username_to_kick)
            await sio.emit('you_kicked', {'user': username_to_kick}, room=infom_sid)
            await sio.disconnect(user_data_to_kick['sid'])

            # Update users
            del users[username_to_kick]
            redis_store.save('users', users)

            await sio.emit('update_users', {'users': await get_room_users(room_id)}, room=room_id)
        else:
            sio.logger.error(f'User to be kicked not found in room: {username_to_kick}')
    else:
        sio.logger.error('User requesting to kick is not admin')


@sio.event
async def is_room_admin(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)
    rooms = redis_store.load('rooms')

    if room_id in rooms:
        is_admin = rooms[room_id]['admin'] == username
        await sio.emit('is_admin', {'is_admin': is_admin}, room=sid)
    else:
        await sio.emit('is_admin', {'is_admin': False}, room=sid)


@sio.event
async def dismiss_room(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)
    rooms = redis_store.load('rooms')

    rooms_to_delete = []
    for id, room in rooms.items():
        if room['admin'] == username:
            rooms_to_delete.append(id)

    for id in rooms_to_delete:
        del rooms[id]

    redis_store.save('rooms', rooms)

    for room_id in rooms_to_delete:
        await sio.emit('room_dismissed', {'room_id': room_id}, room=room_id)

    await sio.emit('rooms', {'rooms': rooms})


@sio.event
async def delete_room(sid, data):
    room_id = data['room_id']
    users = redis_store.load('users')
    rooms = redis_store.load('rooms')

    username = users[sid]['user']  # Get the username associated with this sid
    if room_id in rooms and rooms[room_id]['admin'] == username:  # Verify if the user is the admin
        del rooms[room_id]
        redis_store.save('rooms', rooms)

    await sio.emit('room_deleted', {'room_id': room_id}, room=sid)


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
