from __future__ import annotations
import pandas as pd
from gi_gi_n_gi_multiclass.core.engine import run_sim
from gi_gi_n_gi_multiclass.core.types import SimConfig
from gi_gi_n_gi_multiclass.metrics.basic import summary_table

def run_once(cfg: SimConfig) -> pd.DataFrame:
    res = run_sim(cfg)
    return summary_table(res)
