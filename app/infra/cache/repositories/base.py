from redis.asyncio import Redis


class RedisRepository:
    def __init__(self, redis: Redis) -> None:
        super().__init__()
        self._redis = redis
