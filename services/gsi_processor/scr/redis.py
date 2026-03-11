import redis.asyncio as aioredis


class RedisClient:
    def __init__(self, host: str, port: int, db: int):
        self.redis = aioredis.Redis(host=host, port=port, db=db)

    async def set(self, key: str, value: str):
        await self.redis.set(key, value)

    async def get(self, key: str) -> str:
        return await self.redis.get(key)