import chromadb
from chromadb.utils import embedding_functions
from threading import Lock
from typing import Any

from app.ai.core.runtime import settings
from app.com.logger import get_logger

logger = get_logger(__name__)

_client: Any = None
_client_lock = Lock()


def _get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                try:
                    _client = chromadb.PersistentClient(
                        path=settings.chroma_path,
                    )
                    logger.info(f"ChromaDB 로컬 연결 성공: {settings.chroma_path}")
                except Exception as e:
                    logger.error(f"ChromaDB 연결 실패: {e}")
                    raise
    return _client


def _get_embedding_function():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embedding_model,
    )


def _get_hf_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="jhgan/ko-sroberta-multitask",
    )


def get_collection(name: str = "precedents"):
    client = _get_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=_get_embedding_function(),
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
                "hnsw:M": 16,
            },
        )
        logger.info(
            f"컬렉션 획득: {name} "
            f"(embedding_provider=openai, "
            f"embedding_model={settings.embedding_model_name})"
        )
        return collection
    except Exception as e:
        logger.error(f"컬렉션 생성/획득 실패: {e}")
        raise


def get_opinion_collection(name: str = "opinion"):
    client = _get_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=_get_hf_embedding_function(),
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
                "hnsw:M": 16,
            },
        )
        logger.info(f"Opinion 컬렉션 획득: {name} (embedding=jhgan/ko-sroberta-multitask)")
        return collection
    except Exception as e:
        logger.error(f"Opinion 컬렉션 생성/획득 실패: {e}")
        raise
