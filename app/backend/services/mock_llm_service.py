# 사건 분석 관련 mock 함수 모음 (임시 mock — 추후 llm_service로 교체)

import joblib
from pathlib import Path

# 서버 시작 시 ML 모델 1회 로드
_ML_DIR = Path("app/ai/ml")
_model = joblib.load(_ML_DIR / "model.pkl")
_vectorizer = joblib.load(_ML_DIR / "vectorizer.pkl")

async def ask_followup_questions(case_description: str) -> list[str]:
    """
    사건 설명을 분석하여 추가로 필요한 정보를 질문 목록으로 반환

    예시 데이터 사용 — 추후 LLM 연동하여 동적 반환 필요

    Returns:
        추가 질문 목록. 추가 정보가 필요 없으면 빈 리스트 반환
    """

    # [예시 데이터] 추후 LLM 연동하여 반환 필요
    return [
        "사고 발생 당시 피해자의 상태는 어떠했나요?",
        "가해자와 피해자의 관계는 무엇인가요?",
        "사건 발생 장소 및 시간을 구체적으로 알려주세요."
    ]


async def analyze_case(case_description: str, additional_info: str) -> dict:
    """
    사건 설명과 추가 정보를 분석하여 구조화된 결과 반환

    예시 데이터 사용 — 추후 LLM 연동하여 동적 반환 필요

    Returns:
        AnalysisResult 형식의 dict
    """

    # 사건 설명(최초 입력 + 추가 입력) 텍스트를 벡터로 변환 후 형사/민사 분류
    vector = _vectorizer.transform([case_description + " " + additional_info])
    case_type = _model.predict(vector)[0]

    # [예시 데이터] 추후 LLM 연동하여 반환 필요
    return {
        "case_type": case_type,
        "main_action": "음주운전",
        "victim_exist": True,
        "injury_level": "경미한 부상",
        "evidence": [
            {"type": "CCTV", "description": "사고 현장 CCTV 영상"},
            {"type": "혈중알코올 검사", "description": "혈중알코올농도 0.15% 검사 결과"}
        ]
    }
