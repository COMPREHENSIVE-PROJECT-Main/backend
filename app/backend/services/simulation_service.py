# 시뮬레이션 DB CRUD
from sqlalchemy.orm import Session

from app.backend.models.simulation import Simulation
from app.com.logger import get_logger

logger = get_logger("simulation_service")


def create_simulation(db: Session, case_id: str, user_id: int) -> Simulation:
    """시뮬레이션 레코드 생성 (시뮬 시작 시 호출)"""
    simulation = Simulation(
        case_id=case_id,
        user_id=user_id,
        status="in_progress",
        rounds=[],
        judges=[],
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    logger.info(f"시뮬레이션 생성: id={simulation.id}, case_id={case_id}")
    return simulation


def append_round(db: Session, simulation_id: int, round_data: dict) -> None:
    """라운드 완료 시 결과 추가"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        return

    # JSONB append (새 리스트로 교체해야 SQLAlchemy가 변경 감지)
    updated = list(simulation.rounds) + [round_data]
    simulation.rounds = updated
    db.commit()


def append_judge(db: Session, simulation_id: int, judge_data: dict) -> None:
    """판사 판결 완료 시 결과 추가"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        return

    updated = list(simulation.judges) + [judge_data]
    simulation.judges = updated
    db.commit()


def save_final_verdict(db: Session, simulation_id: int, verdict_data: dict) -> None:
    """최종 판결 저장 + 상태 completed로 변경"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        return

    simulation.final_verdict = verdict_data
    simulation.status = "completed"
    db.commit()
    logger.info(f"시뮬레이션 완료: id={simulation_id}")


def mark_failed(db: Session, simulation_id: int) -> None:
    """에러 발생 시 상태 failed로 변경"""
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        return

    simulation.status = "failed"
    db.commit()


def get_simulation(db: Session, case_id: str, user_id: int) -> Simulation | None:
    """case_id + user_id로 가장 최근 시뮬레이션 조회"""
    return (
        db.query(Simulation)
        .filter(
            Simulation.case_id == case_id,
            Simulation.user_id == user_id,
        )
        .order_by(Simulation.created_at.desc())
        .first()
    )
