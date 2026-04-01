from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from gi_gi_n_gi_multiclass.core.state import SystemState

@dataclass(frozen=True)
class FCFS:
    name: str = "FCFS"
    def select_customer(self, state: SystemState, now: float) -> Optional[int]:
        if not state.waiting:
            return None
        # oldest: max time-in-queue = now - arrival_time
        return max(state.waiting, key=lambda cid: now - state.arrival_time[cid])
