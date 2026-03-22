"""Embeddings: OpenAI primary, sentence-transformers local fallback."""
import logging
from pathlib import Path

import numpy as np
from openai import AsyncOpenAI, AuthenticationError, RateLimitError

from app.core.config import settings

logger = logging.getLogger(__name__)

_MODEL = "text-embedding-3-small"
_OPENAI_DIM = 1536
_LOCAL_DIM = 384
_EMBEDDINGS_DIR = Path("data/embeddings")

_st_model = None


def _get_st_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        logger.warning("Falling back to local sentence-transformers embeddings")
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _st_model


def _expected_dim() -> int:
    """Return the dimension the current model will produce without calling it.

    If an OpenAI key is configured we expect 1536 (text-embedding-3-small).
    Otherwise the local sentence-transformers fallback produces 384.
    """
    return _OPENAI_DIM if settings.OPENAI_API_KEY else _LOCAL_DIM


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Return (N, D) float32 embedding matrix.

    Tries OpenAI text-embedding-3-small first (D=1536).
    Falls back to all-MiniLM-L6-v2 via sentence-transformers (D=384)
    if OpenAI is unavailable (no key, rate limit, or any other error).
    """
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.embeddings.create(model=_MODEL, input=texts)
        vectors = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        return np.array(vectors, dtype=np.float32)
    except (RateLimitError, AuthenticationError, Exception) as e:
        logger.warning(f"OpenAI embeddings failed ({e}), using local fallback")
        model = _get_st_model()
        vectors = model.encode(texts, show_progress_bar=False)
        return np.array(vectors, dtype=np.float32)


def save_embeddings(account_id: str, response_ids: list[str], embeddings: np.ndarray) -> None:
    """Persist embeddings and their response_id index to disk."""
    account_dir = _EMBEDDINGS_DIR / account_id
    account_dir.mkdir(parents=True, exist_ok=True)
    np.save(account_dir / "embeddings.npy", embeddings)
    (account_dir / "response_ids.txt").write_text("\n".join(response_ids))
    # Record dimension so load_embeddings can detect model switches
    dim = embeddings.shape[1] if embeddings.ndim == 2 and len(embeddings) > 0 else 0
    (account_dir / "dim.txt").write_text(str(dim))


def load_embeddings(account_id: str) -> tuple[list[str], np.ndarray]:
    """Load persisted embeddings; returns (response_ids, embeddings).

    Returns empty structures in two cases:
    - No saved embeddings exist yet.
    - Saved dimension doesn't match the current model's dimension
      (e.g. switching between OpenAI 1536-d and local 384-d).
      The caller should re-embed everything rather than mixing shapes.
    """
    account_dir = _EMBEDDINGS_DIR / account_id
    ids_path = account_dir / "response_ids.txt"
    emb_path = account_dir / "embeddings.npy"
    dim_path = account_dir / "dim.txt"

    if not ids_path.exists() or not emb_path.exists():
        return [], np.empty((0, _expected_dim()), dtype=np.float32)

    # Check for dimension mismatch before loading the (potentially large) array
    if dim_path.exists():
        try:
            saved_dim = int(dim_path.read_text().strip())
            expected = _expected_dim()
            if saved_dim != 0 and saved_dim != expected:
                logger.warning(
                    f"Saved embeddings are {saved_dim}-d but current model produces "
                    f"{expected}-d — discarding cache to force re-embedding"
                )
                return [], np.empty((0, expected), dtype=np.float32)
        except ValueError:
            pass  # malformed dim.txt — fall through and load anyway

    response_ids = ids_path.read_text().splitlines()
    embeddings = np.load(emb_path)
    return response_ids, embeddings
