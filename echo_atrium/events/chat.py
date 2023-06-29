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

@sio.event
async def room_chat_img(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    base64_image = data.get('image', None)

    if username is not None:
        if room_id is not None and base64_image is not None:
            # base64 image processing
            # base64_image = base64_image.split(",")[1]  # Strip the base64 image header
            await sio.emit('room_chat_img', {'user': username, 'image': base64_image}, room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} sent an image")
        else:
            sio.logger.error(f"No room_id or image found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")
@sio.event
async def room_chat_file(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    blob_file = data.get('file', None)
    filename = data.get('filename', None)
    filetype = data.get('filetype', None)

    if username is not None:
        if room_id is not None and blob_file is not None and filename is not None and filetype is not None:
            await sio.emit('room_chat_file', {'user': username, 'file': blob_file, 'filename': filename, 'filetype': filetype}, room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} sent a file")
        else:
            sio.logger.error(f"No room_id or file found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")
