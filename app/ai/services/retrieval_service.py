# 에이전트 공방 시작 전 사전 자료 조사 
# ChromaDB에서 판례/법조문/양형기준을 검색하고 가져오는 파일

from app.ai.models.state import RetrievedDocument, RetrievalCollection
from app.ai.db.vector_db import get_collection 
from app.com.logger import get_logger

logger = get_logger("retrieval_service")


class RetrievalError(RuntimeError):
    """Raised when legal-material retrieval cannot provide usable context."""


def _preview_titles(documents: list[RetrievedDocument], *, limit: int = 3) -> str:
    titles = [doc.title or doc.doc_id for doc in documents[:limit]]
    return ", ".join(titles)


def _metadata_title(metadata: dict) -> str:
    for key in ("title", "case_name", "law_name", "article_title", "crime_type", "sub_type"):
        value = metadata.get(key)
        if value:
            return str(value)
    return ""


def format_rag_context(
    documents: list[RetrievedDocument],
    *,
    max_docs: int = 6,
    max_chars: int = 6000,
    per_doc_chars: int = 900,
) -> str:
    parts: list[str] = []
    used = 0

    for index, doc in enumerate(documents[:max_docs], start=1):
        title = doc.title or doc.doc_id
        content = doc.content.strip()
        if len(content) > per_doc_chars:
            content = content[:per_doc_chars].rstrip() + "..."

        rendered = f"[근거 {index}] collection={doc.collection.value}, title={title}\n{content}"
        if used + len(rendered) > max_chars:
            break
        parts.append(rendered)
        used += len(rendered)

    return "\n\n".join(parts)


def search_chromadb(
    case_summary : str, # 사건 설명
    role_query : str,   # 역할별 검색 쿼리 (공격/방어 측 입장 반영)
    top_k : int = 5,    # 컬렉션별 최대 검색 결과 수
) -> list[RetrievedDocument] :

    results = []
    failures: list[str] = []

    # 검색 쿼리 생성 (사건 설명 + 역할별 검색 쿼리)
    query = f"{case_summary}\n{role_query}"
    logger.info(
        "Chroma 검색 시작: role_query_chars=%s, case_summary_chars=%s, top_k=%s",
        len(role_query),
        len(case_summary),
        top_k,
    )

    # 컬렉션별 순차 검색 (cases, statutes, sentencing)
    for collection_name in RetrievalCollection :
        try :
            collection = get_collection(collection_name.value)
            search_results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            ids = search_results.get("ids", [[]])[0]
            documents = search_results.get("documents", [[]])[0]
            metadatas = search_results.get("metadatas", [[]])[0]
            distances = search_results.get("distances", [[]])[0]
            logger.info(
                "Chroma 검색 완료: collection=%s, hits=%s",
                collection_name.value,
                len(ids),
            )

            # 검색 결과 파싱
            for i, doc_id in enumerate(ids):
                metadata = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
                results.append(
                    RetrievedDocument(
                        doc_id = doc_id,
                        collection = collection_name,
                        title = _metadata_title(metadata),
                        content = documents[i] if i < len(documents) else "",
                        score = distances[i] if i < len(distances) else None,
                        metadata = metadata,
                    )
                )
        except Exception as e :
            failures.append(f"{collection_name.value}: {e}")
            logger.warning(f"{collection_name.value} 컬렉션 검색 실패 : {e}")
            continue

    if not results:
        failure_detail = "; ".join(failures) if failures else "검색 결과가 0건입니다."
        raise RetrievalError(f"법률 근거 검색 실패: {failure_detail}")

    logger.info(
        "Chroma 검색 요약: total_hits=%s, preview_titles=%s",
        len(results),
        _preview_titles(results),
    )

    return results


_OPINION_FALLBACK = (
    "제공된 별도 여론 데이터가 없습니다. "
    "여론을 임의로 추정하지 말고 법리와 기록 중심으로 판단하십시오."
)


def search_opinions(case_summary: str, top_k: int = 10) -> str:
    """
    사건 내용과 유사한 여론 기사를 opinion 컬렉션에서 검색하고
    sentiment_score를 집계하여 judge_public 프롬프트용 문자열로 반환.
    """
    from app.ai.db.vector_db import get_opinion_collection

    try:
        collection = get_opinion_collection()
        results = collection.query(
            query_texts=[case_summary],
            n_results=top_k,
            include=["metadatas"],
        )

        metadatas = results.get("metadatas", [[]])[0]
        if not metadatas:
            logger.warning("Opinion 검색 결과 없음")
            return _OPINION_FALLBACK

        scores = [float(m.get("sentiment_score", 0.0)) for m in metadatas]
        total = len(scores)
        avg_score = sum(scores) / total
        pos_count = sum(1 for s in scores if s > 0)
        neg_count = total - pos_count

        logger.info(
            "Opinion 검색 완료: total=%s, avg_score=%.4f, pos=%s, neg=%s",
            total, avg_score, pos_count, neg_count,
        )

        return (
            f"- 분석 기사: {total}건\n"
            f"- 평균 감성 점수: {avg_score:.2f}\n"
            f"- 부정 여론: {neg_count}건 ({neg_count * 100 // total}%)\n"
            f"- 긍정 여론: {pos_count}건 ({pos_count * 100 // total}%)"
        )

    except Exception as e:
        logger.warning("Opinion 검색 실패, 폴백 사용: %s", e)
        return _OPINION_FALLBACK
