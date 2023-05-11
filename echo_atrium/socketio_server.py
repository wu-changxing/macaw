import django

django.setup()
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from channels.db import database_sync_to_async

import socketio
from rest_framework.authtoken.models import Token
import itertools
from sanic_cors import CORS, cross_origin

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000"],
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
    return next(room_id_counter)


@database_sync_to_async
def get_token(token_str):
    try:
        return Token.objects.get(key=token_str)
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def get_user_from_token(token):
    return token.user


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
            users[user.username] = {'user': user.username, 'token': token_str, 'sid': sid}
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
    await sio.emit('pid_updated', {'user':users[username]}, room=room_id, skip_sid=sid)
@sio.event
async def join_room(sid, data):
    room_id = data['room_id']
    sio.logger.info(f"the users is : {users}")
    peer_id = users[data['username']]['peer_id']
    sio.logger.info(f"\n\n\n\n\n\nthe peer id is ----->>>>>>>>: {data} \n\n\n\n")
    username = data.get('username', None)
    sio.logger.info(f"join the room : {room_id}")
    sio.enter_room(sid, room_id)
    users[username].update({'room_id': room_id, 'peer_id': peer_id })
    room_users = await get_room_users(room_id)
    await sio.emit('user_joined', {'sid': sid,  'username':username, 'users':room_users, 'peer_id':peer_id}, room=room_id, skip_sid=sid)

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
    await sio.leave_room(sid, room_id)
    if sid in users:
        del users[sid]
    await sio.emit('user_left', {'sid': sid}, room=room_id)
    room_users = await get_room_users(room_id)
    if not room_users:
        if room_id in rooms:
            del rooms[room_id]


@sio.event
async def create_room(sid, data):
    room_name = data['room_name']
    room_id = generate_unique_room_id()
    rooms[room_id] = {'name': room_name, 'creator': sid}
    sio.logger.info(f"create the room -->-->>>>: {room_id}")
    await sio.emit('room_created', {'room_id': room_id, 'room_name': room_name}, room=sid)

@sio.event
async def delete_room(sid, data):
    room_id = data['room_id']
    if room_id in rooms and rooms[room_id]['creator'] == sid:
        del rooms[room_id]
    await sio.emit('room_deleted', {'room_id': room_id}, room=sid)

@sio.event
async def list_rooms(sid):
    room_list = [{'room_id': room_id, 'room_name': room['name']} for room_id, room in rooms.items()]
    await sio.emit('room_list', {'rooms': room_list}, room=sid)