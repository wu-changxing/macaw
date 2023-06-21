import datetime
import itertools
import socketio
from socketio.exceptions import ConnectionRefusedError

from echo_atrium.utils import get_token, update_user_exp, check_user_status, get_user_from_token
from .helpers import generate_unique_room_id,  get_username_by_sid, get_sid_by_username, get_room_users

# Initialization of socketio
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

# Global variables declaration
socket_app = socketio.ASGIApp(sio)
users = {}
rooms = {}
room_id_counter = itertools.count()
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












