from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
from app.schemas.analysis import MeetingAnalysisSchema


class LLMAnalyzerProvider(ABC):
    @abstractmethod
    def analyze_transcript(self, transcript_text: str, segments: List[dict] = None) -> MeetingAnalysisSchema:
        pass

    @abstractmethod
    def answer_query(self, question: str, transcript_text: str, analysis_dict: Dict[str, Any] = None) -> Tuple[str, List[str]]:
        pass
