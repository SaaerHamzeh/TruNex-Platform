"""
📡 Utility: Realtime WebSocket Broadcaster to Admin Dashboard
استدعِ أي من دوال البث أدناه لإرسال رسائل فورية إلى واجهة الإدارة.
"""

from typing import Dict, Optional, Union
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def _broadcast(subtype: str, data: Optional[Dict] = None):
    """
    Internal function to send any broadcast message with a `subtype`.
    Always uses type='broadcast' as required by WebSocket handler.
    """
    payload = {
        "type": "broadcast",     # يجب أن تبقى broadcast
        "subtype": subtype       # يتم التعامل معها داخل FetchLogsConsumer
    }

    if data:
        payload.update(data)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "fetch_logs",
        payload
    )


# ✅ Public Functions (call these from views / tasks)

def push_log(message: str):
    """🔁 Push live log message to dashboard."""
    _broadcast("log", {"message": message})


def push_countdown(next_fetch_timestamp: Union[int, float]):
    """⏳ Push countdown until next fetch run."""
    _broadcast("countdown", {
        "next_fetch_timestamp": int(next_fetch_timestamp)
    })


def push_toggle_state(enabled: bool):
    """🟢🔴 Notify dashboard about new fetching state."""
    _broadcast("toggle_fetch", {
        "enabled": enabled
    })


def push_updated_settings(fetch_interval: int, fetch_limit: int):
    """⚙️ Push updated fetch config (interval + limit)."""
    _broadcast("update_settings", {
        "fetch_interval": fetch_interval,
        "fetch_limit": fetch_limit
    })


def push_generic_alert(message: str, level: str = "info"):
    """📢 Optional utility for sending alerts (future use)."""
    _broadcast("alert", {
        "message": message,
        "level": level  # e.g., info, warning, error
    })
