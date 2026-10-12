import json
from typing import Tuple, List, Dict, Any, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import AppException
from app.schemas.analysis import MeetingAnalysisSchema
from app.services.analysis.base import LLMAnalyzerProvider
from app.services.analysis.prompts import ANALYSIS_SYSTEM_INSTRUCTION, QUERY_SYSTEM_INSTRUCTION
from app.services.retrieval import retrieve_relevant_snippets, split_transcript_chunks


class GeminiAnalyzerProvider(LLMAnalyzerProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key if api_key is not None else (settings.gemini_api_key or "")
        self.model_name = model_name or settings.gemini_model
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if not self.api_key or self.api_key.startswith("your_gemini_api_key"):
            raise AppException(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in the environment or .env file.",
                503
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _call_gemini_json(self, prompt: str, system_instruction: str) -> dict:
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1,
            )
        )
        text = response.text or "{}"
        try:
            return json.loads(text)
        except json.JSONDecodeError as err:
            logger.warning(f"Initial JSON parse failed, retrying once: {err}")
            retry_prompt = f"Previous response was not valid JSON:\n{text}\n\nFix the formatting and output valid JSON only:\n{prompt}"
            retry_res = client.models.generate_content(
                model=self.model_name,
                contents=retry_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.0,
                )
            )
            return json.loads(retry_res.text or "{}")

    def analyze_transcript(self, transcript_text: str, segments: List[dict] = None) -> MeetingAnalysisSchema:
        if not transcript_text.strip():
            raise AppException("Transcript is empty, cannot perform analysis.", 400)

        if len(transcript_text) > 15000:
            chunks = split_transcript_chunks(transcript_text, chunk_size=1200, overlap=200)
            combined_prompt = f"Analyze this full transcript excerpt chunk:\n\n{chunks[0]}"
        else:
            combined_prompt = f"Analyze the following meeting transcript:\n\n{transcript_text}"

        raw_data = self._call_gemini_json(combined_prompt, ANALYSIS_SYSTEM_INSTRUCTION)

        try:
            analysis = MeetingAnalysisSchema.model_validate(raw_data)
        except Exception as e:
            logger.warning(f"Schema validation error: {e}. Retrying once with schema feedback.")
            fix_prompt = f"The following JSON did not conform to the schema: {e}\n\nRaw JSON:\n{json.dumps(raw_data)}\n\nReformat and return conforming JSON:"
            raw_data = self._call_gemini_json(fix_prompt, ANALYSIS_SYSTEM_INSTRUCTION)
            analysis = MeetingAnalysisSchema.model_validate(raw_data)

        for item in analysis.action_items:
            item.deadline_normalized = None

        analysis.metadata = {
            "provider": "gemini",
            "model": self.model_name,
            "schema_version": "1.0.0"
        }
        return analysis

    def answer_query(
        self,
        question: str,
        transcript_text: str,
        analysis_dict: Dict[str, Any] = None
    ) -> Tuple[str, List[str]]:
        if not question.strip():
            raise AppException("Question cannot be empty.", 422)

        analysis_summary = ""
        if analysis_dict:
            analysis_summary = f"Meeting Summary: {analysis_dict.get('summary', '')}\nDecisions: {json.dumps(analysis_dict.get('decisions', []))}\nAction Items: {json.dumps(analysis_dict.get('action_items', []))}\nBlockers: {json.dumps(analysis_dict.get('blockers', []))}\nUnresolved Items: {json.dumps(analysis_dict.get('unresolved_items', []))}"

        prompt = f"""Question: {question}

Context Analysis:
{analysis_summary}

Full / Relevant Transcript:
{transcript_text[:12000]}
"""
        raw_res = self._call_gemini_json(prompt, QUERY_SYSTEM_INSTRUCTION)
        answer = raw_res.get("answer", "The meeting does not provide enough information to answer this question.")
        evidence = raw_res.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [evidence]
        return answer, evidence
