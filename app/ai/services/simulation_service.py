# 시뮬레이션 흐름 제어
import uuid

from app.ai.models.state import (
    AgentContext, AgentRole, CaseType, TrialState
)
from app.com.logger import get_logger

logger = get_logger("simulation_service")


def _preview_text(text: str | None, *, limit: int = 120) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _role_label(role: AgentRole) -> str:
    labels = {
        AgentRole.PROSECUTOR: "검사",
        AgentRole.PLAINTIFF: "원고 변호사",
        AgentRole.CRIMINAL_DEFENSE: "피고 변호사",
        AgentRole.CIVIL_DEFENSE: "피고 변호사",
    }
    return labels.get(role, role.value)


def _log_message_result(message) -> None:
    logger.info(
        "공방 메시지 생성: agent=%s, round=%s, position=%s, key_points=%s, cited_rules=%s, summary=%s",
        message.agent_name,
        message.round_number + 1,
        message.position,
        len(message.key_points),
        len(message.cited_rules),
        _preview_text(message.summary),
    )

def init_state(case_text: str, case_type: str, round_limit: int = 3) -> TrialState :
    # 0 단계 : 공유 상태 초기화
    from app.ai.services.retrieval_service import search_opinions
    opinion_data = search_opinions(case_text)

    state = TrialState(
        case_id = str(uuid.uuid4()),
        case_type = CaseType.CRIMINAL if case_type == "형사" else CaseType.CIVIL,
        case_summary=case_text,
        round_limit=round_limit,
        metadata={
            "opinion_data": opinion_data,
        },
    )
    logger.info(
        "0단계 공유 상태 초기화 완료: case_id=%s, case_type=%s, round_limit=%s, summary_chars=%s",
        state.case_id,
        state.case_type.value,
        state.round_limit,
        len(case_text),
    )
    return state

def assign_role(state: TrialState) -> tuple[AgentContext, AgentContext] :
    # 1 단계 : 에이전트 역할 배정 + 역할 프롬프트 주입
    logger.info("1단계 에이전트 역할 배정 시작: case_id=%s, case_type=%s", state.case_id, state.case_type.value)

    # 사건 유형 확인 후, 공격 측 (형사 -> 검사 | 민사 -> 원고 변호사)
    if state.case_type == CaseType.CRIMINAL :
        from app.ai.agents.prosecutor import SYSTEM_PROMPT as attacker_prompt
        attacker_role = AgentRole.PROSECUTOR
    else :
        from app.ai.agents.plaintiff import SYSTEM_PROMPT as attacker_prompt
        attacker_role = AgentRole.PLAINTIFF

    # 방어 측 (형사 -> 형사 피고 변호사 | 민사 -> 민사 피고 변호사)
    if state.case_type == CaseType.CRIMINAL :
        from app.ai.agents.criminal_defense import SYSTEM_PROMPT as defender_prompt
        defender_role = AgentRole.CRIMINAL_DEFENSE
    else :
        from app.ai.agents.civil_defense import SYSTEM_PROMPT as defender_prompt
        defender_role = AgentRole.CIVIL_DEFENSE

    # 공격 측 역할 배정
    attacker_context = AgentContext(
        assigned_role = attacker_role,
        role_prompt = attacker_prompt,
    )

    # 방어 측 역할 배정
    defender_context = AgentContext(
        assigned_role = defender_role,
        role_prompt = defender_prompt,
    )
    logger.info(
        "1단계 에이전트 역할 배정 완료: attacker=%s, defender=%s",
        _role_label(attacker_role),
        _role_label(defender_role),
    )
    return attacker_context, defender_context

def pre_search(
    state : TrialState,
    attacker_ctx : AgentContext,
    defender_ctx : AgentContext,
) -> None:
    # 2 단계 : 사전 검색
    from app.ai.services.retrieval_service import search_chromadb
    logger.info("2단계 사전 검색 시작: case_id=%s", state.case_id)

    # 공격 측 역할별 검색 쿼리 import
    if state.case_type == CaseType.CRIMINAL:
        from app.ai.agents.prosecutor import SEARCH_QUERY as attacker_query
    else:
        from app.ai.agents.plaintiff import SEARCH_QUERY as attacker_query

    # 방어 측 역할별 검색 쿼리 import
    if state.case_type == CaseType.CRIMINAL:
        from app.ai.agents.criminal_defense import SEARCH_QUERY as defender_query
    else:
        from app.ai.agents.civil_defense import SEARCH_QUERY as defender_query

    # 공격 측 변론에 사용할 판례/법조문 사전 검색
    attacker_docs = search_chromadb(state.case_summary, attacker_query)
    attacker_ctx.retrieved_docs = attacker_docs
    for doc in attacker_docs :
        state.add_attacker_doc(doc)
    logger.info(
        "2단계 공격측 검색 완료: role=%s, docs=%s",
        _role_label(attacker_ctx.assigned_role),
        len(attacker_docs),
    )

    # 방어 측 검색 (공격 측 결과와 분리)
    defender_docs = search_chromadb(state.case_summary, defender_query)
    defender_ctx.retrieved_docs = defender_docs
    for doc in defender_docs :
        state.add_defender_doc(doc)
    logger.info(
        "2단계 방어측 검색 완료: role=%s, docs=%s",
        _role_label(defender_ctx.assigned_role),
        len(defender_docs),
    )
    logger.info(
        "2단계 사전 검색 종료: attacker_docs=%s, defender_docs=%s",
        len(state.attacker_docs),
        len(state.defender_docs),
    )

def run_debate(
    state : TrialState,
    attacker_ctx : AgentContext,
    defender_ctx : AgentContext,
) -> None:
    # 3 단계 : 공방 3라운드 진행
    logger.info("3단계 공방 시작: case_id=%s, round_limit=%s", state.case_id, state.round_limit)
    
    # 사건 유형에 따라 공격 측 에이전트 분기
    if state.case_type == CaseType.CRIMINAL :
        from app.ai.agents.prosecutor import argue as attacker_argue, rebut as attacker_rebut # 검사
    else :
        from app.ai.agents.plaintiff import argue as attacker_argue, rebut as attacker_rebut # 원고 변호사 

    # 사건 유형에 따라 방어 측 에이전트 분기
    if state.case_type == CaseType.CRIMINAL:
        from app.ai.agents.criminal_defense import argue as defender_argue, rebut as defender_rebut # 형사 사건 피고 변호사
    else:
        from app.ai.agents.civil_defense import argue as defender_argue, rebut as defender_rebut # 민사 사건 피고 변호사

    for round_num in range(state.round_limit) :
        state.current_round = round_num
        logger.info("3단계 라운드 시작: round=%s/%s", round_num + 1, state.round_limit)

        # 3-1 공격 측 변론 
        msg = attacker_argue(state, attacker_ctx, round_num)
        state.add_message(msg)
        _log_message_result(msg)

        # 3-2 방어 측 반박
        msg = defender_rebut(state, defender_ctx, round_num)
        state.add_message(msg)
        _log_message_result(msg)

        # 3-3 방어 측 변론
        msg = defender_argue(state, defender_ctx, round_num)
        state.add_message(msg)
        _log_message_result(msg)

        # 3-4 공격 측 반박
        msg = attacker_rebut(state, attacker_ctx, round_num)
        state.add_message(msg)
        _log_message_result(msg)
        logger.info(
            "3단계 라운드 종료: round=%s/%s, total_messages=%s",
            round_num + 1,
            state.round_limit,
            len(state.messages),
        )
    logger.info("3단계 공방 종료: total_messages=%s", len(state.messages))

def run_summarize(state : TrialState) -> None:
    # 4 단계 : 변론 종합
    logger.info("4단계 변론 종합 시작: case_id=%s, messages=%s", state.case_id, len(state.messages))
    state.debate_summary = {
        "공격측_발언" : [
            {
                "라운드" : msg.round_number,
                "유형" : msg.position, # 변론 or 반박
                "내용" : msg.content,
                "인용_출처" : msg.cited_rules,
            }
            for msg in state.messages
            if msg.role in (AgentRole.PROSECUTOR, AgentRole.PLAINTIFF)
        ],
        "방어측_발언" : [
            {
                "라운드" : msg.round_number,
                "유형" : msg.position, # 변론 or 반박
                "내용" : msg.content,
                "인용_출처" : msg.cited_rules,
            }
            for msg in state.messages
            if msg.role in (AgentRole.CRIMINAL_DEFENSE, AgentRole.CIVIL_DEFENSE)
        ],
        "인용_출처" : list({ # 전체 발언에서 언급된 출처 중복 제거 후 리스트 변환 
            rule
            for msg in state.messages
            for rule in msg.cited_rules 
        }),
    }
    logger.info(
        "4단계 변론 종합 완료: attacker_messages=%s, defender_messages=%s, unique_citations=%s",
        len(state.debate_summary["공격측_발언"]),
        len(state.debate_summary["방어측_발언"]),
        len(state.debate_summary["인용_출처"]),
    )

def run_judges(state: TrialState) -> None:
    # 5 단계 : 판사 3인 판결
    from app.ai.agents.judge_principle import judge as judge_principle
    from app.ai.agents.judge_equity import judge as judge_equity
    from app.ai.agents.judge_public import judge as judge_public
    logger.info("5단계 판사 3인 판결 시작: case_id=%s", state.case_id)

    for opinion in (judge_principle(state), judge_equity(state), judge_public(state)):
        state.add_judge_opinion(opinion)
        logger.info(
            "5단계 판사 의견 완료: judge=%s, decision=%s, sentence=%s, summary=%s",
            opinion.judge_name,
            opinion.decision,
            opinion.sentence,
            _preview_text(opinion.opinion_summary),
        )
    logger.info("5단계 판사 3인 판결 종료: opinions=%s", len(state.judge_opinions))

def run_master_judge(state: TrialState) -> None:
    # 6 단계 : 마스터 판사 최종 판결
    from app.ai.agents.judge_master import judge as judge_master
    logger.info("6단계 마스터 판사 최종 판결 시작: case_id=%s", state.case_id)

    verdict, reasoning, report, sentence = judge_master(state)
    state.set_final_decision(verdict, reasoning, report, sentence)
    logger.info(
        "6단계 마스터 판결 완료: verdict=%s, sentence=%s, reasoning=%s",
        verdict,
        sentence,
        _preview_text(reasoning),
    )

def build_response(state: TrialState) -> dict:
    # 7 단계 : FastAPI 응답 변환
    response = {
        "case_id" : state.case_id,
        "최종_판결" : state.final_verdict,
        "최종_형량" : state.final_sentence,
        "판결_근거" : state.final_reasoning,
        "판사별_비교" : {
            opinion.judge_name : {
                "판결" : opinion.decision,
                "형량_또는_배상액" : opinion.sentence,
                "근거" : opinion.reasoning,
            }
            for opinion in state.judge_opinions
        },
        "공방_기록" : [
            {
                "에이전트" : msg.agent_name,
                "라운드" : msg.round_number,
                "유형" : msg.position,
                "내용" : msg.content,
                "인용_출처" : msg.cited_rules,
            }
            for msg in state.messages
        ],
        "종합_분석_리포트" : state.final_report,
    }
    logger.info(
        "7단계 응답 변환 완료: case_id=%s, verdict=%s, judges=%s, rounds=%s",
        state.case_id,
        state.final_verdict,
        len(state.judge_opinions),
        state.round_limit,
    )
    return response

def run_simulation(case_text: str, case_type: str, round_limit: int = 3) -> dict:
    # 전체 시뮬레이션 실행
    logger.info(
        "시뮬레이션 시작: case_type=%s, round_limit=%s, case_summary=%s",
        case_type,
        round_limit,
        _preview_text(case_text),
    )
    state = init_state(case_text, case_type, round_limit=round_limit)
    attacker_ctx, defender_ctx = assign_role(state)
    pre_search(state, attacker_ctx, defender_ctx)
    run_debate(state, attacker_ctx, defender_ctx)
    run_summarize(state)
    run_judges(state)
    run_master_judge(state)
    response = build_response(state)
    logger.info(
        "시뮬레이션 종료: case_id=%s, final_verdict=%s, final_sentence=%s",
        state.case_id,
        state.final_verdict,
        state.final_sentence,
    )
    return response
