import asyncio

import httpx

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_INTERVAL = 2


async def embed_text(text: str) -> list[float]:
    payload = {
        "model": settings.ollama_embedding_model,
        "prompt": text,
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                embedding = data["embedding"]
                logger.info(f"임베딩 수신 완료: dim={len(embedding)} (attempt={attempt})")
                return embedding
        except Exception as e:
            logger.warning(f"임베딩 호출 실패 (attempt={attempt}/{_MAX_RETRIES}): {e}")
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_INTERVAL)

    logger.error("임베딩 최종 호출 실패, 빈 리스트 반환")
    return []
