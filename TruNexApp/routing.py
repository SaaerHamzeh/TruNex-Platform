from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/fetch-logs/$", consumers.FetchLogsConsumer.as_asgi()),
]



# from django.urls import path
# from . import consumers

# websocket_urlpatterns = [
#     path('ws/fetch-logs/', consumers.FetchLogsConsumer.as_asgi()),
# ]
