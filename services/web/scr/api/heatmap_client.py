import json
import logging
from typing import Any

import httpx
import redis
from scr.infra.config import settings

logger = logging.getLogger(__name__)


class InferenceClient:
    """Client for interacting with the inference service."""
    
    def __init__(
        self,
        redis_host: str = settings.REDIS_HOST,
        redis_port: int = settings.REDIS_PORT,
        redis_password: str | None = settings.REDIS_PASSWORD,
        inference_service_url: str | None = None,
        request_timeout: float = settings.REQUEST_TIMEOUT_SECONDS,
    ):
        """
        Initialize the inference client.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_password: Redis password (optional)
            inference_service_url: Base URL of inference service for direct API calls
            request_timeout: Timeout for HTTP requests
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
        self.inference_service_url = inference_service_url
        self.request_timeout = request_timeout
        self._input_queue = "inference:input"
        self._output_queue = "inference:output"
        self._heatmap_result_key = "heat_map"

    def enqueue_prediction_request(self, record_id: str, payload: dict[str, Any]) -> bool:
        """
        Enqueue a prediction request to the inference service.
        
        Args:
            record_id: Unique identifier for the request
            payload: Data payload containing features for prediction
            
        Returns:
            True if successfully enqueued, False otherwise
        """
        try:
            request_data = {
                "record_id": record_id,
                "payload": payload,
            }
            message = json.dumps(request_data, ensure_ascii=False)
            # use Redis Streams for queueing requests
            try:
                self.redis_client.xadd(self._input_queue, {"data": message})
            except Exception:
                # fallback to rpush for older Redis instances if necessary
                self.redis_client.rpush(self._input_queue, message)
            logger.info("Enqueued prediction request: %s", record_id)
            return True
        except Exception as e:
            logger.error("Error enqueuing prediction request: %s", e)
            return False

    def get_latest_result(self) -> dict[str, Any] | None:
        """
        Get the latest result from the inference output queue.
        
        Note: This pops the result from the queue. If you need to keep results,
        consider using get_heatmap_result instead.
        
        Returns:
            Latest inference result or None if queue is empty
        """
        try:
            result = self.redis_client.rpop(self._output_queue)
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            logger.error("Error retrieving inference result: %s", e)
            return None

    def get_all_results(self) -> list[dict[str, Any]]:
        """
        Get all results from the inference output queue (non-destructive peek).
        
        Returns:
            List of all results currently in the output queue
        """
        try:
            results = []
            result = self.redis_client.lpop(self._output_queue)
            while result:
                try:
                    results.append(json.loads(result))
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in output queue: %s", result)
                result = self.redis_client.lpop(self._output_queue)
            return results
        except Exception as e:
            logger.error("Error retrieving inference results: %s", e)
            return []

    def get_current_heatmap(self) -> list[list[float]] | None:
        """
        Get the current heatmap from Redis.
        
        Returns:
            Heatmap matrix or None if not available
        """
        try:
            # Try GETDEL if available to atomically get and delete the key
            data = None
            try:
                getdel = getattr(self.redis_client, "getdel", None)
                if callable(getdel):
                    data = self.redis_client.getdel(self._heatmap_result_key)
                else:
                    # fallback to transaction: GET then DEL
                    pipe = self.redis_client.pipeline()
                    pipe.get(self._heatmap_result_key)
                    pipe.delete(self._heatmap_result_key)
                    res = pipe.execute()
                    data = res[0]
            except Exception:
                # last-resort single GET (do not delete) to remain safe
                data = self.redis_client.get(self._heatmap_result_key)

            if not data:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error("Error fetching heatmap from Redis: %s", e)
            return None

    def set_heatmap(self, heatmap: list[list[float]]) -> bool:
        """
        Store a heatmap in Redis.
        
        Args:
            heatmap: 2D list of float values
            
        Returns:
            True if successfully stored, False otherwise
        """
        try:
            data = json.dumps(heatmap, ensure_ascii=False)
            self.redis_client.set(self._heatmap_result_key, data)
            logger.info("Heatmap stored in Redis")
            return True
        except Exception as e:
            logger.error("Error storing heatmap: %s", e)
            return False

    def check_inference_health(self) -> dict[str, Any] | None:
        """
        Check the health of the inference service.
        
        Returns:
            Health response dict or None if service is unavailable
        """
        if not self.inference_service_url:
            logger.warning("Inference service URL not configured")
            return None

        try:
            with httpx.Client(timeout=self.request_timeout) as client:
                response = client.get(
                    f"{self.inference_service_url}/inference/health",
                    timeout=self.request_timeout,
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning("Inference service returned status %d", response.status_code)
                    return None
        except Exception as e:
            logger.error("Error checking inference service health: %s", e)
            return None


def get_inference_client() -> InferenceClient:
    """Factory function to create an InferenceClient instance."""
    return InferenceClient(inference_service_url=settings.INFERENCE_SERVICE_URL)