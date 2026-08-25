from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState


@dataclass(frozen=True)
class NaiveFCFS:
    """FCFS across all eligible customers, without class prioritization."""

    name: str = "NaiveFCFS"

    def select_customer(self, state: MultiSystemState, now: float) -> Optional[int]:
        oldest = [state.oldest_waiting(cls) for cls in range(state.n_classes)]
        candidates = [cid for cid in oldest if cid is not None]
        if not candidates:
            return None
        return min(candidates, key=lambda cid: state.arrival_time[cid])
