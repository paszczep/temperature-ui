from asgiref.wsgi import WsgiToAsgi
from application import create_app

# asgi_app = WsgiToAsgi(create_app())

app = create_app()
