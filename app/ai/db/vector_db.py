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


def get_collection(name: str = "precedents"): # 테스트 완료 후, Azure GPT-4o 버전으로 변경
    client = _get_client()
    try:
        ollama_ef = embedding_functions.OllamaEmbeddingFunction(
            url=f"{settings.ollama_base_url}/api/embeddings",
            model_name=settings.ollama_embed_model,
        )
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=ollama_ef,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
                "hnsw:M": 16,
            },
        )
        logger.info(f"컬렉션 획득: {name} (embedding_model={settings.ollama_embed_model})")
        return collection
    except Exception as e:
        logger.error(f"컬렉션 생성/획득 실패: {e}")
        raise
