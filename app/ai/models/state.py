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
    cited_rules: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrialState(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    case_id: str
    case_type: CaseType = CaseType.UNKNOWN
    case_summary: str = ""
    facts: list[str] = Field(default_factory=list)
    round_limit: int = Field(default=3, ge=1)
    current_round: int = Field(default=0, ge=0)
    retrieved_docs: list[RetrievedDocument] = Field(default_factory=list)
    messages: list[AgentMessage] = Field(default_factory=list)
    judge_opinions: list[JudgeOpinion] = Field(default_factory=list)
    final_verdict: str | None = None
    final_reasoning: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rounds(self) -> TrialState:
        if self.current_round > self.round_limit:
            raise ValueError("current_round cannot exceed round_limit")
        return self

    def add_retrieved_doc(self, doc: RetrievedDocument) -> None:
        self.retrieved_docs.append(doc)

    def add_message(self, message: AgentMessage) -> None:
        self.messages.append(message)

    def add_judge_opinion(self, opinion: JudgeOpinion) -> None:
        self.judge_opinions.append(opinion)

    def set_final_decision(self, verdict: str, reasoning: str) -> None:
        self.final_verdict = verdict
        self.final_reasoning = reasoning
