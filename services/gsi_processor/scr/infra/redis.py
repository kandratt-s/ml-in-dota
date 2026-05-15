import json

import redis.asyncio as aioredis

from scr.schemas.inference_queue import InferenceRecord
from scr.schemas.snapshot import SnapshotState


class RedisClient:
    def __init__(self, url: str, *, max_connections: int | None = None) -> None:
        self._redis = aioredis.Redis.from_url(
            url,
            decode_responses=True,
            max_connections=max_connections,
        )

    async def close(self) -> None:
        await self._redis.aclose()

    @property
    def raw(self) -> aioredis.Redis:
        return self._redis
    

class ActiveTokensRepository:
    def __init__(self, client: RedisClient) -> None:
        self.r = client.raw
        self.prefix = "active:token:"
        self.ttl = 5400

    async def add(self, token: str) -> None:
        key = self.prefix + token
        await self.r.set(key, 1, ex=self.ttl)

    async def remove(self, token: str) -> None:
        await self.r.delete(self.prefix + token)

    async def is_active(self, token: str) -> bool:
        # key = self.prefix + token
        # return await self.r.exists(key) == 1
        return True


class InferenceQueueRepository:
    def __init__(self, client: RedisClient, queue_name: str) -> None:
        self.r = client.raw
        self.queue_name = queue_name

    async def enqueue_request(self, record: InferenceRecord) -> None:
        message = record.model_dump_json()
        # Use Redis Streams for enqueueing requests
        await self.r.xadd(self.queue_name, {"data": message})


class SnapshotStateRepository:
    """
    Repository for storing and retrieving GSI snapshots for comparison with previous state.
    
    Each token (player session) has a snapshot cache that stores the previous GSI state.
    This allows features to be computed based on delta/changes between snapshots.
    """
    
    def __init__(self, client: RedisClient) -> None:
        self.r = client.raw
        self.prefix = "snapshot"
    
    def _snapshot_key(self, token: str) -> str:
        """Generate Redis key for storing snapshot state for a token."""
        return f"{self.prefix}:{token}:current"
    
    async def get_previous_snapshot(self, token: str) -> SnapshotState | None:
        """
        Load the previous snapshot (n-1) for a given token.
        
        Args:
            token: Player session token
            
        Returns:
            Previous snapshot as dict, or None if no previous snapshot exists
        """
        try:
            raw_snapshot = await self.r.get(self._snapshot_key(token))
            if not raw_snapshot:
                return None
            return SnapshotState.model_validate_json(raw_snapshot)
        except (json.JSONDecodeError, Exception):
            return None
    
    async def save_current_snapshot(self, token: str, snapshot: SnapshotState) -> None:
        """
        Save the current snapshot for a given token (will become n-1 on next call).
        
        Args:
            token: Player session token
            snapshot: Current snapshot data to store
        """
        try:
            snapshot_json = snapshot.model_dump_json()
            # Store without expiration - will be updated on next GSI event
            await self.r.set(self._snapshot_key(token), snapshot_json)
        except Exception as e:
            # Log but don't fail - snapshot storage is not critical
            import logging
            logging.warning(f"Failed to save snapshot for token {token}: {e}")
    
    async def clear_snapshot(self, token: str) -> None:
        """
        Clear the snapshot for a given token (e.g., when game ends).
        
        Args:
            token: Player session token
        """
        try:
            await self.r.delete(self._snapshot_key(token))
        except Exception:
            pass


