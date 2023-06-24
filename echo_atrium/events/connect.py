from socketio.exceptions import ConnectionRefusedError
from .utils import get_token, get_user_from_token
from .redis_store import RedisStore
from . import sio
from .helpers import get_room_users

redis_store = RedisStore()  # assuming Redis is running on localhost and the default port

@sio.event
async def connect( sid, environ, auth=None):
    if auth and 'token' in auth:
        token_str = auth['token']
        token = await get_token(token_str)
        if token:
            user = await get_user_from_token(token)
            if sid not in sio.environ:
                sio.environ[sid] = {}
            sio.environ[sid]['user'] = user
            sio.logger.info('User %s connected', user)
            sio.logger.info("sio environ: %s", sio.environ[sid])
            sio.logger.info("auth: %s", auth)
            await sio.emit('connected', {'user': user.username}, room=sid)

            # Save the user to Redis
            users = redis_store.load('users') or {}
            users[user.username] = {'sid': sid, 'username': user.username}  # Save username as well
            redis_store.save('users', users)


        else:
            sio.logger.error('Token not found for: %s', token_str)
            raise ConnectionRefusedError("authentication failed")
    else:
        sio.logger.error('No token provided for sid %s', sid)
        raise ConnectionRefusedError("authentication failed")


@sio.event
async def disconnect(sid):
    user = sio.environ[sid]['user']
    sio.logger.info('User %s disconnected', user)
    #reomve user's roomid and peerid from redis
    users = redis_store.load('users')
    rooms = redis_store.load('rooms')

    username = user.username

    room_id = users[username].get('room_id', None)
    if not room_id:
        return
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
    # Remove the user from Redis
    # users = redis_store.load('users')
    # if user.username in users:
    #     del users[user.username]
    #     redis_store.save('users', users)
