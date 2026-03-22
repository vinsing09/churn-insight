"""HDBSCAN clustering of response embeddings."""
import json
from collections import defaultdict

import anthropic
import hdbscan
import numpy as np

from app.core.config import settings

_NAMING_MODEL = "claude-haiku-4-5-20251001"

_NAMING_SYSTEM = """\
You are a B2B SaaS analyst naming customer churn themes for a marketing team.
Return ONLY a valid JSON object — no markdown, no explanation.
"""

_NAMING_PROMPT = """\
These customer responses all belong to the same churn theme.
Give this theme a short, descriptive name and a one-sentence description.

Responses:
{responses}

Return JSON with exactly these keys:
{{
  "name": "<3-6 word descriptive name, title case>",
  "description": "<one sentence explaining what drives this theme>"
}}
"""


async def name_cluster(sample_texts: list[str]) -> tuple[str, str]:
    """Ask Claude Haiku to name a cluster from its sample responses.

    Returns (name, description). Falls back to a generic label on any error.
    """
    block = "\n".join(f"- {t}" for t in sample_texts[:8])
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=_NAMING_MODEL,
            max_tokens=128,
            system=_NAMING_SYSTEM,
            messages=[{"role": "user", "content": _NAMING_PROMPT.format(responses=block)}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return data["name"], data.get("description", "")
    except Exception:
        return "", ""


def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 5) -> np.ndarray:
    """Run HDBSCAN and return integer cluster labels (-1 = noise/unclustered)."""
    if len(embeddings) < min_cluster_size:
        return np.full(len(embeddings), -1, dtype=int)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=2,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(embeddings).astype(int)


def labels_to_cluster_map(labels: np.ndarray, response_ids: list[str]) -> dict[int, list[str]]:
    """Map cluster label → list of response_ids (excludes noise label -1)."""
    clusters: dict[int, list[str]] = defaultdict(list)
    for label, rid in zip(labels, response_ids):
        if label != -1:
            clusters[int(label)].append(rid)
    return dict(clusters)
