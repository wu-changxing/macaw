# echo_atrium/socketio_server.py
import uuid
import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from channels.db import database_sync_to_async
from django.utils import timezone
import socketio
import itertools

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000", "https://aaron404.com", "http://localhost:8000",
                          "https://eac.aaron404.com"],
    engineio_logger=True,
    logger=True,
    debug=True,
    ping_timeout=20,  # Increase the ping timeout (in seconds)
    ping_interval=10  # Increase the ping interval (in seconds)
)

socket_app = socketio.ASGIApp(sio)
users = {}
rooms = {}
from socketio.exceptions import ConnectionRefusedError

room_id_counter = itertools.count()


def generate_unique_room_id():
    return str(uuid.uuid4())


@database_sync_to_async
def get_token(token_str):
    from rest_framework.authtoken.models import Token
    try:
        return Token.objects.get(key=token_str)
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def update_user_exp(token_str, exp):
    from rest_framework.authtoken.models import Token
    from django.core.exceptions import ObjectDoesNotExist
    token = Token.objects.get(key=token_str)
    user = token.user
    now = timezone.now()  # Now 'now' is timezone-aware

    try:
        user_profile = user.userprofile
        if not user_profile.last_exp_gain or now - user_profile.last_exp_gain >= datetime.timedelta(hours=4):
            user_profile.exp += exp
            user_profile.last_exp_gain = now
            user_profile.save()
        return user_profile.exp
    except ObjectDoesNotExist:
        # Handle case where user does not have a UserProfile
        pass


@database_sync_to_async
def check_user_status(token_str):
    print("Checking status")
    from rest_framework.authtoken.models import Token
    from django.core.exceptions import ObjectDoesNotExist
    token = Token.objects.get(key=token_str)
    user = token.user
    now = timezone.now()  # Now 'now' is timezone-aware

    try:
        user_profile = user.userprofile

        if not user_profile.last_exp_gain:
            return (True, "You can check again immediately.")
        elif now - user_profile.last_exp_gain >= datetime.timedelta(hours=4):
            difference = now - user_profile.last_exp_gain
            hours, remainder = divmod(difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return (True, "You can check again immediately.")
        else:
            difference = datetime.timedelta(hours=4) - (now - user_profile.last_exp_gain)
            hours, remainder = divmod(difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return (False, "You can check again after {} hours, {} minutes, {} seconds.".format(int(hours), int(minutes), int(seconds)))
    except ObjectDoesNotExist:
        return False



@database_sync_to_async
def get_user_from_token(token):
    return token.user


def get_username_by_sid(sid):
    for user in users.values():
        if 'sid' in user and user['sid'] == sid:
            return user['user']
    return None


def get_sid_by_username(username):
    for user in users.values():
        if 'user' in user and user['user'] == username:
            return user['sid']
    return None


@sio.event
async def connect(sid, environ, auth=None):
    if auth and 'token' in auth:
        token_str = auth['token']
        token = await get_token(token_str)
        if token:
            user = await get_user_from_token(token)
            if sid not in sio.environ:
                sio.environ[sid] = {}
            sio.environ[sid]['user'] = user
            users[user.username] = {'user': user.username, 'sid': sid}
            sio.logger.info('User %s connected', user)
            sio.logger.info("sio environ: %s", sio.environ[sid])
            sio.logger.info("auth: %s", auth)
            await sio.emit('connected', {'user': user.username}, room=sid)
        else:
            sio.logger.error('Token not found for: %s', token_str)
            raise ConnectionRefusedError("authentication failed")
    else:
        sio.logger.error('No token provided for sid %s', sid)
        raise ConnectionRefusedError("authentication failed")


@sio.event
async def update_pid(sid, data):
    sio.logger.info(f"update pid: {data}")
    username = data['username']
    peer_id = data['peer_id']
    room_id = data['room_id']
    users[username].update({'peer_id': peer_id, 'room_id': room_id, })
    sio.logger.info(f"update pid: {users[username]}")
    await sio.emit('pid_updated', {'user': users[username]}, room=room_id, skip_sid=sid)


@sio.event
async def join_room(sid, data):
    sio.logger.info(f"\n\n\n\n\n\nthe peer id is ----->>>>>>>>: {data} \n\n\n\n")
    room_id = data['room_id']
    sio.logger.info(f"the users is : {users}")
    peer_id = data['peer_id']
    username = data.get('username', None)
    sio.logger.info(f"join the room : {room_id}")

    sio.enter_room(sid, room_id)
    users[username].update({'room_id': room_id, 'peer_id': peer_id})
    room_users = await get_room_users(room_id)
    await sio.emit('exist_users', {'users': room_users}, room=sid)
    length = len(room_users)
    await sio.emit('user_joined',
                   {'new_user': {'sid': sid, 'username': username, 'peer_id': peer_id, }, 'users': room_users,
                    'users_num': length},
                   room=room_id, skip_sid=sid)


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


async def get_room_users(room_id):
    room_users = {}
    for sid, user_data in users.items():
        if user_data.get('room_id') == room_id:  # Use the get() method to avoid KeyError
            room_users[sid] = user_data
    return room_users


@sio.event
async def leave(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)
    if username in users:
        del users[username]
    await sio.emit('user_left', {'sid': sid, 'username': username}, room=room_id)
    room_users = await get_room_users(room_id)
    if not room_users:
        if room_id in rooms:
            del rooms[room_id]
    await sio.leave_room(sid, room_id)


@sio.event
async def is_room_admin(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)
    if room_id in rooms:
        is_admin = rooms[room_id]['admin'] == username
        await sio.emit('is_admin', {'is_admin': is_admin}, room=sid)
    else:
        await sio.emit('is_admin', {'is_admin': False}, room=sid)


@sio.event
async def create_room(sid, data):
    room_name = data['room_name']
    username = get_username_by_sid(sid)
    room_id = generate_unique_room_id()
    creation_time = datetime.datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S')  # Get the current time and convert it to a string
    rooms[room_id] = {'name': room_name, 'creator': sid, 'admin': username,
                      'created_at': creation_time}  # Store the username as admin and the creation time as a string
    sio.logger.info(f"create the room -->-->>>>: {room_id}")
    await sio.emit('rooms', {'rooms': rooms}, room=sid)
    await sio.emit('room_created', {'room_id': room_id, 'room_name': room_name, 'is_admin': True,
                                    'created_at': creation_time}, room=sid)  # 'created_at' is already a string

    sio.logger.info(f"rooms are : {'rooms':rooms}")
    await sio.emit('is_admin', {'is_admin': True}, room=sid)
    await sio.emit('room_list', {rooms}, )
    # await sio.emit('room_admin', {'room_id': room_id, 'admin': username}, room=room_id)


@sio.event
async def delete_room(sid, data):
    room_id = data['room_id']
    username = users[sid]['user']  # Get the username associated with this sid
    if room_id in rooms and rooms[room_id]['admin'] == username:  # Verify if the user is the admin
        del rooms[room_id]
    await sio.emit('room_deleted', {'room_id': room_id}, room=sid)


@sio.event
async def list_rooms(sid):
    # Convert datetime to string
    # for room in rooms.values():
    #     room['created_at'] = room['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    await sio.emit('rooms', {'rooms': rooms})
    sio.logger.info(f"rooms are : {rooms}")


@sio.event
async def dismiss_room(sid, data):
    room_id = data['room_id']
    username = get_username_by_sid(sid)
    if room_id in rooms and rooms[room_id]['admin'] == username:
        del rooms[room_id]
    await sio.emit('room_dismissed', {'room_id': room_id}, room=room_id)
    await sio.emit('rooms', {'rooms': rooms})


@sio.event
async def check(sid, data):
    username = get_username_by_sid(sid)
    if username:
        user_exp = await update_user_exp(data.get('token'), 2)
        user_sid = get_sid_by_username(username)
        if rooms:
            for room_id, room in rooms.items():  # get the room_id and room details
                await sio.emit('user_checked', {'user': username, 'exp': user_exp}, room=room_id, skip_sid=user_sid)
        await sio.emit('exp_updated', {'user': username, 'exp': user_exp}, room=sid)
    else:
        sio.logger.error('Username not found for sid %s', sid)


@sio.event
async def check_status(sid, data):
    username = get_username_by_sid(sid)
    token = data.get('token')
    if username:
        user_sid = get_sid_by_username(username)
        status,message  = await check_user_status(token)
        await sio.emit('check_status', {'user': username, 'status': status, 'message': message}, room=sid)


@sio.event
async def kick_user(sid, data):
    room_id = data['room_id']
    username_to_kick = data['user']
    username_requesting = get_username_by_sid(sid)

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
            del users[username_to_kick]
            await sio.emit('update_users', {'users': await get_room_users(room_id)}, room=room_id)

        else:
            sio.logger.error(f'User to be kicked not found in room: {username_to_kick}')

    else:
        sio.logger.error('User requesting to kick is not admin')


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
