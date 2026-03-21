"""HDBSCAN clustering — placeholder.

Groups response embeddings into thematic clusters and maps
each cluster to a Theme record in the database.
"""
import numpy as np


def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 5) -> np.ndarray:
    """Run HDBSCAN on embeddings and return cluster label array (-1 = noise)."""
    raise NotImplementedError


def labels_to_themes(
    labels: np.ndarray,
    response_ids: list[str],
    account_id: str,
) -> list[dict]:
    """Convert cluster labels to theme dicts ready for DB insertion."""
    raise NotImplementedError
