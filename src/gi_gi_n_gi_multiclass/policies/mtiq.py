from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState

def _tiq_pick_in_class(state: MultiSystemState, cls: int, now: float, w_l: float, w_h: float) -> Optional[int]:
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
    
    def pick_lcfs(cands):
        best = None
        best_arr = None
        for cid in cands:
            arr = state.arrival_time[cid]
            if best is None or arr > best_arr:
                best = cid
                best_arr = arr
        return best

    return pick_lcfs(r2)

@dataclass(frozen=True)
class MTIQ:
    """Bassamboo-style mTIQ scaffold.

    The cross-class choice is argmax of beta_i(n_i), where n_i is current number
    of servers allocated to class i (in_service_by_class[i]).

    Within-class selection:
      - if thresholds provided for that class, TIQ within class
      - else FCFS within class
    """

    beta: Sequence[Callable[[int], float]]
    w_l: Optional[Sequence[Optional[float]]] = None
    w_h: Optional[Sequence[Optional[float]]] = None
    name: str = "MTIQ"

    def select_customer(self, state: MultiSystemState, now: float) -> Optional[int]:
        best_cls = None
        best_val = None
        for i in range(state.n_classes):
            if len(state.waiting_by_class[i]) == 0:
                continue
            ni = state.in_service_by_class[i]
            val = float(self.beta[i](int(ni)))
            if best_cls is None or val > best_val:
                best_cls = i
                best_val = val
        if best_cls is None:
            return None

        # TIQ if thresholds exist
        if self.w_l is not None and self.w_h is not None:
            wl = self.w_l[best_cls]
            wh = self.w_h[best_cls]
            if wl is not None and wh is not None:
                return _tiq_pick_in_class(state, best_cls, now, float(wl), float(wh))

        # FCFS within class
        best = None
        best_arr = None
        for cid in state.waiting_by_class[best_cls]:
            arr = state.arrival_time[cid]
            if best is None or arr < best_arr:
                best = cid
                best_arr = arr
        return best
