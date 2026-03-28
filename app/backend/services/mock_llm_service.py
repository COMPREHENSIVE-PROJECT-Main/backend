# 사건 설명 분석 후 추가 질문 생성 (임시 mock — 추후 llm_service로 교체)


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
