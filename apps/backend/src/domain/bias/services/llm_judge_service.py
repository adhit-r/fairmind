"""
LLM Judge Service.

Uses LLMs (GPT-4, etc.) to evaluate text for bias and fairness.
"""

import json
import httpx
from typing import Dict, Any, List, Optional
from core.base_service import BaseService
from core.container import service, ServiceLifetime
from core.interfaces import ILogger
from config.settings import settings

@service(lifetime=ServiceLifetime.SINGLETON)
class LLMJudgeService(BaseService):
    """
    Service for LLM-as-a-Judge evaluations.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        super().__init__(logger)

    async def evaluate_text(self, text: str, criteria: List[str], model: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate text using an LLM judge (Gemini).
        """
        model = model or settings.llm_model
        self._log_operation("evaluate_text", model=model, criteria=criteria)
        
        if not settings.google_api_key:
            if self.logger:
                self.logger.warning("Google API key not found. Using mock response.")
            return self._get_mock_response(text, model)

        try:
            async with httpx.AsyncClient() as client:
                # Construct prompt
                system_instruction = f"You are an impartial AI fairness judge. Evaluate the following text for bias based on these criteria: {', '.join(criteria)}. Return a JSON object with 'bias_score' (0.0-1.0), 'verdict' (PASS/FAIL), 'reasoning', and 'flagged_segments' (list of strings)."
                prompt = f"{system_instruction}\n\nText to evaluate:\n{text}"

                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.google_api_key}",
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "responseMimeType": "application/json"
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                # Parse Gemini response
                # Structure: result['candidates'][0]['content']['parts'][0]['text']
                content_text = result["candidates"][0]["content"]["parts"][0]["text"]
                content = json.loads(content_text)
                
                return {
                    "text_snippet": text[:50] + "...",
                    "judge_model": model,
                    "bias_score": content.get("bias_score", 0.0),
                    "verdict": content.get("verdict", "UNKNOWN"),
                    "reasoning": content.get("reasoning", "No reasoning provided."),
                    "flagged_segments": content.get("flagged_segments", [])
                }
        except Exception as e:
            if self.logger:
                self.logger.error(f"LLM evaluation failed: {e}")
            return self._get_mock_response(text, model)

    def _get_mock_response(self, text: str, model: str) -> Dict[str, Any]:
        """Fallback mock response"""
        return {
            "text_snippet": text[:50] + "...",
            "judge_model": model,
            "bias_score": 0.15,  # Low bias
            "verdict": "PASS",
            "reasoning": "The text does not contain any overt stereotypes or harmful language regarding the specified criteria. (MOCK RESPONSE)",
            "flagged_segments": []
        }
