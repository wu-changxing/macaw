# echo_atrium/socketio_server.py

from .events import socket_app,  connect, join_room,  leave, \
    is_room_admin, create_room, delete_room, list_rooms, dismiss_room, check, check_status, kick_user, \
    toggle_video, room_chat_msg

# Assuming that these functions are defined correctly as async functions in their respective modules
# and they are decorated with @sio.event, we do not need to register them here with sio.event(...).
