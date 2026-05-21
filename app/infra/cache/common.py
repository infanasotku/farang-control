from typing import Awaitable, TypeVar, cast

from redis.asyncio import Redis


class RedisKey(str):
    def __init__(self, value: str):
        super().__init__()
        self.value = value.rstrip(":")

    def __add__(self, other):
        as_str = str(other)
        as_str = as_str.lstrip(":")
        return RedisKey(f"{self}:{as_str}")


KEY_PREFIX = RedisKey("farang")


T = TypeVar("T")


def as_awaitable(value: Awaitable[T] | T) -> Awaitable[T]:
    return cast(Awaitable[T], value)


async def scan_keys_page(
    redis: Redis,
    prefix: str,
    *,
    cursor: int = 0,
    limit: int = 100,
    batch: int = 500,
) -> list[str]:
    result: list[str] = []

    while len(result) < limit:
        next_cursor, keys = await cast(
            Awaitable[tuple[int, list[str]]],
            redis.scan(
                cursor=cursor,
                match=f"{prefix}*",
                count=batch,
            ),
        )

        result.extend(keys)

        cursor = int(next_cursor)

        if cursor == 0:
            break

    return result[:limit]
