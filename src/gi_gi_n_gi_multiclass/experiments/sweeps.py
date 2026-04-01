from __future__ import annotations
import itertools
import pandas as pd
from gi_gi_n_gi_multiclass.core.engine import run_sim
from gi_gi_n_gi_multiclass.core.types import SimConfig
from gi_gi_n_gi_multiclass.metrics.basic import summary_table

def sweep(config_factory, grid: dict) -> pd.DataFrame:
    """Sweep parameters.

    config_factory: callable(**params) -> SimConfig
    grid: dict of param -> list of values
    """
    keys = list(grid.keys())
    rows = []
    for values in itertools.product(*[grid[k] for k in keys]):
        params = dict(zip(keys, values))
        cfg: SimConfig = config_factory(**params)
        res = run_sim(cfg)
        tbl = summary_table(res)
        for k, v in params.items():
            tbl[k] = v
        rows.append(tbl)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
