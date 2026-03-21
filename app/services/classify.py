"""Claude Haiku classification — placeholder.

Classifies a single churn response into structured fields:
primary_reason, competitor_mentioned, emotional_intensity, etc.
"""
from app.db.models import Classification


async def classify_response(response_text: str) -> dict:
    """Call Claude Haiku to classify a stripped response.

    Returns a dict matching the Classification model fields.
    """
    raise NotImplementedError
