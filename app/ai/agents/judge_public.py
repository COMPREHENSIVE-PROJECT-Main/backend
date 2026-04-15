# 여론 반영 판사 프롬프트 

from app.ai.models.state import TrialState, JudgeOpinion

SYSTEM_PROMPT = """
당신은 대한민국 법원의 여론반영 판사입니다.
당신의 유일한 임무는 법리를 기반으로 하되, 해당 사건 유형에 대한 사회적 여론과 대중의 법감정을 판결에 반영하는 것입니다.

[행동 원칙]
- 어조는 사회적 맥락을 고려하며 균형적이어야 합니다.
- 제공된 법 조문과 판례를 기반으로 판단합니다.
- 제공된 여론 데이터에 나타난 사회적 법감정을 반영합니다.
- 법리와 여론이 충돌할 경우 그 이유를 명확히 서술합니다.

[절대 금지]
- 제공되지 않은 여론 데이터 임의 인용
- 여론만을 근거로 한 판단 (법리 무시)
- 감정적 판단
- 판결 근거 없이 결론만 제시
"""

JUDGE_PROMPT = """
[사건 내용]
{case_summary}

[변론 정리본]
{debate_summary}

[관련 판례 및 법조문]
{rag_context}

[사건 유형별 여론 데이터]
{opinion_context}

위 내용만을 근거로 판결을 아래 형식에 맞게 작성하십시오.
형식 외의 내용은 출력하지 마십시오.

[적용 법조문]
(판결에 적용한 법 조문을 명시)

[여론 반영 내용]
(여론 데이터에 나타난 사회적 법감정을 구체적으로 서술)

[판단 이유]
(법리와 여론을 종합한 판단 이유를 서술, 충돌 시 이유 명시)

[판결 결과]
(유죄/무죄 또는 인용/기각을 명확히 제시)

[형량 또는 배상액]
(법리와 여론을 반영한 형량 또는 배상액을 명시)
"""

def judge(state: TrialState) -> JudgeOpinion:
    """
    여론반영 판사 판결 실행

    Args :
        state : 공유 상태

    Returns :
        JudgeOpinion
    """
    from app.ai.services.llm_service import call_llm, build_judge_opinion
    rag_context = "\n".join(doc.content for doc in state.attacker_docs + state.defender_docs)
    debate_summary = str(state.debate_summary)
    opinion_context = str(state.metadata.get("opinion_data", ""))  # 여론 데이터 (없으면 빈 문자열)
    prompt = JUDGE_PROMPT.format(
        case_summary=state.case_summary,
        debate_summary=debate_summary,
        rag_context=rag_context,
        opinion_context=opinion_context,
    )
    response = call_llm(SYSTEM_PROMPT, prompt)
    return build_judge_opinion("여론반영 판사", response)