# 시뮬레이션 흐름 제어
import uuid

from app.ai.models.state import (
    AgentContext, AgentRole, CaseType, TrialState
)

def init_state(case_text: str, case_type: str) -> TrialState :
    # 0 단계 : 공유 상태 초기화
    return TrialState(
        case_id = str(uuid.uuid4()), 
        case_type = CaseType.CRIMINAL if case_type == "형사" else CaseType.CIVIL,
        case_summary=case_text,
    )

def assign_role(state: TrialState) -> tuple[AgentContext, AgentContext] :
    # 1 단계 : 에이전트 역할 프롬프트 주입
    from app.ai.agents.prosecutor import build_prompt as build_prosecution_prompt
    from app.ai.agents.defense import build_prompt as build_defense_prompt

    # 사건 유형 확인 후, 공격 측 (형사 -> 검사 | 민사 -> 원고 변호사)
    if state.case_type == CaseType.CRIMINAL : 
        attacker_role = AgentRole.PROSECUTOR
    else :
        attacker_role = AgentRole.PLAINTIFF

    # 공격 측 프롬프트 생성
    attacker_context = AgentContext(
        assigned_role = attacker_role,
        role_prompt=build_prosecution_prompt(state.case_summary, attacker_role),
    )

    # 방어 측 프롬프트 생성 
    defender_context = AgentContext(
        assigned_role = AgentRole.DEFENDANT,
        role_prompt=build_defense_prompt(state.case_summary, state.case_type)
    )
    return attacker_context, defender_context

def pre_search(
    state : TrialState,
    attacker_ctx : AgentContext,
    defender_ctx : AgentContext,
) -> None:
    # 2 단계 : 사전 검색
    from app.ai.services.retrieval_service import search_chromadb

    # 공격 측 검색
    attacker_docs = search_chromadb(state.case_summary, attacker_ctx.role_prompt)
    attacker_ctx.retrieved_docs = attacker_docs
    for doc in attacker_docs : 
        state.add_attacker_doc(doc)

    # 방어 측 검색 (공격 측 결과와 분리)
    defender_docs = search_chromadb(state.case_summary, defender_ctx.role_prompt)
    defender_ctx.retrieved_docs = defender_docs
    for doc in defender_docs :
        state.add_defender_doc(doc)

def run_debate(
    state : TrialState,
    attacker_ctx : AgentContext,
    defender_ctx : AgentContext,
) -> None:
    # 3 단계 : 공방 3라운드 진행
    
    # 사건 유형에 따라 공격 측 에이전트 분기
    if state.case_type == CaseType.CRIMINAL :
        from app.ai.agents.prosecutor import argue as attacker_argue, rebut as attacker_rebut
    else :
        from app.ai.agents.plaintiff import argue as attacker_argue, rebut as attacker_rebut

    # 방어 측은 항상 피고 변호사
    from app.ai.agents.lawyer import argue as defender_argue, rebut as defender_rebut

    for round_num in range(state.round_limit) :
        state.current_round = round_num

        # 3-1 공격 측 변론 
        msg = attacker_argue(state, attacker_ctx, round_num)
        state.add_message(msg)

        # 3-2 방어 측 반박
        msg = defender_rebut(state, defender_ctx, round_num)
        state.add_message(msg)

        # 3-3 방어 측 변론
        msg = defender_argue(state, defender_ctx, round_num)
        state.add_message(msg)

        # 3-4 공격 측 반박
        msg = attacker_rebut(state, attacker_ctx, round_num)
        state.add_message(msg)

def run_summarize(state : TrialState) -> None:
    # 4 단계 : 변론 종합
    state.debate_summary = {
        "공격 측_발언" : [
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
            if msg.role in (AgentRole.DEFENSE, AgentRole.DEFENDANT)
        ],
        "인용_출처" : list({ # 전체 발언에서 언급된 출처 중복 제거 후 리스트 변환 
            rule
            for msg in state.messages
            for rule in msg.cited_rules 
        }),
    }

def run_judges(state: TrialState) -> None:
    # 5 단계 : 판사 3인 판결
    from app.ai.agents.judge import judge_principle, judge_equity, judge_public

    state.add_judge_opinion(judge_principle(state)) # 원칙주의 판사
    state.add_judge_opinion(judge_equity(state))    # 형평주의 판사
    state.add_judge_opinion(judge_public(state))     # 여론반영 판사 

def run_master_judge(state: TrialState) -> None:
    # 6 단계 : 마스터 판사 최종 판결
    from app.ai.agents.master_judge import judge_master

    verdict, reasoning, report = judge_master(state)
    state.set_final_decision(verdict, reasoning, report)

def build_response(state: TrialState) -> dict:
    # 7 단계 : FastAPI 응답 변환
    return {
        "case_id" : state.case_id,
        "최종_판결" : state.final_verdict,
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

def run_simulation(case_text: str, case_type: str) -> dict:
    # 전체 시뮬레이션 실행
    state = init_state(case_text, case_type)
    attacker_ctx, defender_ctx = assign_role(state)
    pre_search(state, attacker_ctx, defender_ctx)
    run_debate(state, attacker_ctx, defender_ctx)
    run_summarize(state)
    run_judges(state)
    run_master_judge(state)
    return build_response(state)