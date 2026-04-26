# 공방 시뮬레이션 오케스트레이터
# ai_bridge.py → simulation_service.py → 에이전트 파이프라인 실행 후 SSE 스트리밍

import asyncio
import json
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.backend.schemas.simulation_schema import (
    FinalVerdictData,
    JudgeDecisionData,
    RoundEndData,
    RoundStartData,
    SimulationEndData,
    SimulationErrorData,
    SimulationStartData,
    TokenData,
)
from app.backend.services.simulation_service import (
    append_judge,
    append_round,
    create_simulation,
    mark_failed,
    save_final_verdict,
)
from app.com.logger import get_logger

logger = get_logger("simulation")

_TOKEN_DELAY = 0.05


def _sse_format(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_tokens(text: str) -> AsyncGenerator[str, None]:
    words = text.split(" ")
    for i, word in enumerate(words):
        chunk = word if i == len(words) - 1 else word + " "
        yield _sse_format("token", TokenData(text=chunk).model_dump())
        await asyncio.sleep(_TOKEN_DELAY)


### 스트리밍 제너레이터 ###

async def run_simulation(
    case_id: str,
    case_type: str,
    user_id: int,
    db: Session,
    start_from_round: int = 1,
) -> AsyncGenerator[str, None]:
    """
    공방 시뮬레이션 SSE 스트리밍 제너레이터

    Args:
        case_id: 시뮬레이션할 사건 ID
        case_type: "형사" | "민사"
        user_id: 요청 유저 ID (DB 저장용)
        db: DB 세션
        start_from_round: 재개할 라운드 번호 (기본 1 = 처음부터)
    """
    current_round = 0
    simulation_id = None

    try:
        logger.info(f"시뮬레이션 시작: case_id={case_id}, case_type={case_type}, start_from_round={start_from_round}")

        simulation = create_simulation(db=db, case_id=case_id, user_id=user_id)
        simulation_id = simulation.id

        from app.ai_bridge import run_workflow
        data = await run_workflow(case_id, case_type)

        yield _sse_format("simulation_start", SimulationStartData(
            case_id=case_id,
            case_type=data["case_type"],
            total_rounds=data["total_rounds"]
        ).model_dump())

        await asyncio.sleep(0.3)

        # 형사/민사에 따른 화자 설정
        speakers = [("검사", "prosecution"), ("변호인", "defense")] if case_type == "형사" \
              else [("원고", "prosecution"), ("피고", "defense")]

        for round_data in data["rounds"]:
            round_no = round_data["round"]
            current_round = round_no

            if round_no < start_from_round:
                continue

            for role, role_key in speakers:
                agent_data = round_data[role_key]

                yield _sse_format("round_start", RoundStartData(
                    round=round_no,
                    speaker=role,
                    speaker_role=role_key
                ).model_dump())

                await asyncio.sleep(0.2)

                async for token_event in _stream_tokens(agent_data["argument"]):
                    yield token_event

                await asyncio.sleep(0.3)

                round_end_data = RoundEndData(
                    round=round_no,
                    speaker=role,
                    argument=agent_data["argument"],
                    evidence_refs=agent_data["evidence_refs"]
                )

                yield _sse_format("round_end", round_end_data.model_dump())

                append_round(db=db, simulation_id=simulation_id, round_data=round_end_data.model_dump())

                await asyncio.sleep(0.5)

        for judge in data["judges"]:
            judge_data = JudgeDecisionData(
                judge_type=judge["judge_type"],
                decision=judge["decision"],
                value=judge["value"],
                rationale=judge["rationale"]
            )

            yield _sse_format("judge_decision", judge_data.model_dump())

            append_judge(db=db, simulation_id=simulation_id, judge_data=judge_data.model_dump())

            await asyncio.sleep(0.8)

        verdict_data = FinalVerdictData(**data["final_verdict"])
        yield _sse_format("final_verdict", verdict_data.model_dump())

        save_final_verdict(db=db, simulation_id=simulation_id, verdict_data=verdict_data.model_dump())

        await asyncio.sleep(0.3)

        yield _sse_format("simulation_end", SimulationEndData(
            case_id=case_id
        ).model_dump())

        logger.info(f"시뮬레이션 완료: case_id={case_id}, simulation_id={simulation_id}")

    except Exception as e:
        logger.error(f"시뮬레이션 오류: case_id={case_id}, round={current_round}, error={e}")

        if simulation_id:
            mark_failed(db=db, simulation_id=simulation_id)

        yield _sse_format("error", SimulationErrorData(
            code="SIMULATION_ERROR",
            message="시뮬레이션 중 오류가 발생했습니다.",
            failed_at_round=current_round
        ).model_dump())
