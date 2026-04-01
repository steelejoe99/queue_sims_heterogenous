from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from gi_gi_n_gi_multiclass.core.types import SimResult
from gi_gi_n_gi_multiclass.outputs.schemas import customers_to_dataframe
from gi_gi_n_gi_multiclass.metrics.steady_state import time_average_L

def plot_wait_times(res: SimResult, max_points: int = 5000) -> None:
    df = customers_to_dataframe(res)
    df = df[(df["arrival_time"] >= res.config.warmup_time) & (df["outcome"] == "SERVED")].copy()
    if len(df) == 0:
        print("No served customers post-warmup.")
        return
    df["wait"] = df["service_start"] - df["arrival_time"]
    df = df.iloc[:max_points]
    plt.figure(figsize=(10,4))
    plt.plot(df["customer_id"].values, df["wait"].values)
    plt.xlabel("customer_id")
    plt.ylabel("wait (time units)")
    plt.title(f"Wait times ({res.config.policy.name}), N={res.config.n_servers}")
    plt.show()

def plot_queue_samples(res: SimResult, dt: float = 0.5) -> None:
    stats = time_average_L(res, dt=dt)
    plt.figure(figsize=(6,4))
    plt.bar(["L","Lq"], [stats["L"], stats["Lq"]])
    plt.ylabel("time-average")
    plt.title(f"Time-average L, Lq (dt={dt})")
    plt.show()
