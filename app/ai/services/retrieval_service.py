# 에이전트 공방 시작 전 사전 자료 조사 
# ChromaDB에서 판례/법조문/양형기준을 검색하고 가져오는 파일

from app.ai.models.state import RetrievedDocument, RetrievalCollection
from app.ai.db.vector_db import get_collection 
from app.com.logger import get_logger

logger = get_logger("retrieval_service")

def search_chromadb( 
    case_summary : str, # 사건 설명
    role_prompt : str,  # 역할 프롬프트 (공격/방어 측 입장 반영)
    top_k : int = 5,    # 컬렉션별 최대 검색 결과 수 
) -> list[RetrievedDocument] :
    
    results = []

    # 검색 쿼리 생성 (사건 설명 + 역할 프롬프트)
    query = f"{case_summary}\n{role_prompt}"

    # 컬렉션별 순차 검색 (cases, statutes, sentencing)
    for collection_name in RetrievalCollection :
        try :
            collection = get_collection(collection_name.value)
            search_results = collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            # 검색 결과 파싱
            for i, doc_id in enumerate(search_results["ids"][0]):
                results.append(
                    RetrievedDocument(
                        doc_id = doc_id,
                        collection = collection_name,
                        title = search_results["metadatas"][0][i].get("title", ""),
                        content = search_results["documents"][0][i],
                        score = search_results["distances"][0][i] if "distances" in search_results else None,
                        metadata = search_results["metadatas"][0][i],
                    )
                )
        except Exception as e :
            # 컬렉션 검색 실패 시 로그만 남기고 계속 진행
            logger.warning(f"{collection_name.value} 컬렉션 검색 실패 : {e}")
            continue
    
    return results