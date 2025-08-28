# from channels.generic.websocket import AsyncWebsocketConsumer
# import json


# class FetchLogConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.channel_layer.group_add("fetch_logs", self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard("fetch_logs", self.channel_name)

#     async def receive(self, text_data):
#         pass  # غير ضروري في حالتنا

#     async def fetch_log_message(self, event):
#         if event.get("subtype") == "countdown":
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "message": event["message"],
#                         "next_fetch_timestamp": event["next_fetch_timestamp"],
#                         "subtype": "countdown",
#                     }
#                 )
#             )
#         else:
#             await self.send(text_data=json.dumps({"message": event["message"]}))

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class FetchLogsConsumer(AsyncWebsocketConsumer):
    """Handles real‑time fetch logs and control messages with internal subtype dispatch."""

    async def connect(self):
        self.group_name = "fetch_logs"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive a message from client and broadcast it to group."""
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # Always forward the broadcast
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast",
                **payload,
            },
        )

    async def broadcast(self, event):
        """Main message dispatcher from channel layer."""
        subtype = event.get("subtype")

        # Dispatch to specific handler if defined
        handler_name = f"handle_{subtype}"
        handler = getattr(self, handler_name, None)

        if callable(handler):
            await handler(event)
        else:
            # Default: just send raw event
            await self.send(text_data=json.dumps(event))

    # ✅ Handlers for specific subtypes
    async def handle_toggle_fetch(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "subtype": "toggle_fetch",
                    "enabled": event.get("enabled", False),
                    "message": "🔁 Auto-fetch state updated",
                }
            )
        )

    async def handle_update_settings(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "subtype": "update_settings",
                    "fetch_interval": event.get("fetch_interval"),
                    "fetch_limit": event.get("fetch_limit"),
                    "message": "⚙️ Settings changed",
                }
            )
        )

    async def handle_log(self, event):
        await self.send(
            text_data=json.dumps(
                {"subtype": "log", "message": event.get("message", "")}
            )
        )
