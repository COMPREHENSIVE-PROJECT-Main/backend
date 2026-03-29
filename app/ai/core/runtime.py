from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Sequence

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.com.logger import get_logger

logger = get_logger(__name__)

DEFAULT_COLLECTIONS: tuple[str, ...] = ("cases", "statutes", "sentencing")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    llm_mode: str = "test"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    chroma_path: str = "./chroma_db"
    redis_url: str = "redis://localhost:6379"
    embedding_dim: int = 768
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "lawdb"


settings = Settings()


@dataclass
class RuntimeStatus:
    embedding_model: str
    redis_ready: bool
    vector_collections: list[str]


def _validate_settings() -> None:
    if settings.embedding_dim <= 0:
        raise ValueError("embedding_dim must be greater than 0")

    if not settings.ollama_model:
        raise ValueError("ollama_model must be configured")

    if not settings.openai_api_key:
        raise ValueError("openai_api_key must be configured")

    if not settings.openai_embedding_model:
        raise ValueError("openai_embedding_model must be configured")

def _warm_embedding_runtime() -> None:
    importlib.import_module("chromadb.utils.embedding_functions")
    logger.info(f"Embedding runtime ready (model={settings.openai_embedding_model})")


def _warm_vector_db(collection_names: Sequence[str]) -> list[str]:
    from app.ai.db.vector_db import get_collection

    ready_collections: list[str] = []
    for name in collection_names:
        get_collection(name)
        ready_collections.append(name)
    logger.info(f"Vector DB runtime ready (collections={ready_collections})")
    return ready_collections


async def _warm_redis() -> bool:
    from app.ai.db.redis import get_redis_client

    client = get_redis_client()
    try:
        await client.ping()
        logger.info("Redis runtime ready")
        return True
    finally:
        await client.aclose()


async def initialize_runtime(
    collection_names: Sequence[str] | None = None,
) -> RuntimeStatus:
    _validate_settings()
    _warm_embedding_runtime()
    ready_collections = _warm_vector_db(collection_names or DEFAULT_COLLECTIONS)
    redis_ready = await _warm_redis()

    return RuntimeStatus(
        embedding_model=settings.openai_embedding_model,
        redis_ready=redis_ready,
        vector_collections=ready_collections,
    )
