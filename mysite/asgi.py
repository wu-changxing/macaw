import os
from django.core.asgi import get_asgi_application
from echo_atrium.socketio_server import socket_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings.dev')

django_asgi_app = get_asgi_application()

async def application(scope, receive, send):
    if scope["type"] == "websocket":
        await socket_app(scope, receive, send)
    elif scope["type"] == "http":
        if scope["path"].startswith("/socket.io/"):
            await socket_app(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    else:
        print(scope)
        print("Unknown scope type: ", scope["type"])
        raise ValueError("Unsupported connection type: %s" % scope["type"])
