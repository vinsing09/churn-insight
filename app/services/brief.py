"""Claude Sonnet brief generation for ad creative strategy."""
import json

import anthropic

from app.core.config import settings

_MODEL = "claude-sonnet-4-6"

_SYSTEM = """\
You are a senior performance marketing strategist specialising in B2B SaaS.
Given customer churn data, you generate actionable ad creative briefs.
Return ONLY a valid JSON object — no markdown, no explanation.
"""

_PROMPT = """\
Generate an ad creative brief based on this churn theme.

Theme name: {theme_name}
Theme description: {theme_description}

Sample churn responses from this theme:
{responses}

{ad_copy_section}

Output a JSON object with exactly these keys:
{{
  "angle_name": "<short, memorable name for this creative angle>",
  "gap_description": "<what unmet need or pain this angle addresses>",
  "headline_hypothesis": "<a specific ad headline to test, max 10 words>",
  "test_recommendation": "<how to test: format, channel, audience segment>"
}}
"""


async def generate_brief(
    theme_name: str,
    theme_description: str,
    sample_responses: list[str],
    ad_copy: str | None = None,
) -> dict:
    """Call Claude Sonnet to generate an ad creative brief.

    Returns a dict matching the Brief model fields (excluding id, account_id, theme_id).
    """
    responses_block = "\n".join(f"- {r}" for r in sample_responses[:10])

    if ad_copy:
        ad_copy_section = f"Current ad copy / headlines:\n{ad_copy}\n\nIdentify gaps between what churned users needed and what this copy promises."
    else:
        ad_copy_section = ""

    prompt = _PROMPT.format(
        theme_name=theme_name,
        theme_description=theme_description,
        responses=responses_block,
        ad_copy_section=ad_copy_section,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)

    return {
        "angle_name": data["angle_name"],
        "gap_description": data["gap_description"],
        "headline_hypothesis": data["headline_hypothesis"],
        "test_recommendation": data["test_recommendation"],
        "model_used": _MODEL,
    }
