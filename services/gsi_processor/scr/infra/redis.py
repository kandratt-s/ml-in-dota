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
    

class EnemyStateRepository:
    def __init__(self, client: RedisClient) -> None:
        self.r = client.raw

    def _heroes_key(self, token: str) -> str:
        return f"token:{token}:enemy_heroes"

    def _last_seen_key(self, token: str) -> str:
        return f"token:{token}:enemy_last_seen"

    def _distances_key(self, token: str) -> str:
        return f"token:{token}:enemy_distances"
    
    def _positions_key(self, token: str) -> str:
        return f"token:{token}:enemy_positions"
    



    async def write_enemy_positions(self, token: str, data: dict[str, tuple[int, int]]) -> None:
        mapping = {str(k): json.dumps(v) for k, v in data.items()}
        await self.r.hset(self._positions_key(token), mapping=mapping)

    async def read_enemy_positions(self, token: str) -> dict[str, tuple[int, int]]:
        raw = await self.r.hgetall(self._positions_key(token))
        return {k: tuple(json.loads(v)) for k, v in raw.items()}



    async def write_enemy_heroes(self, token: str, data: list[str]) -> None:
        key = self._heroes_key(token)
        if data:
            await self.r.delete(key)              
            await self.r.sadd(key, *data)         

    async def read_enemy_heroes(self, token: str) -> set[str]:
        key = self._heroes_key(token)
        return set(await self.r.smembers(key))



    async def write_last_seen(self, token: str, values: dict[str, int]) -> None:
        mapping = {k: str(v) for k, v in values.items()}
        await self.r.hset(self._last_seen_key(token), mapping=mapping)


    async def read_last_seen(self, token: str) -> dict[str, int]:
        raw = await self.r.hgetall(self._last_seen_key(token))
        return {k: int(v) for k, v in raw.items()}



    async def write_distances(self, token: str, values: dict[str, int]) -> None:
        mapping = {k: str(v) for k, v in values.items()}
        await self.r.hset(self._distances_key(token), mapping=mapping)


    async def read_distances(self, token: str) -> dict[str, int]:
        raw = await self.r.hgetall(self._distances_key(token))
        return {k: int(v) for k, v in raw.items()}


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

