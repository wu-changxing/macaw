# echo_atrium/events/__init__.py
import datetime
import itertools
import socketio


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
room_id_counter = itertools.count()
from .connect import *
from .admin import *
from .media import *
from .chat import *
from .room import *
from .user import *
