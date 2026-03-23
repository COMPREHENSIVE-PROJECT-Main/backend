import asyncio

import httpx

from app.ai.core.config import settings
from app.com.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_INTERVAL = 2


async def call_llm(messages: list[dict], system_prompt: str) -> str:
    full_messages = [{"role": "system", "content": system_prompt}] + list(messages)
    payload = {
        "model": settings.ollama_model,
        "messages": full_messages,
        "stream": False,
    }

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["message"]["content"]
                logger.info(f"Ollama LLM 응답 수신 (attempt={attempt})")
                return content
        except Exception as e:
            logger.warning(f"Ollama 호출 실패 (attempt={attempt}/{_MAX_RETRIES}): {e}")
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_INTERVAL)

    logger.error("Ollama LLM 최종 호출 실패")
    return "AI 응답 생성 중 오류 발생"
