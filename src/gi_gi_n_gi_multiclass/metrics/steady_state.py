

from __future__ import annotations

import numpy as np
from typing import Any
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe

def time_average_L(res: Any) -> dict:
    """Exact time-average L and Lq over [warmup_time, end_time].

    Uses per-customer overlap durations directly.

    L  = average number in system
    Lq = average number waiting (not in service)
    """
    df = customers_to_dataframe(res)
    t0 = float(res.config.warmup_time)
    t1 = float(res.end_time)

    if t1 <= t0:
        return {"L": float("nan"), "Lq": float("nan")}

    T = t1 - t0

    def overlap(start, end):
        if start is None or end is None:
            return 0.0
        if not np.isfinite(start) or not np.isfinite(end):
            return 0.0
        s = max(float(start), t0)
        e = min(float(end), t1)
        return max(0.0, e - s)

    system_time = 0.0
    queue_time = 0.0

    for _, r in df.iterrows():
        a = r["arrival_time"]
        s = r["service_start"]
        e = r["service_end"]
        aband = r["abandon_time"]
        out = r["outcome"]

        if out == "SERVED":
            # in system from arrival to service end
            system_time += overlap(a, e)
            # in queue from arrival to service start
            queue_time += overlap(a, s)

        elif out == "ABANDONED":
            # in system and queue from arrival to abandonment
            system_time += overlap(a, aband)
            queue_time += overlap(a, aband)

        elif out == "IN_SYSTEM_END":
            # still in system at end of observation window
            system_time += overlap(a, t1)

            if s is None or (not np.isfinite(s)):
                # still waiting at t1
                queue_time += overlap(a, t1)
            else:
                # entered service before t1, queue ends at service start
                queue_time += overlap(a, s)

    return {
        "L": float(system_time / T),
        "Lq": float(queue_time / T),
    }