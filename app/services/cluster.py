"""HDBSCAN clustering of response embeddings."""
from collections import defaultdict

import hdbscan
import numpy as np


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
