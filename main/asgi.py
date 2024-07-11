import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from notifications.consumers import UserNotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

websocket_urlpatterns = [
    path('ws/notifications/', UserNotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "https": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        ))
})
