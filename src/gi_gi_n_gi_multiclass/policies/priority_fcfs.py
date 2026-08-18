from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState

@dataclass(frozen=True)
class PriorityFCFS:
    """Strict class priority; FCFS within each class."""

    priority_order: Sequence[int]
    name: str = "PriorityFCFS"

    def choose_class(self, state: MultiSystemState, now: float) -> Optional[int]:
        for cls in self.priority_order:
            if 0 <= cls < state.n_classes and len(state.waiting_by_class[cls]) > 0:
                return cls
        return None

    def select_customer(self, state: MultiSystemState, now: float) -> Optional[int]:
        cls = self.choose_class(state, now)
        if cls is None:
            return None
        return state.oldest_waiting(cls)
