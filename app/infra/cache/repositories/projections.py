import json
from uuid import UUID, uuid4

from app.dto.projections import Projection, UpsertProjection
from app.infra.cache.common import CELERY_KEY_PREFIX, KEY_PREFIX, as_awaitable, scan_keys_page
from app.infra.cache.repositories.base import RedisRepository

PROJECTION_KEY = KEY_PREFIX + "projections"


class RedisEngineProjectionRepository(RedisRepository):
    async def get(self, *, offset: int = 0, limit: int = 100) -> list[Projection]:
        prefix = PROJECTION_KEY + "*"

        keys = await scan_keys_page(
            self._redis,
            prefix,
            cursor=offset,
            limit=limit,
        )

        pipe = self._redis.pipeline(transaction=False)

        for key in keys:
            pipe.hgetall(key)

        vals = await as_awaitable(pipe.execute())

        data = [
            ({k: json.loads(v) for k, v in val.items()} | {"engine_id": key.split(":")[-1]})
            for key, val in zip(keys, vals)
            if val
        ]

        return [Projection.model_validate(item) for item in data]

    async def upsert(self, projection: UpsertProjection) -> None:
        key = PROJECTION_KEY + str(projection.engine_id)

        data = projection.model_dump(exclude={"engine_id"}, mode="json", exclude_none=True)
        payload = {k: json.dumps(v) for k, v in data.items()}
        await as_awaitable(self._redis.hset(key, mapping=payload))

    async def delete(self, engine_id: UUID) -> None:
        key = PROJECTION_KEY + str(engine_id)
        await as_awaitable(self._redis.delete(key))

    async def try_lock_syncing(self) -> str | None:
        lock_key = CELERY_KEY_PREFIX + "syncing-lock"
        lock_token = str(uuid4())

        lock = self._redis.lock(lock_key, timeout=60 * 30, blocking=False)
        acquired = await lock.acquire(token=lock_token)
        if not acquired:
            return None

        return lock_token
