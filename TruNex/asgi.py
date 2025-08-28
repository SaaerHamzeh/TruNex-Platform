"""
ASGI config for TruNex project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TruNex.settings")

# application = get_asgi_application()

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf import settings
from django.conf.urls.static import static
from TruNexApp.routing import websocket_urlpatterns

# ✅ هذا مهم لتفعيل static files
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TruNex.settings")

django_asgi_app = get_asgi_application()

# ✅ لف الـ Django app بـ static handler أثناء التطوير
application = ProtocolTypeRouter(
    {
        "http": ASGIStaticFilesHandler(django_asgi_app),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
