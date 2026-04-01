from __future__ import annotations
import numpy as np

class RNGStreams:
    """Reproducible independent streams for arrivals, service, patience."""
    def __init__(self, seed: int) -> None:
        ss = np.random.SeedSequence(seed)
        child = ss.spawn(3)
        self.arrivals = np.random.default_rng(child[0])
        self.service = np.random.default_rng(child[1])
        self.patience = np.random.default_rng(child[2])
