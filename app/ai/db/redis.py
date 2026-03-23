import redis.asyncio as aioredis

from app.ai.core.config import settings
from app.com.logger import get_logger

logger = get_logger(__name__)


def get_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def get_cache(key: str) -> str | None:
    try:
        client = get_redis_client()
        value = await client.get(key)
        await client.aclose()
        return value
    except Exception as e:
        logger.error(f"Redis get_cache 실패 (key={key}): {e}")
        return None


async def set_cache(key: str, value: str, expire: int = 3600) -> None:
    try:
        client = get_redis_client()
        await client.set(key, value, ex=expire)
        await client.aclose()
    except Exception as e:
        logger.error(f"Redis set_cache 실패 (key={key}): {e}")


async def delete_cache(key: str) -> None:
    try:
        client = get_redis_client()
        await client.delete(key)
        await client.aclose()
    except Exception as e:
        logger.error(f"Redis delete_cache 실패 (key={key}): {e}")
