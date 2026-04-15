# 민사 사건 원고 변호사 프롬프트 

from app.ai.models.state import AgentRole, AgentContext, AgentMessage, TrialState

SEARCH_QUERY = "원고 변호사 입장 손해배상 청구 관련 판례 법조문"

SYSTEM_PROMPT = """
당신은 대한민국 민사 재판의 원고 변호사입니다.
당신의 유일한 임무는 원고의 청구를 인용시키고 최대한의 손해배상을 이끌어내는 것입니다.

[행동 원칙]
- 어조는 설득적이며 의뢰인의 피해를 강조해야 합니다.
- 제공한 사건 내용과 판례/법조문만 근거로 사용합니다.
- 사건 내용에 없는 사실은 절대 추가하지 않습니다.

[절대 금지]
- 사실 왜곡 또는 없는 피해 주장
- 청구 포기 또는 배상액 축소 발언
- 피고 입장 대변 또는 피고에게 유리한 진술
- 원고의 손해배상을 깎는 행위
- 원고에게 불리한 진술
- 판결 예측 또는 선고
"""

INITIAL_ARGUMENT_PROMPT = """
[사건 내용]
{case_summary}

[관련 판례 및 법조문]
{rag_context}

위 내용만을 근거로 초기 변론을 아래 형식에 맞게 작성하십시오.
형식 외의 내용은 출력하지 마십시오.

[핵심 주장]
(피고의 행위로 인한 원고의 피해를 명확히 서술)

[법적 근거]
(적용 민법 조문과 판례를 구체적으로 명시)

[청구 내용]
(제공된 판례와 손해액 산정 기준을 근거로 청구 금액을 명시하고 산정 이유를 서술)
"""

REBUTTAL_PROMPT = """
[사건 내용]
{case_summary}

[이전 발언 내역]
{debate_history}

[관련 판례 및 법조문]
{rag_context}

현재 라운드까지 피고 변호사의 발언에 대해 반박 대상으로 삼아 형식에 맞게 작성하십시오.
형식 외의 내용은 출력하지 마십시오.

[반박 대상]
(현재 라운드까지 피고 변호사의 주장 중 반박할 핵심 내용을 항목별로 나열)

[반박 근거]
(판례 또는 민법 조문을 근거로 논리적 허점 지적)

[청구 유지]
(초기 청구를 유지하면서 원고 피해를 추가로 강화할 논거 서술)
"""


def build_prompt(
        case_summary: str,
        role: AgentRole,
        rag_context: str,
        action: str,
        debate_history: str = None,
) -> str:
    """
    민사 사건 원고 변호사 프롬프트 생성

    Args :
        case_summary : 사건 원문
        role : 에이전트 역할 (PLAINTIFF 고정)
        rag_context : ChromaDB에서 조회한 사건 관련 판례/법조문
        action : 현재 수행할 행동 ("변론" 또는 "반박")
        debate_history : 이전 발언 내역

    Returns :
        완성된 프롬프트 문자열
    """
    if action == "반박":
        return REBUTTAL_PROMPT.format(
            case_summary=case_summary,
            rag_context=rag_context,
            debate_history=debate_history,
        )
    return INITIAL_ARGUMENT_PROMPT.format(
        case_summary=case_summary,
        rag_context=rag_context,
    )


def argue(state: TrialState, ctx: AgentContext, round_num: int) -> AgentMessage:
    """
    민사 사건 원고 변호사 변론 실행

    Args :
        state : 공유 상태
        ctx : 민사 사건 원고 변호사 에이전트 컨텍스트
        round_num : 현재 라운드 번호

    Returns :
        AgentMessage
    """
    from app.ai.services.llm_service import call_llm, build_agent_message
    rag_context = "\n".join(doc.content for doc in ctx.retrieved_docs)
    prompt = build_prompt(
        case_summary=state.case_summary,
        role=ctx.assigned_role,
        rag_context=rag_context,
        action="변론",
    )
    response = call_llm(SYSTEM_PROMPT, prompt)
    return build_agent_message(ctx.assigned_role, "원고 변호사", round_num, "변론", response)


def rebut(state: TrialState, ctx: AgentContext, round_num: int) -> AgentMessage:
    """
    민사 사건 원고 변호사 반박 실행

    Args :
        state : 공유 상태
        ctx : 민사 사건 원고 변호사 에이전트 컨텍스트
        round_num : 현재 라운드 번호

    Returns :
        AgentMessage
    """
    from app.ai.services.llm_service import call_llm, build_agent_message
    rag_context = "\n".join(doc.content for doc in ctx.retrieved_docs)
    debate_history = "\n".join(msg.content or "" for msg in state.messages)
    prompt = build_prompt(
        case_summary=state.case_summary,
        role=ctx.assigned_role,
        rag_context=rag_context,
        action="반박",
        debate_history=debate_history,
    )
    response = call_llm(SYSTEM_PROMPT, prompt)
    return build_agent_message(ctx.assigned_role, "원고 변호사", round_num, "반박", response)