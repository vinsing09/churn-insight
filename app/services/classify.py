"""Claude Haiku response classification."""
import json
from datetime import datetime, timezone

import anthropic

from app.core.config import settings

_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM = """\
You are an expert analyst classifying B2B SaaS churn survey responses.
Return ONLY a valid JSON object — no markdown, no explanation.
"""

_PROMPT = """\
Classify this churn response into the following JSON structure:

{{
  "primary_reason": "<price|missing_feature|competitor|complexity|poor_fit|unused|service|other>",
  "competitor_mentioned": <true|false>,
  "competitor_name": "<name or null>",
  "emotional_intensity": <1-5>,
  "marketing_actionability": "<high|medium|low>",
  "key_phrases": ["<phrase>", ...],
  "summary": "<1-2 sentence summary>",
  "confidence": <0.0-1.0>
}}

Scoring guidance:
- emotional_intensity: 1=neutral, 2=mild dissatisfaction, 3=moderate frustration, 4=strong negative, 5=extreme anger
- marketing_actionability: high=ads can directly address this pain; medium=addressable with nuance; low=systemic/not ad-addressable

Response to classify:
{text}
"""


async def classify_response(response_text: str) -> dict:
    """Call Claude Haiku to classify a stripped churn response.

    Returns a dict matching the Classification model fields plus 'classified_at' and 'model_used'.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = await client.messages.create(
        model=_MODEL,
        max_tokens=512,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _PROMPT.format(text=response_text)}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if the model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)

    return {
        "primary_reason": data.get("primary_reason", "other"),
        "competitor_mentioned": bool(data.get("competitor_mentioned", False)),
        "competitor_name": data.get("competitor_name"),
        "emotional_intensity": int(data.get("emotional_intensity", 3)),
        "marketing_actionability": data.get("marketing_actionability", "medium"),
        "key_phrases": data.get("key_phrases", []),
        "summary": data.get("summary", ""),
        "classified_at": datetime.now(timezone.utc),
        "model_used": _MODEL,
        "confidence": float(data.get("confidence", 0.8)),
    }
