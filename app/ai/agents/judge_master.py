# 마스터 판사 프롬프트 

from app.ai.models.state import TrialState

SYSTEM_PROMPT = """
당신은 대한민국 법원의 마스터 판사입니다.
당신의 유일한 임무는 세 판사의 판결을 종합하여 최종 판결과 분석 보고서를 작성하는 것입니다.

[행동 원칙]
- 어조는 명확하고 권위 있어야 합니다.
- 세 판사의 판결을 균형 있게 검토합니다.
- 공통점과 차이점을 분석하여 최종 판결을 도출합니다.
- 일반인이 이해할 수 있도록 판결 이유를 서술합니다.

[절대 금지]
- 세 판사의 판결 내용을 무시한 독자적 판단
- 근거 없는 최종 판결
- 판결 이유 없이 결론만 제시
"""

JUDGE_PROMPT = """
[사건 내용]
{case_summary}

[변론 정리본]
{debate_summary}

[원칙주의 판사 판결]
{judge_principle_result}

[형평주의 판사 판결]
{judge_equity_result}

[여론반영 판사 판결]
{judge_public_result}

위 세 판사의 판결을 종합하여 아래 형식에 맞게 작성하십시오.
형식 외의 내용은 출력하지 마십시오.

[판결 비교 분석]
(세 판결의 공통점과 차이점을 항목별로 분석)

[종합 판단 이유]
(세 판결을 종합한 최종 판단 이유를 일반인이 이해할 수 있도록 서술)

[최종 판결 결과]
(유죄/무죄 또는 인용/기각을 명확히 제시)

[최종 형량 또는 배상액]
(세 판결을 종합한 최종 형량 또는 배상액을 명시)

[종합 분석 보고서]
(사건 전체 흐름, 쟁점, 판결 의미를 일반인 눈높이로 서술)
"""

def judge(state: TrialState) -> tuple[str, str, str, str]:
    """
    마스터 판사 최종 판결 실행

    Args :
        state : 공유 상태

    Returns :
        (verdict, reasoning, report) tuple
    """
    from app.ai.services.llm_service import call_llm, _parse_section
    debate_summary = str(state.debate_summary)
    judge_opinions = {o.judge_name: f"판결: {o.decision}\n형량: {o.sentence or '없음'}\n근거: {o.reasoning}" for o in state.judge_opinions}
    prompt = JUDGE_PROMPT.format(
        case_summary=state.case_summary,
        debate_summary=debate_summary,
        judge_principle_result=judge_opinions.get("원칙주의 판사", ""),
        judge_equity_result=judge_opinions.get("형평주의 판사", ""),
        judge_public_result=judge_opinions.get("여론반영 판사", ""),
    )
    response = call_llm(SYSTEM_PROMPT, prompt)
    verdict   = _parse_section(response, "최종 판결 결과") or response[:100]
    reasoning = _parse_section(response, "종합 판단 이유") or response
    sentence  = _parse_section(response, "최종 형량 또는 배상액") or ""
    report    = _parse_section(response, "종합 분석 보고서") or response
    return verdict, reasoning, report, sentence