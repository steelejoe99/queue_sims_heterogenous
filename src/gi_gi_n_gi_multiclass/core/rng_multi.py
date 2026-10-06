"""Class-specific reproducible random-number streams for multiclass runs."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class MultiRngStreams:
    """Independent arrival, service, and patience generators per true class."""
    arrivals: list[np.random.Generator]
    service: list[np.random.Generator]
    patience: list[np.random.Generator]

def make_multi_rng_streams(seed: int, n_classes: int) -> MultiRngStreams:
    """Create deterministic per-class streams from one simulation seed."""
    base = int(seed)
    arrivals = [np.random.default_rng(base + 1000 + i) for i in range(n_classes)]
    service = [np.random.default_rng(base + 2000 + i) for i in range(n_classes)]
    patience = [np.random.default_rng(base + 3000 + i) for i in range(n_classes)]
    return MultiRngStreams(arrivals=arrivals, service=service, patience=patience)

def make_label_rng(seed: int) -> np.random.Generator:
    """Create the stream used only for true-to-assigned class labelling."""
    return np.random.default_rng(int(seed) + 4000)
