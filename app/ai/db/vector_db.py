import chromadb

from app.ai.core.config import settings
from app.com.logger import get_logger

logger = get_logger(__name__)

_client: chromadb.HttpClient | None = None


def _get_client() -> chromadb.HttpClient:
    global _client
    if _client is None:
        try:
            _client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
            logger.info(f"ChromaDB 연결 성공: {settings.chroma_host}:{settings.chroma_port}")
        except Exception as e:
            logger.error(f"ChromaDB 연결 실패: {e}")
            raise
    return _client


def get_collection(name: str = "precedents"):
    client = _get_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100,
                "hnsw:M": 16,
            },
        )
        logger.info(f"컬렉션 획득: {name}")
        return collection
    except Exception as e:
        logger.error(f"컬렉션 생성/획득 실패: {e}")
        raise
