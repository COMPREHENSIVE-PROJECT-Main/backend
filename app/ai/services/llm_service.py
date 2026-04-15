# LLM 호출 및 응답 파싱 공용 유틸리티

import re
import logging
import requests
from app.ai.models.state import AgentMessage, AgentRole, JudgeOpinion
from app.ai.core.runtime import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model

# LLM 호출
def call_llm(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "options": {"num_ctx": 2048},  # gemma3:4b 최대값으로 명시
        "messages": [
            {"role" : "system", "content" : system_prompt},
            {"role" : "user", "content" : user_prompt},
        ],
        "stream" : False,
    }
    try :
        resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except requests.RequestException as e :
        logger.error("Ollama 호출 실패 ; %s", e)
        raise RuntimeError(f"LLM 호출 오류 : {e}") from e
    
# 파싱 헬퍼 (텍스트에서 필요한 부분만 잘라내는 함수)

def _parse_section(text : str, header : str) -> str:
    # [header] 세션 내용 추출. 다음 [섹션] 또는 끝까지
    match = re.search(rf"\[{re.escape(header)}\]\s*(.*?)(?=\n\[|\Z)", text, re.S)
    return match.group(1).strip() if match else "" 

def _parse_list(text : str, header : str) -> list[str] :
    # 섹션 내용을 줄 단위 리스트로 반환. '- ', '1. ' 등 접두사 제거
    raw = _parse_section(text, header)
    result = []
    for line in raw.splitlines() :
        line = re.sub(r"^[\-\*\d]+[\.\)]\s*", "", line).strip()
        if line :
            result.append(line)
    return result 

# 공방 에이전트들의 변론/반박을 반환하는 결과물 
"""
# LLM 프롬프트가 아래 형식으로 출력하도록 지시해야 합니다:

   [핵심 주장]
   주장 내용...

   [법적 근거]
   - 형법 제OO조
   - 판례 XXXX

   [변론 내용]
   전체 변론 텍스트...
"""

def build_agent_message(
    role : AgentRole,
    agent_name : str,
    round_num : int,
    position : str,
    response : str,
) -> AgentMessage :
    # 변론/반박에 따라 파싱할 섹션 헤더가 다름
    if position == "반박":
        key_points  = _parse_list(response, "반박 대상")
        cited_rules = _parse_list(response, "반박 근거")
    else:
        key_points  = _parse_list(response, "핵심 주장")
        cited_rules = _parse_list(response, "법적 근거")
    content = response

    return AgentMessage(
       role         = role,           # 에이전트 역할 (AgentRole enum)
       agent_name   = agent_name,     # 화면에 표시될 이름 (예: "검사")
       round_number = round_num,      # 현재 라운드 번호
       position     = position,       # "변론" or "반박"
       summary      = response[:200], # 변론/반박 본문 앞 200자 요약 목록/카드 미리보기용
       content      = content,        # 변론/반박 전체 본문
       key_points   = key_points,     # 핵심 주장 또는 반박 대상 목록
       cited_rules  = cited_rules,    # 인용한 판례/법조문 목록
    )

# 판사 에이전트들이 판단을 마치고 반환하는 결과물 
"""
   LLM 프롬프트가 아래 형식으로 출력하도록 지시해야 합니다:

   [판결 결과]
   유죄 / 무죄 / 인용 / 기각

   [판단 이유]
   이유 텍스트...

   [형량]
   징역 OO년 (없으면 생략 가능)
"""

def build_judge_opinion(
    judge_name : str,
    response : str,
) -> JudgeOpinion :
    decision  = _parse_section(response, "판결 결과") or response[:100]
    reasoning = _parse_section(response, "판단 이유") or response
    sentence  = _parse_section(response, "형량 또는 배상액") or None
    cited_rules = _parse_list(response, "적용 법조문")

    return JudgeOpinion(
        judge_name      = judge_name,     # 판사 이름
        opinion_summary = response[:200], # LLM 응답 전체 앞 200자 요약 목록/카드 미리보기용
        decision        = decision,       # 판결 결과 (유죄|무죄|인용|기각)
        reasoning       = reasoning,      # 판단 이유
        sentence        = sentence,       # 형량 또는 배상액
        cited_rules     = cited_rules,    # 적용 판례/법조문 
    )