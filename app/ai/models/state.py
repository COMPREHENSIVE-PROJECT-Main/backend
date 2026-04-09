from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseType(str, Enum):
    UNKNOWN = "unknown"
    CRIMINAL = "criminal"
    CIVIL = "civil"


class RetrievalCollection(str, Enum):
    CASES = "cases"
    STATUTES = "statutes"
    SENTENCING = "sentencing"


class AgentRole(str, Enum):
    PROSECUTOR = "prosecutor"
    DEFENSE = "defense"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    JUDGE = "judge"
    MASTER_JUDGE = "master_judge"
    SYSTEM = "system"


class RetrievedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    collection: RetrievalCollection
    title: str
    content: str
    score: float | None = None
    summary: str | None = None
    cited_rules: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: AgentRole
    agent_name: str
    round_number: int = Field(ge=0, default=0)
    position: str | None = None
    summary: str
    key_points: list[str] = Field(default_factory=list)
    cited_rules: list[str] = Field(default_factory=list)
    next_action: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JudgeOpinion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    judge_name: str
    round_number: int = Field(ge=0, default=0)
    opinion_summary: str
    reasoning: str
    decision: str
    sentence: str | None = None # 형량 또는 배상액 (예 : "징역 3년", "배상액 500만원")
    cited_rules: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentContext(BaseModel): # 에이전트 개인 상태 컨테이너 - 상대 에이전트는 접근 불가
    model_config = ConfigDict(extra="forbid") # 정의되지 않은 필드가 들어오면 오류 발생

    assigned_role: AgentRole                  # 배정된 역할 (검사, 원고 변호사, 피고 변호사 등)
    role_prompt: str                          # 맡은 역할에 대한 프롬프트 저장
    retrieved_docs: list[RetrievedDocument] = Field(default_factory=list) # 개인 검색 결과



class TrialState(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True) # 정의되지 않은 필드 오류 발생, 필드 변경 시에도 유효성 검사

    case_id: str
    case_type: CaseType = CaseType.UNKNOWN
    case_summary: str = ""
    facts: list[str] = Field(default_factory=list)
    round_limit: int = Field(default=3, ge=1)
    current_round: int = Field(default=0, ge=0)
    attacker_docs: list[RetrievedDocument] = Field(default_factory=list) # 공격 측 전용 검색 결과 (방어 측 접근 불가)
    defender_docs: list[RetrievedDocument] = Field(default_factory=list) # 방어 측 전용 검색 결과 (공격 측 접근 불가)
    messages: list[AgentMessage] = Field(default_factory=list)
    judge_opinions: list[JudgeOpinion] = Field(default_factory=list)
    debate_summary: dict | None = None                                   # 변론 종합 결과(공격측 발언, 방어측 발언, 인용 출처)
    final_verdict: str | None = None
    final_reasoning: str | None = None
    final_report: str | None = None                                      # 마스터 판사 종합 분석 리포트
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rounds(self) -> TrialState:
        if self.current_round > self.round_limit:
            raise ValueError("current_round cannot exceed round_limit")
        return self

    def add_attacker_doc(self, doc: RetrievedDocument) -> None:
        # 공격 측 검색 결과 추가 - 방어 측은 이 메서드 호출 불가
        self.attacker_docs.append(doc)

    def add_defender_doc(self, doc: RetrievedDocument) -> None:
        # 방어 측 검색 결과 추가 - 공격 측은 이 메서드 호출 불가
        self.defender_docs.append(doc)

    def add_message(self, message: AgentMessage) -> None:
        self.messages.append(message)

    def add_judge_opinion(self, opinion: JudgeOpinion) -> None:
        self.judge_opinions.append(opinion)

    def set_final_decision(self, verdict: str, reasoning: str, report: str) -> None:
        self.final_verdict = verdict
        self.final_reasoning = reasoning
        self.final_report = report                                      # 종합 분석 리포트 함께 저장
