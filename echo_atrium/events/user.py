from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users, get_sid_by_username
from .utils import get_token, update_user_exp, check_user_status, get_user_from_token
from .redis_store import RedisStore
from . import sio

redis_store = RedisStore()


@sio.event
async def check_status(sid, data):
    username = get_username_by_sid(sid)
    token = data.get('token')
    if username:
        status, message = await check_user_status(token)
        await sio.emit('check_status', {'user': username, 'status': status, 'message': message}, room=sid)


@sio.event
async def check(sid, data):
    username = get_username_by_sid(sid)
    if username:
        user_exp = await update_user_exp(data.get('token'), 2)
        user_sid = get_sid_by_username(username)

        rooms = redis_store.load('rooms')
        if rooms:
            for room_id, room in rooms.items():  # get the room_id and room details
                await sio.emit('user_checked', {'user': username, 'exp': user_exp}, room=room_id, skip_sid=user_sid)

        await sio.emit('exp_updated', {'user': username, 'exp': user_exp}, room=sid)
    else:
        sio.logger.error('Username not found for sid %s', sid)
