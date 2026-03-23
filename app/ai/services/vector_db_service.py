from app.ai.db.vector_db import get_collection
from app.com.logger import get_logger

logger = get_logger(__name__)


async def insert_vectors(documents: list[dict]) -> int:
    collection = get_collection()
    try:
        ids = [doc["id"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        docs = [doc["document"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=metadatas,
        )
        logger.info(f"벡터 삽입 완료: {len(ids)}건")
        return len(ids)
    except Exception as e:
        logger.error(f"벡터 삽입 실패: {e}")
        raise


async def search_vectors(
    query_embedding: list[float],
    top_n: int = 5,
    where: dict | None = None,
) -> list[dict]:
    collection = get_collection()
    try:
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_n,
            "include": ["documents", "distances", "metadatas"],
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        output = []
        for doc_id, content, score, meta in zip(ids, documents, distances, metadatas):
            output.append({
                "document_id": doc_id,
                "content": content,
                "score": score,
                "metadata": meta or {},
            })

        logger.info(f"벡터 검색 완료: {len(output)}건 반환")
        return output
    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        raise


async def delete_vectors(document_ids: list[str]) -> bool:
    collection = get_collection()
    try:
        collection.delete(ids=document_ids)
        logger.info(f"벡터 삭제 완료: {len(document_ids)}건")
        return True
    except Exception as e:
        logger.error(f"벡터 삭제 실패: {e}")
        return False
