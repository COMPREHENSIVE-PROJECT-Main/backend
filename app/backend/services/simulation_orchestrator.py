# 공방 시뮬레이션 오케스트레이터
# 현재: mock 데이터로 SSE 스트리밍
# AI파트 완료 후: ai_bridge.py 호출로 교체 예정

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


# mock 데이터 
# [임시] AI파트 ai_bridge.py 연동 완료 시 아래 mock 데이터 및
# _get_mock_simulation_data() 함수 전체를 교체한다.

def _get_mock_simulation_data(case_id: str) -> dict:
    """
    mock 시뮬레이션 데이터 반환

    AI파트 연동 시 이 함수를 ai_bridge.py 호출로 교체:
        from app.ai_bridge import run_workflow
        result = await run_workflow(case_id)
    """
    return {
        "case_type": "형사",
        "total_rounds": 3,
        "rounds": [
            {
                "round": 1,
                "prosecution": {
                    "argument": "피고인은 혈중알코올농도 0.15% 상태로 차량을 운전하여 피해자 차량을 추돌하였습니다. 현장 CCTV와 혈중알코올 검사 결과가 이를 명백히 입증합니다.",
                    "evidence_refs": ["도로교통법 제44조 제1항", "교통사고처리특례법 제3조"]
                },
                "defense": {
                    "argument": "피고인은 음주 후 대리운전을 요청하였으나 대리운전 기사가 오지 않아 부득이하게 운전하게 된 사정이 있습니다. 또한 피해자 차량의 급정거가 사고의 직접적 원인임을 주장합니다.",
                    "evidence_refs": ["형법 제20조 (정당행위)", "국립과학수사연구원 감정서"]
                }
            },
            {
                "round": 2,
                "prosecution": {
                    "argument": "피고인의 주장과 달리 블랙박스 영상에는 피해자 차량의 급정거 사실이 확인되지 않습니다. 피고인의 과실이 전적으로 인정됩니다.",
                    "evidence_refs": ["블랙박스 영상 분석 보고서", "사고 재현 감정 결과"]
                },
                "defense": {
                    "argument": "피고인은 초범이며 사고 직후 피해자를 즉시 구호하고 신고하였습니다. 피해자와 합의가 이루어진 점을 고려하여 선처를 요청합니다.",
                    "evidence_refs": ["합의서", "피해자 탄원서", "피고인 초범 증명서"]
                }
            },
            {
                "round": 3,
                "prosecution": {
                    "argument": "음주운전 재발 방지를 위한 사회적 경고가 필요합니다. 피해자는 2주간 치료가 필요한 부상을 입었으며, 엄중한 처벌이 마땅합니다.",
                    "evidence_refs": ["진단서 (치료기간 2주)", "음주운전 통계자료"]
                },
                "defense": {
                    "argument": "피고인은 깊이 반성하고 있으며 재발 방지를 위해 음주운전 예방 교육을 이수하였습니다. 실형보다는 집행유예가 적절하다고 사료됩니다.",
                    "evidence_refs": ["음주운전 예방 교육 이수증", "반성문", "직장 재직 증명서"]
                }
            }
        ],
        "judges": [
            {
                "judge_type": "원칙판사",
                "decision": "유죄",
                "value": "징역 24개월",
                "rationale": "혈중알코올농도 0.15%는 면허취소 기준을 크게 상회하며, 실질적 피해가 발생하였으므로 법정 기준에 따라 처벌한다."
            },
            {
                "judge_type": "형평판사",
                "decision": "유죄",
                "value": "징역 12개월 집행유예 2년",
                "rationale": "초범, 피해자와의 합의, 즉각적 구호 조치를 고려하면 실형보다 집행유예가 형평에 맞다."
            },
            {
                "judge_type": "여론판사",
                "decision": "유죄",
                "value": "징역 18개월",
                "rationale": "음주운전에 대한 사회적 경각심이 높은 시점에서 솜방망이 처벌은 여론의 신뢰를 저해한다."
            }
        ],
        "final_verdict": {
            "decision": "유죄",
            "value": "징역 12개월 집행유예 2년",
            "order": "피고인을 징역 1년에 처한다. 다만 이 판결 확정일로부터 2년간 위 형의 집행을 유예한다.",
            "rationale": "피고인이 음주운전으로 타인에게 상해를 입힌 사실은 인정되나, 초범이고 피해자와 합의한 점, 즉시 구호 조치를 취한 점을 감안하여 집행유예를 선고한다.",
            "conclusion": "음주운전의 위험성을 인지하고 있었음에도 운전한 과실은 중하나, 제반 정상을 고려하여 집행유예로 선고한다."
        }
    }


# 스트리밍 제너레이터

async def run_simulation(case_id: str) -> AsyncGenerator[str, None]:
    """
    공방 시뮬레이션 SSE 스트리밍 제너레이터

    현재는 mock 데이터를 사용하며,
    AI파트 완료 후 _get_mock_simulation_data()를 ai_bridge.py 호출로 교체한다.
    """
    try:
        logger.info(f"시뮬레이션 시작: case_id={case_id}")

        # [임시 mock] AI파트 연동 시 아래 한 줄을 ai_bridge 호출로 교체
        data = _get_mock_simulation_data(case_id)

        # 시뮬 시작 이벤트
        yield _sse_format("simulation_start", SimulationStartData(
            case_id=case_id,
            case_type=data["case_type"],
            total_rounds=data["total_rounds"]
        ).model_dump())

        await asyncio.sleep(0.3)

        # ### 공방 라운드 ###############
        for round_data in data["rounds"]:
            round_no = round_data["round"]

            for role, role_key in [("검사", "prosecution"), ("변호인", "defense")]:
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
