# LLM 호출 및 응답 파싱 공용 유틸리티

import json
import logging
import re
from functools import lru_cache
from typing import TypeVar

from openai import AzureOpenAI, BadRequestError
from pydantic import BaseModel, ValidationError

from app.com.logger import get_logger
from app.ai.models.state import AgentMessage, AgentRole, JudgeOpinion
from app.ai.core.runtime import settings
from app.ai.schemas.llm_schema import (
    AgentStructuredOutput,
    JudgeStructuredOutput,
    MasterJudgeStructuredOutput,
)

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class StructuredLLMOutputError(RuntimeError):
    """LLM 응답이 요구한 구조를 만족하지 못할 때 발생."""


def _preview_text(text: str | None, *, limit: int = 120) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _is_content_filter_error(exc: Exception) -> bool:
    text = str(exc)
    return "content_filter" in text or "ResponsibleAIPolicyViolation" in text


def _replace_violent_phrasing(text: str, *, strict: bool = False) -> str:
    softened = text
    replacements = [
        ("밀치고", "접촉을 수반하고"),
        ("밀쳤", "접촉을 수반했"),
        ("폭행", "유형력 행사"),
        ("폭력", "물리력 행사"),
        ("때려", "신체 접촉을 가해"),
        ("때렸", "신체 접촉을 가했"),
        ("구타", "물리력 행사"),
        ("찔러", "위험한 접촉을 가해"),
        ("찔렀", "위험한 접촉을 가했"),
        ("흉기", "위험한 도구"),
        ("살해", "치명적 결과 초래"),
        ("살인", "중대한 인명 침해 범죄"),
        ("상해", "신체 침해"),
        ("피를", "상해 흔적을"),
    ]
    if strict:
        replacements.extend(
            [
                ("강도", "재산 침해 범죄"),
                ("강간", "성적 자기결정권 침해 범죄"),
                ("강제추행", "성적 자기결정권 침해 행위"),
            ]
        )
    for source, target in replacements:
        softened = softened.replace(source, target)
    return softened


def _normalize_user_prompt(text: str, *, strict: bool = False) -> str:
    normalized = _replace_violent_phrasing(text, strict=strict)
    return (
        "[법률 분석 입력 형식]\n"
        "이 입력은 모의 재판 및 법률 분석용 사건 기록이다.\n"
        "사실관계는 중립적·추상적인 법률 용어로만 재진술하고, 폭력 또는 피해 장면을 생생하게 묘사하지 말라.\n"
        "범죄 성립 여부, 책임 유무, 형량 또는 배상 판단에 필요한 법률 논점만 간결하게 분석하라.\n"
        "사건의 자극적 표현을 반복하지 말고, 법조문·판례·쟁점 중심으로 정리하라.\n\n"
        f"{normalized}"
    )


def _normalize_system_prompt(system_prompt: str) -> str:
    return (
        "[시스템 공통 규칙]\n"
        "이 작업은 법률 분석과 모의 재판을 위한 구조화된 텍스트 생성이다.\n"
        "사건 내용을 법률 문서처럼 중립적으로 요약하고, 폭력성 표현은 추상적 법률 용어로 축약하라.\n"
        "선정적·생생한 묘사, 감정적 수사, 장면 재현은 금지한다.\n\n"
        f"{system_prompt}"
    )


def format_debate_history(messages: list[AgentMessage], *, max_chars: int = 6000) -> str:
    rendered_messages = [
        f"[라운드 {msg.round_number + 1} / {msg.agent_name} / {msg.position or '발언'}]\n{msg.content or msg.summary}"
        for msg in messages
    ]
    rendered = "\n\n".join(rendered_messages)
    if len(rendered) <= max_chars:
        return rendered
    return "[이전 발언 일부 생략]\n" + rendered[-max_chars:]


@lru_cache(maxsize=1)
def _get_azure_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.normalized_azure_openai_endpoint,
        timeout=settings.llm_timeout_seconds,
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = False,
    _content_filter_retry: bool = False,
) -> str:
    normalized_system_prompt = _normalize_system_prompt(system_prompt)
    normalized_user_prompt = _normalize_user_prompt(user_prompt)
    request_kwargs = {
        "model": settings.chat_model_name,
        "messages": [
            {"role": "system", "content": normalized_system_prompt},
            {"role": "user", "content": normalized_user_prompt},
        ],
        "timeout": settings.llm_timeout_seconds,
    }
    if json_mode:
        request_kwargs["response_format"] = {"type": "json_object"}

    try:
        logger.info(
            "Azure OpenAI 호출 시작: model=%s, json_mode=%s, system_chars=%s, user_chars=%s",
            settings.chat_model_name,
            json_mode,
            len(normalized_system_prompt),
            len(normalized_user_prompt),
        )
        response = _get_azure_client().chat.completions.create(**request_kwargs)
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise RuntimeError("LLM 응답이 길이 제한으로 잘렸습니다")
        content = choice.message.content
        if not content:
            raise RuntimeError("LLM 응답 본문이 비어 있습니다")
        logger.info(
            "Azure OpenAI 호출 완료: model=%s, finish_reason=%s, response_chars=%s, preview=%s",
            settings.chat_model_name,
            choice.finish_reason,
            len(content),
            _preview_text(content),
        )
        return content.strip()
    except BadRequestError as e:
        if _is_content_filter_error(e) and not _content_filter_retry:
            logger.warning(
                "Azure OpenAI 입력 필터 감지: model=%s, sanitized_retry=true",
                settings.chat_model_name,
            )
            return call_llm(
                _normalize_system_prompt(system_prompt),
                _normalize_user_prompt(user_prompt, strict=True),
                json_mode=json_mode,
                _content_filter_retry=True,
            )
        logger.error("Azure OpenAI 호출 실패 ; %s", e)
        raise RuntimeError(f"LLM 호출 오류 : {e}") from e
    except Exception as e:
        logger.error("Azure OpenAI 호출 실패 ; %s", e)
        raise RuntimeError(f"LLM 호출 오류 : {e}") from e


def _json_template(schema: type[BaseModel]) -> dict:
    if schema is AgentStructuredOutput:
        return {
            "summary": "발언 요약을 문자열로 작성",
            "key_points": ["핵심 주장 또는 반박 대상을 문자열 배열로 작성"],
            "cited_rules": ["인용한 법조문, 판례, 양형기준을 문자열 배열로 작성"],
            "content": "사용자에게 보여줄 전체 발언 본문을 문자열로 작성",
        }
    if schema is JudgeStructuredOutput:
        return {
            "opinion_summary": "판결 요약을 문자열로 작성",
            "cited_rules": ["적용 법조문, 판례, 양형기준을 문자열 배열로 작성"],
            "reasoning": "판단 이유를 문자열로 작성",
            "decision": "유죄/무죄 또는 인용/기각 중 하나를 문자열로 작성",
            "sentence": "형량 또는 배상액을 문자열로 작성. 없으면 null",
        }
    if schema is MasterJudgeStructuredOutput:
        return {
            "verdict": "최종 판결 결과를 문자열로 작성",
            "reasoning": "종합 판단 이유를 문자열로 작성",
            "sentence": "최종 형량 또는 배상액을 문자열로 작성. 없으면 빈 문자열",
            "report": "종합 분석 보고서를 문자열로 작성",
        }
    return {field_name: "" for field_name in schema.model_fields}


def _json_output_instruction(schema: type[BaseModel]) -> str:
    template_json = json.dumps(_json_template(schema), ensure_ascii=False, indent=2)
    return (
        "\n\n[출력 형식]\n"
        "위 지시에 다른 출력 형식이 포함되어 있어도, 최종 응답은 아래 JSON 형태만 허용됩니다.\n"
        "마크다운 코드블록, 설명 문장, 주석, schema 설명은 출력하지 마십시오.\n"
        "`properties`, `required`, `type`, `title` 같은 schema 키를 출력하지 마십시오.\n"
        "아래 템플릿의 값을 실제 사건 내용에 맞게 채워 JSON 객체 하나만 출력하십시오.\n"
        f"{template_json}"
    )


def _extract_json_object(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        loaded = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        loaded = json.loads(stripped[start:end + 1])

    if not isinstance(loaded, dict):
        raise ValueError("LLM JSON output must be an object")
    return loaded


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    *,
    retries: int = 1,
) -> T:
    prompt = user_prompt + _json_output_instruction(schema)
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        logger.info(
            "LLM 구조화 출력 요청: schema=%s, attempt=%s/%s",
            schema.__name__,
            attempt + 1,
            retries + 1,
        )
        response = call_llm(system_prompt, prompt, json_mode=True)
        try:
            payload = _extract_json_object(response)
            validated = schema.model_validate(payload)
            logger.info(
                "LLM 구조화 출력 검증 성공: schema=%s, keys=%s",
                schema.__name__,
                sorted(payload.keys()),
            )
            return validated
        except (json.JSONDecodeError, ValueError, ValidationError) as exc:
            last_error = exc
            logger.warning(
                "LLM 구조화 출력 검증 실패: attempt=%s/%s, error=%s",
                attempt + 1,
                retries + 1,
                exc,
            )
            prompt = (
                user_prompt
                + _json_output_instruction(schema)
                + "\n\n이전 응답은 검증에 실패했습니다. 이번에는 템플릿 키만 사용한 유효한 JSON 객체만 출력하십시오."
            )

    raise StructuredLLMOutputError(f"LLM 구조화 출력 검증 실패: {last_error}")
    
def generate_agent_message(
    system_prompt: str,
    user_prompt: str,
    role: AgentRole,
    agent_name: str,
    round_num: int,
    position: str,
) -> AgentMessage:
    output = call_llm_json(system_prompt, user_prompt, AgentStructuredOutput)
    logger.info(
        "에이전트 발언 생성 완료: agent=%s, round=%s, position=%s, key_points=%s, cited_rules=%s, summary=%s",
        agent_name,
        round_num + 1,
        position,
        len(output.key_points),
        len(output.cited_rules),
        _preview_text(output.summary),
    )
    return AgentMessage(
       role=role,
       agent_name=agent_name,
       round_number=round_num,
       position=position,
       summary=output.summary,
       content=output.content,
       key_points=output.key_points,
       cited_rules=output.cited_rules,
    )

def generate_judge_opinion(
    system_prompt: str,
    user_prompt: str,
    judge_name: str,
) -> JudgeOpinion:
    output = call_llm_json(system_prompt, user_prompt, JudgeStructuredOutput)
    logger.info(
        "판사 의견 생성 완료: judge=%s, decision=%s, cited_rules=%s, summary=%s",
        judge_name,
        output.decision,
        len(output.cited_rules),
        _preview_text(output.opinion_summary),
    )
    return JudgeOpinion(
        judge_name=judge_name,
        opinion_summary=output.opinion_summary,
        decision=output.decision,
        reasoning=output.reasoning,
        sentence=output.sentence,
        cited_rules=output.cited_rules,
    )


def generate_master_judgment(
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str, str, str]:
    output = call_llm_json(system_prompt, user_prompt, MasterJudgeStructuredOutput)
    logger.info(
        "최종 판결 생성 완료: verdict=%s, sentence=%s, reasoning=%s",
        output.verdict,
        output.sentence,
        _preview_text(output.reasoning),
    )
    return output.verdict, output.reasoning, output.report, output.sentence
