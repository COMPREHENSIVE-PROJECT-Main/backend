# 공방 시뮬레이션 엔드포인트
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.backend.models.user import User
from app.backend.schemas.simulation_schema import SimulationStartRequest
from app.backend.services.simulation_orchestrator import run_simulation
from app.backend.utils.dependencies import get_current_user
from app.com.logger import get_logger

logger = get_logger("simulation")

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post(
    "/start",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "SSE 스트림",
            "content": {"text/event-stream": {"example": "event: simulation_start\ndata: {\"case_id\": \"case_0001\", \"case_type\": \"형사\", \"total_rounds\": 3}\n\n"}},
        }
    },
)
async def start_simulation(
    request: SimulationStartRequest,
    current_user: User = Depends(get_current_user)
):
    """
    SSE(text/event-stream) 스트림 반환. Swagger에서 실시간 확인 불가, fetch API로 연동.

    이벤트 순서:
    simulation_start → [round_start → token(반복) → round_end] × N → judge_decision(×3) → final_verdict → simulation_end

    각 이벤트 data 구조:
    - simulation_start: { case_id, case_type, total_rounds }
    - round_start: { round, speaker, speaker_role }
    - token: { text }
    - round_end: { round, speaker, argument, evidence_refs }
    - judge_decision: { judge_type, decision, value, rationale }
    - final_verdict: { decision, value, order, rationale, conclusion }
    - simulation_end: { case_id, message }
    - error: { code, message }
    """
    logger.info(f"시뮬레이션 요청: user_id={current_user.id}, case_id={request.case_id}")

    return StreamingResponse(
        run_simulation(case_id=request.case_id, case_type=request.case_type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx 버퍼링 비활성화
        }
    )
"""
시뮬 확인 curl
curl -N -X POST http://localhost:8080/api/simulation/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 복붙" \
  -d '{"case_id": "case_0001", "case_type": "형사"}'
"""