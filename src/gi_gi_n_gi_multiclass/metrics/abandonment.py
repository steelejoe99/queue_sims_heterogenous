from __future__ import annotations
import numpy as np
import pandas as pd
from gi_gi_n_gi_multiclass.core.types import SimResult
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe
from gi_gi_n_gi_multiclass.metrics.class_metrics import abandonment_probability_by_true_class

def chronic_abandonment_probability(res, chronic_class_id: int = 0) -> float:
    return abandonment_probability_by_true_class(res, chronic_class_id)

def abandonment_fraction(res: SimResult) -> float:
    df = customers_to_dataframe(res)
    df = df[df["arrival_time"] >= res.config.warmup_time]
    if len(df) == 0:
        return float("nan")
    return float((df["outcome"] == "ABANDONED").mean())


def weighted_abandon_cost(res, penalties: dict[int, float]) -> float:
    df = customers_to_dataframe(res)
    t0 = res.config.warmup_time
    df = df[df["arrival_time"] >= t0].copy()
    cost = 0.0
    for cid, p in penalties.items():
        cost += p * float(((df["class_id"] == cid) & (df["outcome"] == "ABANDONED")).sum())
    return cost