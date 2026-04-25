# 형사 사건 검사 프롬프트 

from app.ai.models.state import AgentRole, AgentContext, AgentMessage, TrialState
from app.com.logger import get_logger # 시점 확인을 위한 로그 패키지 

logger = get_logger(__name__)

SEARCH_QUERY = "검사 입장 유죄 입증 관련 판례 법조문"

SYSTEM_PROMPT = """
당신은 대한민국 형사 재판의 검사입니다.
당신의 유일한 임무는 피고인의 유죄를 입증하고 적정 형량을 요청하는 것입니다.

[행동 원칙]
- 어조는 단호하고 논리적이며, 공익적이어야 합니다. 
- 제공한 사건 내용과 판례/법조문만 근거로 사용합니다.
- 사건 내용에 없는 사실은 절대 추가하지 않습니다.
- 사건 내용은 중립적 법률 용어로만 요약하며, 폭력 장면을 생생하게 묘사하지 않습니다.

[절대 금지]
- 피고인에 대한 동정이나 무죄 가능성 언급
- 제공되지 않은 판례/법조문 임의 인용
- 감정적 비난 또는 인신공격
- 증거 없는 주장
- 피고 측에 유리한 진술
- 판결 예측 또는 선고 
- 자극적이거나 선정적인 사건 묘사
"""

INITIAL_ARGUMENT_PROMPT = """
[사건 내용]
{case_summary}

[관련 판례 및 법조문]
{rag_context}

위 내용만을 근거로 초기 변론을 아래 형식에 맞게 작성하십시오.
형식 외의 내용은 출력하지 마십시오.
모든 사건 서술은 법률 문서 스타일의 중립적 표현으로만 작성하십시오.

[핵심 주장]
(피고인의 행위와 죄목을 명확히 서술)

[법적 근거]
(적용 법조문과 판례를 구체적으로 명시)

[요청 형량]
(제공된 양형기준과 검색한 판례, 법조문을 기준으로 형량을 명시하고 가중/감경 요소를 근거로 이유를 서술)
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
모든 사건 서술은 법률 문서 스타일의 중립적 표현으로만 작성하십시오.

[반박 대상]
(현재 라운드까지 피고 변호사의 주장 중 반박할 핵심 내용을 항목별로 나열)

[반박 근거]
(판례 또는 법조문을 근거로 논리적 허점 지적)

[기존 주장 보완]
(초기 주장을 유지하면서 추가로 강화할 논거 서술)
"""


def build_prompt(
        case_summary: str,
        role: AgentRole,
        rag_context: str,
        action: str,
        debate_history: str = None,
) -> str:
    """
    검사 프롬프트 생성

    Args :
        case_summary : 사건 원문
        role : 에이전트 역할 (PROSECUTOR 고정)
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
    검사 변론 실행

    Args :
        state : 공유 상태
        ctx : 검사 에이전트 컨텍스트
        round_num : 현재 라운드 번호

    Returns :
        AgentMessage
    """
    from app.ai.services.llm_service import generate_agent_message
    from app.ai.services.retrieval_service import format_rag_context
    rag_context = format_rag_context(ctx.retrieved_docs)
    prompt = build_prompt(
        case_summary=state.case_summary,
        role=ctx.assigned_role,
        rag_context=rag_context,
        action="변론",
    )
    return generate_agent_message(SYSTEM_PROMPT, prompt, ctx.assigned_role, "검사", round_num, "변론")


def rebut(state: TrialState, ctx: AgentContext, round_num: int) -> AgentMessage:
    """
    검사 반박 실행

    Args :
        state : 공유 상태
        ctx : 검사 에이전트 컨텍스트
        round_num : 현재 라운드 번호

    Returns :
        AgentMessage
    """
    from app.ai.services.llm_service import format_debate_history, generate_agent_message
    from app.ai.services.retrieval_service import format_rag_context
    rag_context = format_rag_context(ctx.retrieved_docs)
    debate_history = format_debate_history(state.messages)
    prompt = build_prompt(
        case_summary=state.case_summary,
        role=ctx.assigned_role,
        rag_context=rag_context,
        action="반박",
        debate_history=debate_history,
    )
    return generate_agent_message(SYSTEM_PROMPT, prompt, ctx.assigned_role, "검사", round_num, "반박")
