from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Sequence

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.com.logger import get_logger

logger = get_logger(__name__)

DEFAULT_COLLECTIONS: tuple[str, ...] = ("cases", "statutes", "sentencing")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    llm_mode: str = "azure"
    llm_timeout_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices("LLM_TIMEOUT_SECONDS", "llm_timeout_seconds"),
    )
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("OPENAI_EMBEDDING_MODEL", "openai_embedding_model"),
    )
    azure_openai_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_ENDPOINT", "azure_openai_endpoint"),
    )
    azure_openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AZURE_OPENAI_API_KEY", "azure_openai_api_key"),
    )
    azure_openai_api_version: str = Field(
        default="2024-12-01-preview",
        validation_alias=AliasChoices("AZURE_OPENAI_API_VERSION", "azure_openai_api_version"),
    )
    azure_openai_deployment_name: str = Field(
        default="",
        validation_alias=AliasChoices(
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
            "azure_openai_deployment_name",
        ),
    )
    chroma_path: str = "./chroma_db"
    redis_url: str = "redis://localhost:6379"
    embedding_dim: int = 768
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "lawdb"

    @field_validator(
        "openai_api_key",
        "openai_embedding_model",
        "azure_openai_endpoint",
        "azure_openai_api_key",
        "azure_openai_api_version",
        "azure_openai_deployment_name",
        mode="before",
    )
    @classmethod
    def _strip_string_values(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def embedding_model_name(self) -> str:
        return self.openai_embedding_model

    @property
    def chat_model_name(self) -> str:
        return self.azure_openai_deployment_name

    @property
    def normalized_azure_openai_endpoint(self) -> str:
        return self.azure_openai_endpoint.rstrip("/")


settings = Settings()


@dataclass
class RuntimeStatus:
    embedding_model: str
    redis_ready: bool
    vector_collections: list[str]


def _validate_settings() -> None:
    if settings.embedding_dim <= 0:
        raise ValueError("embedding_dim must be greater than 0")

    if settings.llm_timeout_seconds <= 0:
        raise ValueError("llm_timeout_seconds must be greater than 0")

    if not settings.openai_api_key:
        raise ValueError("openai_api_key must be configured")
    if not settings.openai_embedding_model:
        raise ValueError("openai_embedding_model must be configured")
    if not settings.azure_openai_endpoint:
        raise ValueError("azure_openai_endpoint must be configured")
    if not settings.azure_openai_api_key:
        raise ValueError("azure_openai_api_key must be configured")
    if not settings.azure_openai_api_version:
        raise ValueError("azure_openai_api_version must be configured")
    if not settings.azure_openai_deployment_name:
        raise ValueError("azure_openai_deployment_name must be configured")

def _warm_embedding_runtime() -> None:
    importlib.import_module("chromadb.utils.embedding_functions")
    logger.info(
        f"Embedding runtime ready (provider=openai, model={settings.embedding_model_name})"
    )


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
        embedding_model=settings.embedding_model_name,
        redis_ready=redis_ready,
        vector_collections=ready_collections,
    )
