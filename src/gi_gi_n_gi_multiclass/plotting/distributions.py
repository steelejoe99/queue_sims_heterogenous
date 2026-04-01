from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

def plot_samples(samples: np.ndarray, title: str) -> None:
    plt.figure(figsize=(6,4))
    plt.hist(samples, bins=40)
    plt.title(title)
    plt.xlabel("value")
    plt.ylabel("count")
    plt.show()
