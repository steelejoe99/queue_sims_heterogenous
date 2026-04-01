# src/gi_gi_n_gi_multiclass/labeling/confusion.py

from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ConfusionMatrixClassifier:
    """
    Rows = true class, columns = assigned class.
    Entry [i, j] = P(assigned=j | true=i).
    """
    matrix: np.ndarray

    def __post_init__(self):
        m = np.asarray(self.matrix, dtype=float)
        if m.ndim != 2 or m.shape[0] != m.shape[1]:
            raise ValueError("matrix must be square")
        if np.any(m < 0):
            raise ValueError("matrix entries must be nonnegative")
        row_sums = m.sum(axis=1)
        if not np.allclose(row_sums, 1.0):
            raise ValueError("each row of confusion matrix must sum to 1")
        object.__setattr__(self, "matrix", m)

    @property
    def n_classes(self) -> int:
        return int(self.matrix.shape[0])

    def assign(self, true_class_id: int, rng: np.random.Generator) -> int:
        probs = self.matrix[true_class_id]
        return int(rng.choice(len(probs), p=probs))