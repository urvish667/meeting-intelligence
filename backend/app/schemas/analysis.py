from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class DecisionItem(BaseModel):
    text: str
    status: Literal["confirmed", "tentative", "rejected", "superseded"] = "confirmed"
    evidence_quote: str = ""
    timestamp: Optional[str] = None
    confidence: Optional[float] = None


class ActionItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline_stated: Optional[str] = None
    deadline_normalized: Optional[str] = None
    priority: Literal["low", "medium", "high", "urgent", "unknown"] = "unknown"
    status: Literal["open", "in_progress", "blocked", "completed", "unknown"] = "open"
    evidence_quote: str = ""
    timestamp: Optional[str] = None
    confidence: Optional[float] = None


class RiskItem(BaseModel):
    description: str
    impact: Optional[str] = None
    evidence_quote: str = ""
    confidence: Optional[float] = None


class BlockerItem(BaseModel):
    description: str
    owner: Optional[str] = None
    dependency: Optional[str] = None
    status: str = "open"
    evidence_quote: str = ""
    confidence: Optional[float] = None


class UnresolvedItem(BaseModel):
    question: str
    owner: Optional[str] = None
    evidence_quote: str = ""
    confidence: Optional[float] = None


class ParticipantItem(BaseModel):
    name: str
    role: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: Optional[float] = None


class MeetingAnalysisSchema(BaseModel):
    summary: str
    decisions: List[DecisionItem] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    blockers: List[BlockerItem] = Field(default_factory=list)
    unresolved_items: List[UnresolvedItem] = Field(default_factory=list)
    participants: List[ParticipantItem] = Field(default_factory=list)
    key_topics: List[str] = Field(default_factory=list)
    metadata: Optional[dict] = None
