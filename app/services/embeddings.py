"""OpenAI embeddings — placeholder.

Generates and stores text-embedding-3-small vectors for clustering.
Embeddings are persisted as .npy files under data/embeddings/<account_id>/.
"""
import numpy as np


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Return an (N, D) float32 array of embeddings for each text."""
    raise NotImplementedError


def save_embeddings(account_id: str, response_ids: list[str], embeddings: np.ndarray) -> None:
    """Persist embeddings to disk for an account."""
    raise NotImplementedError


def load_embeddings(account_id: str) -> tuple[list[str], np.ndarray]:
    """Load persisted embeddings; returns (response_ids, embeddings)."""
    raise NotImplementedError
