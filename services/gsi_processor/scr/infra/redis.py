import json
from typing import Any

import redis.asyncio as aioredis


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
    

class TokenPresenceRepository:
    def __init__(self, client: RedisClient) -> None:
        self.r = client.raw

    async def mark_active(self, token: str, ttl_sec: int) -> None:
        await self.r.set(f"auth:active:{token}", "1", ex=ttl_sec)

    async def is_active(self, token: str) -> bool:
        return await self.r.get(f"auth:active:{token}") is not None
    

class TokenDataRepository:
    def __init__(self, client: RedisClient) -> None:
        self.r = client.raw

    async def write_json(self, token: str, data: dict[str, Any], ttl_sec: int | None = None) -> None:
        value = json.dumps(data, ensure_ascii=False)
        if ttl_sec is None:
            await self.r.set(f"token:data:{token}", value)
        else:
            await self.r.set(f"token:data:{token}", value, ex=ttl_sec)

    async def read_json(self, token: str) -> dict[str, Any] | None:
        raw = await self.r.get(f"token:data:{token}")
        if raw is None:
            return None
        return json.loads(raw)


class FeatureStreamRepository:
    def __init__(self, client: RedisClient, stream_name: str = "features:inference") -> None:
        self.r = client.raw
        self.stream_name = stream_name

    async def write_features(self, payload: dict[str, Any]) -> str:
        message_id = await self.r.xadd(self.stream_name, payload)
        return str(message_id)