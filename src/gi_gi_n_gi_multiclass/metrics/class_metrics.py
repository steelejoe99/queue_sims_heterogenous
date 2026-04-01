from __future__ import annotations

import pandas as pd
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe

def abandonment_probability_by_true_class(res, true_class_id: int) -> float:
    df = customers_to_dataframe(res)
    t0 = float(res.config.warmup_time)
    df = df[df["arrival_time"] >= t0].copy()
    g = df[df["true_class_id"] == true_class_id]
    if len(g) == 0:
        return float("nan")
    return float((g["outcome"] == "ABANDONED").mean())

def abandonment_probability_by_assigned_class(res, assigned_class_id: int) -> float:
    df = customers_to_dataframe(res)
    t0 = float(res.config.warmup_time)
    df = df[df["arrival_time"] >= t0].copy()
    g = df[df["assigned_class_id"] == assigned_class_id]
    if len(g) == 0:
        return float("nan")
    return float((g["outcome"] == "ABANDONED").mean())

def realized_confusion_table(res) -> pd.DataFrame:
    df = customers_to_dataframe(res)
    t0 = float(res.config.warmup_time)
    df = df[df["arrival_time"] >= t0].copy()
    return pd.crosstab(
        df["true_class_id"],
        df["assigned_class_id"],
        rownames=["true_class_id"],
        colnames=["assigned_class_id"],
    )

def chronic_abandonment_probability(res, chronic_class_id: int = 0) -> float:
    return abandonment_probability_by_true_class(res, chronic_class_id)