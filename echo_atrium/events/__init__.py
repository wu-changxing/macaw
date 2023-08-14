# echo_atrium/events/__init__.py
import datetime
import itertools
import socketio
import logging

socketio_logger = logging.getLogger('socketio')  # Get the 'socketio' logger

# Initialization of socketio
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000","http://127.0.0.1:3000","https://backend.aaron404.com", "http://localhost:8000",
                          "https://eac.aaron404.com"],
    engineio_logger=socketio_logger,
    logger=socketio_logger,
    debug=False,  # Set debug level to False (Error level)
    ping_timeout=20,  # Increase the ping timeout (in seconds)
    ping_interval=10,  # Increase the ping interval (in seconds)
    max_http_buffer_size=1024 * 1024 * 100,  # Increase the maximum HTTP buffer size (in bytes)
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
from .quiz_socket import *
