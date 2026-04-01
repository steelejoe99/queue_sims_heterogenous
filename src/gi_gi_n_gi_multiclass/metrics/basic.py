from __future__ import annotations
import pandas as pd
import numpy as np
from gi_gi_n_gi_multiclass.core.types import SimResult
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe
from gi_gi_n_gi_multiclass.metrics.steady_state import time_average_L

def summary_table(res: SimResult) -> pd.DataFrame:
    df = customers_to_dataframe(res)

    # Consider only customers arriving after warmup
    t0 = res.config.warmup_time
    df = df[df["arrival_time"] >= t0].copy()

    served = df[df["outcome"] == "SERVED"].copy()
    abandoned = df[df["outcome"] == "ABANDONED"].copy()

    served["wait"] = served["service_start"] - served["arrival_time"]
    served["sojourn"] = served["service_end"] - served["arrival_time"]

    lam_hat = len(df) / max(1e-9, (res.end_time - t0))
    aband_rate = len(abandoned) / max(1e-9, (res.end_time - t0))
    served_rate = len(served) / max(1e-9, (res.end_time - t0))

    stats = time_average_L(res)

    out = {
        "policy": res.config.policy.name,
        "n_servers": res.config.n_servers,
        "arrivals": int(len(df)),
        "served": int(len(served)),
        "abandoned": int(len(abandoned)),
        "lambda_hat": lam_hat,
        "served_rate": served_rate,
        "abandon_rate": aband_rate,
        "W_mean": float(served["sojourn"].mean()) if len(served) else float("nan"),
        "service_mean": float(df["service_time"].mean()) if len(df) else float("nan"),
        "patience_mean": float(df["patience_time"].mean()) if df["patience_time"].notna().any() else float("nan"),
        "L_timeavg": stats["L"],
        "Lq_timeavg": stats["Lq"],
        "end_time": res.end_time,
    }
    return pd.DataFrame([out])
