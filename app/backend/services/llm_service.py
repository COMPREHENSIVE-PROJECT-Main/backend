# 사건 분석 LLM 서비스 (AI 파트 call_llm 연동)

import json
from pathlib import Path

import joblib

_ML_DIR = Path("app/ai/ml")
_model = joblib.load(_ML_DIR / "model.pkl")
_vectorizer = joblib.load(_ML_DIR / "vectorizer.pkl")


async def ask_followup_questions(case_description: str) -> list[str]:
    """
    사건 설명에서 누락된 핵심 정보를 파악하여 꼭 필요한 추가 질문만 반환.
    정보가 충분하면 빈 리스트 반환 가능.
    """
    from app.ai.services.llm_service import call_llm

    system_prompt = (
        "당신은 법률 AI 재판 시뮬레이션 시스템의 사건 분석 전문가입니다.\n"
        "시뮬레이션에는 다음 정보가 필요합니다: 사건 경위, 당사자 관계, 피해 여부 및 정도, 증거, 행위 시점과 장소.\n"
        "사건 설명에서 이미 파악된 정보는 다시 묻지 말고, 진짜 누락된 핵심 정보에 대해서만 질문을 생성하세요.\n"
        "정보가 충분하면 questions를 빈 배열로 반환하세요.\n"
        "응답은 반드시 JSON 형식으로만 반환하세요."
    )
    user_prompt = (
        f"다음 사건 설명을 읽고, 법률 시뮬레이션에 필요하지만 누락된 정보에 대해서만 질문을 생성하세요.\n\n"
        f"사건 설명:\n{case_description}\n\n"
        f'JSON 형식으로 반환하세요: {{"questions": ["질문1", "질문2"]}}'
    )

    response = call_llm(system_prompt, user_prompt, json_mode=True)
    data = json.loads(response)
    return data.get("questions", [])


async def analyze_case(case_description: str, additional_info: str) -> dict:
    """
    사건 설명과 추가 정보를 분석하여 구조화된 결과 반환.
    사건 유형(case_type)은 ML 모델로 분류, 나머지는 LLM으로 분석.
    """
    from app.ai.services.llm_service import call_llm

    # ML 모델로 사건 유형 분류
    full_text = case_description + " " + additional_info
    vector = _vectorizer.transform([full_text])
    case_type = _model.predict(vector)[0]

    system_prompt = (
        "당신은 법률 사건 분석 전문가입니다.\n"
        "사건 설명과 추가 정보를 바탕으로 주요 행위, 피해자 존재 여부, 피해 정도, 증거 목록을 추출하세요.\n"
        "응답은 반드시 JSON 형식으로만 반환하세요."
    )
    user_prompt = (
        f"다음 사건 설명과 추가 정보를 분석하세요.\n\n"
        f"사건 설명:\n{case_description}\n\n"
        f"추가 정보:\n{additional_info}\n\n"
        "아래 JSON 형식으로만 반환하세요:\n"
        '{"main_action": "주요 행위 (예: 음주운전)", '
        '"victim_exist": true, '
        '"injury_level": "피해 정도 (예: 경미한 부상, 사망, 없음)", '
        '"evidence": [{"type": "증거 유형", "description": "설명"}]}'
    )

    response = call_llm(system_prompt, user_prompt, json_mode=True)
    data = json.loads(response)

    return {
        "case_type": case_type,
        "main_action": data.get("main_action", ""),
        "victim_exist": bool(data.get("victim_exist", False)),
        "injury_level": data.get("injury_level", ""),
        "evidence": data.get("evidence", []),
    }
