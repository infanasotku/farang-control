from uuid import UUID

from app.dto.projections import Projection, UpsertProjection
from app.infra.cache.common import KEY_PREFIX, as_awaitable, scan_keys_page
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

        return [Projection.model_validate(v) for v in vals if v]

    async def upsert(self, projection: UpsertProjection) -> None:
        key = PROJECTION_KEY + str(projection.engine_id)

        data = projection.model_dump(exclude={"engine_id"}, mode="json")
        await as_awaitable(self._redis.hset(key, projection.engine_id.hex, mapping=data))

    async def delete(self, engine_id: UUID) -> None:
        key = PROJECTION_KEY + str(engine_id)
        await as_awaitable(self._redis.delete(key))
