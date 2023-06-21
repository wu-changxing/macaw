from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users
from echo_atrium.events import sio
@sio.event
async def toggle_video(sid, data):
    username = get_username_by_sid(sid)
    status = data['status']
    room_id = data.get('room_id', None)
    if username is not None:
        if room_id is not None:
            await sio.emit('toggle_video', {'user': username, 'status': status}, room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} toggle video to {status}")
        else:
            sio.logger.error(f"No room_id found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")

