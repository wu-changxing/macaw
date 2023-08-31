# echo_atrium/events/chat.py
from .helpers import generate_unique_room_id, get_username_by_sid, get_room_users, redis_store
from . import sio
from .utils import get_token, update_user_exp, check_user_status,deduct_credits_and_add_exp, add_exp_to_user


@sio.event
async def room_chat_msg(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    message = data.get('message', None)

    if username is not None:
        if room_id is not None:
            await sio.emit('room_chat_msg', {'user': username, 'message': message}, room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} sent message {message}")

            rooms = redis_store.load('rooms')

            if room_id in rooms:
                # Initialize the 'last_10_messages' field if it does not exist
                if 'last_10_messages' not in rooms[room_id]:
                    rooms[room_id]['last_10_messages'] = []

                # Append the new message
                rooms[room_id]['last_10_messages'].append({'user': username, 'message': message})

                # Keep only the last 10 messages
                rooms[room_id]['last_10_messages'] = rooms[room_id]['last_10_messages'][-3:]

                # Save the updated rooms info back to Redis
                redis_store.save('rooms', rooms)

            else:
                sio.logger.error(f"room_id {room_id} not found")

        else:
            sio.logger.error(f"No room_id found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")


@sio.event
async def pin_message(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    message = data.get('message', None)

    if username is not None:
        rooms = redis_store.load('rooms')
        if room_id in rooms and rooms[room_id]['admin'] == username:
            if 'pinned_messages' not in rooms[room_id]:
                rooms[room_id]['pinned_messages'] = []

            rooms[room_id]['pinned_messages'].append({'user': username, 'message': message, 'isPinned': True})
            await sio.emit('room_chat_msg',
                           {'user': f'PIN', 'message': f"{username} 说： {message}",
                            'isPinned': True}, room=room_id)

            redis_store.save('rooms', rooms)
        else:
            sio.logger.error(f"User {username} not authorized to pin messages in room {room_id}")
    else:
        sio.logger.error(f"No user_info found for user {username}")


@sio.event
async def unpin_message(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    message = data.get('message', None)

    if username is not None:
        rooms = redis_store.load('rooms')
        if room_id in rooms and rooms[room_id]['admin'] == username:
            if 'pinned_messages' in rooms[room_id]:
                rooms[room_id]['pinned_messages'] = [m for m in rooms[room_id]['pinned_messages'] if
                                                     m['message'] != message]
                redis_store.save('rooms', rooms)
                await sio.emit('room_chat_msg',
                               {'user': 'System', 'message': f"{username} unpin and delete:->{message}",
                                'isPinned': False}, room=room_id)

        else:
            sio.logger.error(f"User {username} not authorized to unpin messages in room {room_id}")
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
            await sio.emit('room_chat_file',
                           {'user': username, 'file': blob_file, 'filename': filename, 'filetype': filetype},
                           room=room_id, skip_sid=sid)
            sio.logger.info(f"User {username} sent a file")
        else:
            sio.logger.error(f"No room_id or file found for user {username}")
    else:
        sio.logger.error(f"No user_info found for user {username}")


@sio.event
async def send_gift(sid, data):
    username = get_username_by_sid(sid)
    room_id = data.get('room_id', None)
    gift = data.get('gift', None)
    credits = gift.get('credits', None)
    exp = gift.get('exp', None)
    image = gift.get('image', None)
    designer = gift.get('designer', None)
    from_user = data.get('from', None)
    to_user =data.get('to', None)

    if username is not None and room_id is not None:
        if username == from_user:
            success = await deduct_credits_and_add_exp(from_user, credits, exp)
            if success:
                await add_exp_to_user(to_user, exp)
                gift = {
                    'user': from_user,
                    'gift': gift,
                    'credits': credits,
                    'exp': exp,
                    'image': image,
                    'designer': designer,
                    'from': username,
                    'to': to_user
                }
                await sio.emit('receive_gift', {'user':username, 'gift': gift},
                               room=room_id, skip_sid=sid)
                sio.logger.info(f"User {from_user} sent a gift to {to_user}")
            else:
                sio.logger.error(f"Insufficient credits for user {from_user}")
        else:
            sio.logger.error(f"Username mismatch: {username} does not match {from_user}")
    else:
        sio.logger.error(f"Gift could not be sent from user {from_user} to user {to_user}")
