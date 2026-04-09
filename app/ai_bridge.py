# 백엔드 simulation_orchestrator.py와 AI 파트 simulation_service.py를 연결

import asyncio
import json
from collections import defaultdict
from pathlib import Path

from app.com.logger import get_logger

logger = get_logger("ai_bridge")


def _load_case_json(case_id: str) -> dict :
    # case_id로 JSON 파일에서 사건 정보 조회
    case_path = Path(f"data/input_cases/{case_id}.json")

    if not case_path.exists():
        raise FileNotFoundError(f"사건 파일을 찾을 수 없습니다: {case_path}")

    with open(case_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _classify_case_type(description: str) -> str:
    # ML 분류기로 사건 유형 판별 (형사/민사)
    from app.ai.ml.classifier import classify

    result = classify(description)
    logger.info(f"사건 유형 분류 결과: {result}")
    return result


def _map_judge_name(judge_name: str) -> str:
    # judge_name → judge_type 변환
    mapping = {
        "원칙주의": "원칙판사",
        "형평주의": "형평판사",
        "여론반영": "여론판사",
    }
    return mapping.get(judge_name, judge_name)


def _map_rounds(messages: list) -> list:
    # 공방_기록 평탄화 리스트 → orchestrator가 기대하는 중첩 구조로 변환
    # run_debate 순서: attacker_argue(0), defender_rebut(1), defender_argue(2), attacker_rebut(3)
    rounds_dict = defaultdict(list)
    for msg in messages:
        round_num = msg.get("라운드", 0) + 1  # 0-indexed → 1-indexed
        rounds_dict[round_num].append(msg)

    rounds = []
    for round_num in sorted(rounds_dict.keys()):
        msgs = rounds_dict[round_num]
        prosecution_msg = msgs[0] if len(msgs) > 0 else {}
        defense_msg     = msgs[2] if len(msgs) > 2 else (msgs[1] if len(msgs) > 1 else {})

        rounds.append({
            "round": round_num,
            "prosecution": {
                "argument":     prosecution_msg.get("내용", "") or "",
                "evidence_refs": prosecution_msg.get("인용_출처", []),
            },
            "defense": {
                "argument":     defense_msg.get("내용", "") or "",
                "evidence_refs": defense_msg.get("인용_출처", []),
            },
        })

    return rounds


def _map_to_schema(simulation_result: dict, case_type: str) -> dict:
    # build_response() 결과를 simulation_schema 형식으로 변환

    # 판사별 판결 변환 (JudgeDecisionData)
    judges = []
    for judge_name, opinion in simulation_result.get("판사별_비교", {}).items():
        judges.append({
            "judge_type": _map_judge_name(judge_name),   # "원칙판사" | "형평판사" | "여론판사"
            "decision": opinion.get("판결", ""),          # "유죄" | "무죄" | "인용" | "기각"
            "value": opinion.get("형량_또는_배상액", ""),  # "징역 24개월" | "70%" 등
            "rationale": opinion.get("근거", ""),          # 판결 근거
        })

    # 최종 판결 변환 (FinalVerdictData)
    final_verdict = {
        "decision": simulation_result.get("최종_판결", ""),       # "유죄" | "무죄" | "인용" | "기각"
        "value": "",                                               # TODO: 마스터 판사 프롬프트 완성 후 채워짐
        "order": "",                                               # TODO: 마스터 판사 프롬프트 완성 후 채워짐
        "rationale": simulation_result.get("판결_근거", ""),       # 판결 이유
        "conclusion": simulation_result.get("종합_분석_리포트", "")[:200],  # 200자 이내
    }

    return {
        "case_type":    case_type,
        "total_rounds": 3,
        "rounds":       _map_rounds(simulation_result.get("공방_기록", [])),
        "judges":       judges,
        "final_verdict": final_verdict,
    }


async def run_workflow(case_id: str) -> dict:
    """
    simulation_orchestrator.py에서 호출하는 메인 함수
    1. case_id → JSON 파일에서 사건 정보 조회
    2. ML 분류기로 사건 유형 판별
    3. simulation_service.run_simulation() 호출 (sync → asyncio.to_thread로 실행)
    4. 반환값을 simulation_schema 형식으로 변환
    """
    from app.ai.services.simulation_service import run_simulation

    logger.info(f"시뮬레이션 시작 — case_id: {case_id}")

    # 1. JSON 파일에서 사건 정보 조회
    case_data = _load_case_json(case_id)
    description = case_data.get("description", "")

    if not description:
        raise ValueError(f"사건 설명이 없습니다: {case_id}")

    # 2. ML 분류기로 사건 유형 판별
    case_type = _classify_case_type(description)

    # 3. 시뮬레이션 실행 (sync 함수를 스레드풀에서 실행)
    logger.info(f"시뮬레이션 실행 — case_type: {case_type}")
    simulation_result = await asyncio.to_thread(run_simulation, description, case_type)

    # 4. simulation_schema 형식으로 변환
    mapped_result = _map_to_schema(simulation_result, case_type)
    logger.info(f"시뮬레이션 완료 — case_id: {case_id}")

    return mapped_result
