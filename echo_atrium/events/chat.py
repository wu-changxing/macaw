from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users
from . import sio

@sio.event
async def room_chat_msg(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    message = data.get('message', None)
    if username is not None:
        if room_id is not None:
            await sio.emit('room_chat_msg', {'user': username, 'message': message}, room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} send message {message}")
        else:
            sio.logger.error(f"No room_id found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")
