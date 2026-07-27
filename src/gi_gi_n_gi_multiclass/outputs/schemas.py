from __future__ import annotations

from typing import Optional, Any
import pandas as pd

def customers_to_dataframe(res: Any) -> pd.DataFrame:
    """Convert simulation customers to a DataFrame.

    Works for both single-class SimResult (core.types.SimResult) and
    multi-class MultiSimResult (core.types_multi.MultiSimResult).
    """
    rows = []
    for rec in res.customers:
        row = {
            "customer_id": rec.customer_id,
            "class_id": getattr(rec, "assigned_class_id", getattr(rec, "class_id", 0)),
            "true_class_id": getattr(rec, "true_class_id", getattr(rec, "class_id", 0)),
            "assigned_class_id": getattr(rec, "assigned_class_id", getattr(rec, "class_id", 0)),
            "arrival_time": rec.arrival_time,
            "service_start": rec.service_start,
            "eligibility_time": getattr(rec, "eligibility_time", rec.arrival_time),
            "service_end": rec.service_end,
            "service_time": rec.service_time,
            "patience_time": rec.patience_time,
            "abandon_time": rec.abandon_time,
            "outcome": rec.outcome,
        }
        if hasattr(rec, "class_id"):
            row["class_id"] = getattr(rec, "class_id")
        rows.append(row)
    df = pd.DataFrame(rows)
    if "class_id" not in df.columns:
        df["class_id"] = 0
    return df

def event_log_to_dataframe(res: Any) -> Optional[pd.DataFrame]:
    if getattr(res, "event_log", None) is None:
        return None
    return pd.DataFrame(res.event_log)
