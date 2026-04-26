from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class LLMRequest(BaseModel):
    messages: list[ChatMessage]
    system_prompt: str


class LLMResponse(BaseModel):
    content: str
    model: str
    created_at: str | None = None


class AgentStructuredOutput(BaseModel):
    summary: str = Field(description="발언의 1~2문장 요약")
    key_points: list[str] = Field(default_factory=list, description="핵심 주장 또는 반박 대상")
    cited_rules: list[str] = Field(default_factory=list, description="인용한 법조문, 판례, 양형기준")
    content: str = Field(description="사용자에게 보여줄 전체 발언 본문")


class JudgeStructuredOutput(BaseModel):
    opinion_summary: str = Field(description="판결 요약")
    cited_rules: list[str] = Field(default_factory=list, description="적용 법조문, 판례, 양형기준")
    reasoning: str = Field(description="판단 이유")
    decision: str = Field(description="유죄/무죄 또는 인용/기각")
    sentence: str | None = Field(default=None, description="형량 또는 배상액")


class MasterJudgeStructuredOutput(BaseModel):
    verdict: str = Field(description="최종 판결 결과")
    reasoning: str = Field(description="종합 판단 이유")
    sentence: str = Field(default="", description="최종 형량 또는 배상액")
    report: str = Field(description="종합 분석 보고서")
