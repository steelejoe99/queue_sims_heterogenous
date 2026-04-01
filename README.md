# GI/GI/N+GI Queue Simulations

This repository provides an event-driven simulator for **GI/GI/N+GI** queues:
- GI interarrival times (renewal arrivals)
- GI service times
- N identical parallel servers
- +GI customer abandonment with i.i.d. patience times

## Quickstart

```bash
pip install -e .
```

```python
from gi_gi_n_gi_multiclass.core.engine import run_sim
from gi_gi_n_gi_multiclass.core.types import SimConfig
from gi_gi_n_gi_multiclass.dists.common import Exponential
from gi_gi_n_gi_multiclass.policies.fcfs import FCFS
from gi_gi_n_gi_multiclass.metrics.basic import summary_table

cfg = SimConfig(
    n_servers=10,
    interarrival=Exponential(rate=8.0),
    service=Exponential(rate=1.0),
    patience=Exponential(rate=0.5),
    policy=FCFS(),
    seed=123,
    warmup_time=100.0,
    run_time=500.0,
    collect_event_log=False,
)
res = run_sim(cfg)
print(summary_table(res))
```

## Folder layout

- `src/gi_gi_n_gi_multiclass/core/`: engine + state + event loop (intended to be stable)
- `src/gi_gi_n_gi_multiclass/dists/`: distribution objects
- `src/gi_gi_n_gi_multiclass/policies/`: FCFS, LCFS, TIQ threshold policies
- `src/gi_gi_n_gi_multiclass/metrics/`: metrics (Wq, Lq, abandonment, etc.)
- `src/gi_gi_n_gi_multiclass/plotting/`: matplotlib plotting utilities
- `src/gi_gi_n_gi_multiclass/experiments/`: sweep helpers and runners
- `notebooks/`: example notebooks (starter templates)
- `tests/`: basic correctness tests

## Notes

- The simulator uses **lazy cancellation** for abandonment events (customers have an `active` flag).
- Metrics can be computed on the full run or restricted to the post-warmup window.
