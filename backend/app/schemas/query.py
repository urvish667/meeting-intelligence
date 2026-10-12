from typing import List, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


class QueryResponse(BaseModel):
    question: str
    answer: str
    evidence: List[Any]
    provider: str
    model: str
