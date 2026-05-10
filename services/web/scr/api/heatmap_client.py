import redis
import json
import logging
from scr.infra.config import settings

class HeatmapClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True  
        )

    def get_current_heatmap(self) -> list[list[float]] | None:
        try:
            data = self.client.get("heat_map")
            if not data:
                return None
            
            return json.loads(data)
        except Exception as e:
            logging.error(f"Error fetching heatmap from Redis: {e}")
            return None

def get_heatmap_client():
    return HeatmapClient()