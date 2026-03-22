"""OpenAI text-embedding-3-small embeddings with numpy persistence."""
from pathlib import Path

import numpy as np
from openai import AsyncOpenAI

from app.core.config import settings

_MODEL = "text-embedding-3-small"
_EMBEDDINGS_DIR = Path("data/embeddings")


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Return (N, 1536) float32 embedding matrix for a list of texts."""
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.embeddings.create(model=_MODEL, input=texts)
    vectors = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    return np.array(vectors, dtype=np.float32)


def save_embeddings(account_id: str, response_ids: list[str], embeddings: np.ndarray) -> None:
    """Persist embeddings and their response_id index to disk."""
    account_dir = _EMBEDDINGS_DIR / account_id
    account_dir.mkdir(parents=True, exist_ok=True)
    np.save(account_dir / "embeddings.npy", embeddings)
    (account_dir / "response_ids.txt").write_text("\n".join(response_ids))


def load_embeddings(account_id: str) -> tuple[list[str], np.ndarray]:
    """Load persisted embeddings; returns (response_ids, embeddings).

    Returns empty structures if no embeddings exist yet.
    """
    account_dir = _EMBEDDINGS_DIR / account_id
    ids_path = account_dir / "response_ids.txt"
    emb_path = account_dir / "embeddings.npy"

    if not ids_path.exists() or not emb_path.exists():
        return [], np.empty((0, 1536), dtype=np.float32)

    response_ids = ids_path.read_text().splitlines()
    embeddings = np.load(emb_path)
    return response_ids, embeddings
