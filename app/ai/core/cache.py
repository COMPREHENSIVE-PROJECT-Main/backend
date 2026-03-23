import hashlib
import json

from app.ai.db.redis import get_cache, set_cache
from app.com.logger import get_logger

logger = get_logger(__name__)


def make_cache_key(messages: list[dict], system_prompt: str) -> str:
    payload = json.dumps({"messages": messages, "system_prompt": system_prompt}, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode()).hexdigest()


async def get_llm_cache(prompt_hash: str) -> str | None:
    return await get_cache(f"llm:{prompt_hash}")


async def set_llm_cache(prompt_hash: str, response: str, expire: int = 3600) -> None:
    await set_cache(f"llm:{prompt_hash}", response, expire=expire)
