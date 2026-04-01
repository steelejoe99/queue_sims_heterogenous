from __future__ import annotations
import numpy as np
from gi_gi_n_gi_multiclass.core.types import SimResult
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe

def service_level(res: SimResult, tau: float) -> float:
    """P(wait <= tau | served) on post-warmup arrivals."""
    df = customers_to_dataframe(res)
    df = df[df["arrival_time"] >= res.config.warmup_time]
    served = df[df["outcome"] == "SERVED"].copy()
    if len(served) == 0:
        return float("nan")
    wait = served["service_start"] - served["arrival_time"]
    return float((wait <= tau).mean())
