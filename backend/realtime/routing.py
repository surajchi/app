from django.urls import re_path

from realtime.consumers import MarketConsumer

websocket_urlpatterns = [
    re_path(r"^ws/$", MarketConsumer.as_asgi()),
]
