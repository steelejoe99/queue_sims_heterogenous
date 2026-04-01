from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState

def _tiq_pick_in_class(state: MultiSystemState, cls: int, now: float, w_l: float, w_h: float) -> Optional[int]:
    # Priority: Region 3 (w>=w_h), then Region 1 (w<w_l), then Region 2.
    # Within region: FCFS (oldest arrival first).
    r3 = []
    r1 = []
    r2 = []
    for cid in state.waiting_by_class[cls]:
        w = now - state.arrival_time[cid]
        if w >= w_h:
            r3.append(cid)
        elif w < w_l:
            r1.append(cid)
        else:
            r2.append(cid)

    def pick_fcfs(cands):
        best = None
        best_arr = None
        for cid in cands:
            arr = state.arrival_time[cid]
            if best is None or arr < best_arr:
                best = cid
                best_arr = arr
        return best

    out = pick_fcfs(r3)
    if out is not None:
        return out
    out = pick_fcfs(r1)
    if out is not None:
        return out
    return pick_fcfs(r2)

@dataclass(frozen=True)
class MostlyFCFS:
    """FCFS within all classes except one split class, where TIQ is used.

    Across-class selection is delegated to class_selector, which must implement choose_class().
    """

    class_selector: object
    split_class_id: int
    w_l: float
    w_h: float
    name: str = "MostlyFCFS"

    def select_customer(self, state: MultiSystemState, now: float) -> Optional[int]:
        # choose class first
        if hasattr(self.class_selector, "choose_class"):
            cls = self.class_selector.choose_class(state, now)
        else:
            # fallback: assume selector is itself a policy returning customer id
            cid = self.class_selector.select_customer(state, now)
            return cid

        if cls is None:
            return None

        if cls == self.split_class_id:
            return _tiq_pick_in_class(state, cls, now, self.w_l, self.w_h)

        # FCFS within chosen class
        best = None
        best_arr = None
        for cid in state.waiting_by_class[cls]:
            arr = state.arrival_time[cid]
            if best is None or arr < best_arr:
                best = cid
                best_arr = arr
        return best
