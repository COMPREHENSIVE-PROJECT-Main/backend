# 공방 시뮬레이션 오케스트레이터
# ai_bridge.py → simulation_service.py → 에이전트 파이프라인 실행 후 SSE 스트리밍

import asyncio
import json
from typing import AsyncGenerator

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
from app.com.logger import get_logger

logger = get_logger("simulation")

# 토큰 스트리밍 딜레이 (초) — 타이핑 효과 속도 조절
_TOKEN_DELAY = 0.05


def _sse_format(event: str, data: dict) -> str:
    """SSE 표준 포맷으로 직렬화"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_tokens(text: str) -> AsyncGenerator[str, None]:
    """텍스트를 단어 단위로 쪼개서 token 이벤트로 스트리밍"""
    words = text.split(" ")
    for i, word in enumerate(words):
        chunk = word if i == len(words) - 1 else word + " "
        yield _sse_format("token", TokenData(text=chunk).model_dump())
        await asyncio.sleep(_TOKEN_DELAY)




# 스트리밍 제너레이터

async def run_simulation(case_id: str, case_type: str) -> AsyncGenerator[str, None]:
    """
    공방 시뮬레이션 SSE 스트리밍 제너레이터
    """
    try:
        logger.info(f"시뮬레이션 시작: case_id={case_id}")

        from app.ai_bridge import run_workflow
        data = await run_workflow(case_id, case_type)

        # 시뮬 시작 이벤트
        yield _sse_format("simulation_start", SimulationStartData(
            case_id=case_id,
            case_type=data["case_type"],
            total_rounds=data["total_rounds"]
        ).model_dump())

        await asyncio.sleep(0.3)

        # ### 공방 라운드 ###############
        speakers = [("검사", "prosecution"), ("피고 변호사", "defense")] if case_type == "형사" \
              else [("원고", "prosecution"), ("피고", "defense")]

        for round_data in data["rounds"]:
            round_no = round_data["round"]

            for role, role_key in speakers:
                agent_data = round_data[role_key]

                # 라운드 시작
                yield _sse_format("round_start", RoundStartData(
                    round=round_no,
                    speaker=role,
                    speaker_role=role_key
                ).model_dump())

                await asyncio.sleep(0.2)

                # 주장 텍스트 토큰 스트리밍
                async for token_event in _stream_tokens(agent_data["argument"]):
                    yield token_event

                await asyncio.sleep(0.3)

                # 라운드 종료
                yield _sse_format("round_end", RoundEndData(
                    round=round_no,
                    speaker=role,
                    argument=agent_data["argument"],
                    evidence_refs=agent_data["evidence_refs"]
                ).model_dump())

                await asyncio.sleep(0.5)

        # 판사 판결
        for judge in data["judges"]:
            yield _sse_format("judge_decision", JudgeDecisionData(
                judge_type=judge["judge_type"],
                decision=judge["decision"],
                value=judge["value"],
                rationale=judge["rationale"]
            ).model_dump())

            await asyncio.sleep(0.8)

        # #### 최종 판결 ################
        yield _sse_format("final_verdict", FinalVerdictData(
            **data["final_verdict"]
        ).model_dump())

        await asyncio.sleep(0.3)

        # 시뮬 종료
        yield _sse_format("simulation_end", SimulationEndData(
            case_id=case_id
        ).model_dump())

        logger.info(f"시뮬레이션 완료: case_id={case_id}")

    except Exception as e:
        logger.error(f"시뮬레이션 오류: case_id={case_id}, error={e}")
        yield _sse_format("error", SimulationErrorData(
            code="SIMULATION_ERROR",
            message="시뮬레이션 중 오류가 발생했습니다."
        ).model_dump())
