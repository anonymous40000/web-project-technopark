import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def centrifugo_publish(channel: str, data: dict) -> bool:
    try:
        url = f"{settings.CENTRIFUGO_HTTP_URL}/api"
        payload = {
            "method": "publish",
            "params": {
                "channel": channel,
                "data": data
            }
        }
        
        r = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": settings.CENTRIFUGO_API_KEY,
            },
            json=payload,
            timeout=3,
        )
        
        r.raise_for_status()
        print(f"✅ Published to channel: {channel}")
        return True
        
    except Exception as e:
        print(f"❌ Centrifugo error: {e}")
        return False