# 공방 요약 서비스
# 라운드별 공방 로그 → 요약 텍스트 생성
#
# [AI 연동 교체 포인트]
# 현재: rounds_raw에서 argument를 그대로 잘라서 요약으로 사용 (mock)
# AI파트 완료 후: _summarize_argument()를 llm_factory 기반 LLM 호출로 교체

from app.backend.schemas.summary_schema import DebateSummary, RoundSummary
from app.com.logger import get_logger

logger = get_logger("summary_refine_service")


def _summarize_argument(argument: str) -> str:
    """
    주장 텍스트 요약

    [임시 mock] AI파트 완료 후 아래 로직을 LLM 호출로 교체:
        from app.core.llm_factory import get_llm_service
        llm = get_llm_service()
        return await llm.call_llm(messages=[...], system_prompt="공방 내용을 2문장으로 요약하세요.")
    """
    # mock: 앞 80자 + "..." 로 요약 대체
    return argument[:80] + "..." if len(argument) > 80 else argument


def _extract_key_issues(rounds_raw: list[dict]) -> list[str]:
    """
    핵심 쟁점 추출

    [임시 mock] AI파트 완료 후 LLM 호출로 교체 예정
    현재는 각 라운드에서 첫 번째 evidence_ref를 쟁점으로 대체
    """
    issues = []
    for r in rounds_raw:
        for role_key in ["prosecution", "defense"]:
            refs = r.get(role_key, {}).get("evidence_refs", [])
            if refs and refs[0] not in issues:
                issues.append(refs[0])
    return issues[:5]  # 상위 5개


def build_debate_summary(case_id: str, case_type: str, rounds_raw: list[dict]) -> DebateSummary:
    """
    DB에서 꺼낸 rounds JSON → 공방 요약 생성

    AI파트 연동 후 _summarize_argument(), _extract_key_issues() 교체만 하면 됨.
    이 함수 자체는 변경 불필요.
    """
    role_map = {
        "prosecution": "검사" if case_type == "형사" else "원고",
        "defense": "변호인" if case_type == "형사" else "피고",
    }

    round_summaries = []
    for round_data in rounds_raw:
        round_no = round_data.get("round", 0)
        for role_key, speaker in role_map.items():
            agent = round_data.get(role_key, {})
            argument = agent.get("argument", "")
            law_refs = agent.get("evidence_refs", [])

            round_summaries.append(RoundSummary(
                round_no=round_no,
                speaker=speaker,
                content=_summarize_argument(argument),
                law_refs=law_refs,
            ))

    key_issues = _extract_key_issues(rounds_raw)

    return DebateSummary(
        case_id=case_id,
        case_type=case_type,
        rounds=round_summaries,
        key_issues=key_issues,
    )
