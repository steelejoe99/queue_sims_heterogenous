from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from gi_gi_n_gi_multiclass.core.state import SystemState

@dataclass(frozen=True)
class TIQ:
    """Two-threshold time-in-queue policy TIQ(w_l, w_h).

    Priority order:
      Region 3: w >= w_h (old)        [highest]
      Region 1: w <  w_l (young)      [next]
      Region 2: w_l <= w < w_h        [lowest]

    Within region:
      Region 3 and 1 use FCFS within-region (oldest within region),
      Region 2 uses LCFS within-region (newest within region).
    """
    w_l: float
    w_h: float
    name: str = "TIQ"

    def __post_init__(self) -> None:
        if not (0.0 <= self.w_l <= self.w_h):
            raise ValueError("Require 0 <= w_l <= w_h")

    def select_customer(self, state: SystemState, now: float) -> Optional[int]:
        if not state.waiting:
            return None

        def wq(cid: int) -> float:
            return now - state.arrival_time[cid]

        region3 = [cid for cid in state.waiting if wq(cid) >= self.w_h]
        if region3:
            # FCFS within region3: oldest
            return max(region3, key=wq)

        region1 = [cid for cid in state.waiting if wq(cid) < self.w_l]
        if region1:
            # FCFS within region1: oldest among young
            return max(region1, key=wq)

        # region2 lowest: LCFS within region2 (newest)
        region2 = [cid for cid in state.waiting if self.w_l <= wq(cid) < self.w_h]
        if region2:
            return min(region2, key=wq)

        # fallback
        return max(state.waiting, key=wq)
