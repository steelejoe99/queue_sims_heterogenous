from __future__ import annotations
import matplotlib.pyplot as plt
from gi_gi_n_gi_multiclass.core.types import SimResult
from gi_gi_n_gi_multiclass.outputs.schemas import event_log_to_dataframe

def plot_event_counts(res: SimResult) -> None:
    ev = event_log_to_dataframe(res)
    if ev is None or len(ev) == 0:
        print("No event log collected. Set collect_event_log=True.")
        return
    counts = ev["etype"].value_counts()
    plt.figure(figsize=(6,4))
    plt.bar(counts.index, counts.values)
    plt.title("Event type counts")
    plt.ylabel("count")
    plt.show()
