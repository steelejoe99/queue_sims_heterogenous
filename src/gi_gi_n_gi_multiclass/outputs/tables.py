from __future__ import annotations

import pandas as pd
import numpy as np

from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe
from gi_gi_n_gi_multiclass.metrics.steady_state import time_average_L


def class_level_summary(res) -> pd.DataFrame:
    
    """"
    The simulation returns an event-level record of every customer.

    For policy experiments we usually want aggregate statistics, such as:

    • arrival rate  
    • service completion rate  
    • abandonment rate  
    • mean waiting time for served customers  
    • time-average queue length  

    The function below computes these quantities both:

    • for the entire system  
    • separately for each customer class

    This makes it easy to compare how different policies affect each class.
    """

    df = customers_to_dataframe(res)

    t0 = res.config.warmup_time
    T = max(1e-9, res.end_time - t0)
    df = df[df["arrival_time"] >= t0].copy()

    t1 = res.end_time

    def overlap(start, end):
        if start is None or end is None:
            return 0.0
        if not np.isfinite(start) or not np.isfinite(end):
            return 0.0
        s = max(float(start), t0)
        e = min(float(end), t1)
        return max(0.0, e - s)

    served = df[df["outcome"] == "SERVED"].copy()
    if len(served) > 0:
        served["Wq"] = served["service_start"] - served["arrival_time"]
        served["W"] = served["service_end"] - served["arrival_time"]

    stats = time_average_L(res)

    rows = [{
        "scope": "OVERALL",
        "arrivals": int(len(df)),
        "served": int((df["outcome"] == "SERVED").sum()),
        "abandoned": int((df["outcome"] == "ABANDONED").sum()),
        "lambda_hat": float(len(df) / T),
        "served_rate": float((df["outcome"] == "SERVED").sum() / T),
        "abandon_rate": float((df["outcome"] == "ABANDONED").sum() / T),
        "Wq_mean_served": float(served["Wq"].mean()) if len(served) else float("nan"),
        "W_mean_served": float(served["W"].mean()) if len(served) else float("nan"),
        "L_timeavg": float(stats["L"]),
        "Lq_timeavg": float(stats["Lq"]),
    }]

    for cid, g in df.groupby("class_id", sort=True):

        gs = g[g["outcome"] == "SERVED"].copy()

        if len(gs) > 0:
            gs["Wq"] = gs["service_start"] - gs["arrival_time"]
            gs["W"] = gs["service_end"] - gs["arrival_time"]

        # compute class-specific L and Lq
        L_i = 0.0
        Lq_i = 0.0

        for _, r in g.iterrows():

            a = r["arrival_time"]
            s = r["service_start"]
            e = r["service_end"]
            aband = r["abandon_time"]
            out = r["outcome"]

            if out == "SERVED":
                L_i += overlap(a, e)
                Lq_i += overlap(a, s)

            elif out == "ABANDONED":
                L_i += overlap(a, aband)
                Lq_i += overlap(a, aband)

            elif out == "IN_SYSTEM_END":
                L_i += overlap(a, t1)

                if s is None or (not np.isfinite(s)):
                    Lq_i += overlap(a, t1)
                else:
                    Lq_i += overlap(a, s)

        rows.append({
            "scope": f"class_{int(cid)}",
            "arrivals": int(len(g)),
            "served": int((g["outcome"] == "SERVED").sum()),
            "abandoned": int((g["outcome"] == "ABANDONED").sum()),
            "lambda_hat": float(len(g) / T),
            "served_rate": float((g["outcome"] == "SERVED").sum() / T),
            "abandon_rate": float((g["outcome"] == "ABANDONED").sum() / T),
            "Wq_mean_served": float(gs["Wq"].mean()) if len(gs) else float("nan"),
            "W_mean_served": float(gs["W"].mean()) if len(gs) else float("nan"),
            "L_timeavg": float(L_i / T),
            "Lq_timeavg": float(Lq_i / T),
        })

    return pd.DataFrame(rows)

def class_metrics(res, class_id):
    df = customers_to_dataframe(res)
    t0 = res.config.warmup_time
    T = max(1e-9, res.end_time - t0)
    df = df[(df["arrival_time"] >= t0) & (df["class_id"] == class_id)].copy()

    served = df[df["outcome"] == "SERVED"].copy()
    if len(served) > 0:
        served["Wq"] = served["service_start"] - served["arrival_time"]
        served["W"] = served["service_end"] - served["arrival_time"]

    return {
        "arrivals": int(len(df)),
        "served": int((df["outcome"] == "SERVED").sum()),
        "abandoned": int((df["outcome"] == "ABANDONED").sum()),
        "lambda_hat": float(len(df) / T),
        "served_rate": float((df["outcome"] == "SERVED").sum() / T),
        "abandon_rate": float((df["outcome"] == "ABANDONED").sum() / T),
        "Wq_mean_served": float(served["Wq"].mean()) if len(served) else float("nan"),
        "W_mean_served": float(served["W"].mean()) if len(served) else float("nan"),
    }