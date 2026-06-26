"""
ASGI entrypoint.

Phase 1 serves the Django HTTP application. Django Channels (WebSocket
routing) is layered in here in Phase 3.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()
