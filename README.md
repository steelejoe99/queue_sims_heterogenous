# GI/GI/N+GI Queue Simulations

An event-driven Python toolkit for simulating queues with general renewal
arrivals, general service or allocation durations, multiple servers, and
customer abandonment. It also includes a multiclass engine for priority,
classification, and consumable-housing allocation studies.

The package is deliberately organised so that studies configure the public API
and analyse the resulting records; they do not edit event-loop code.

## Install

From the repository root:

```bash
python -m pip install -e .
```

Run the regression checks with:

```bash
python -m unittest discover -s tests -v
```

## Choose the right engine

| Model | Entry point | Use when |
|---|---|---|
| Single-class GI/GI/N(+GI) | `run_sim` | One customer population and a conventional reusable-server queue. |
| Multiclass GI/GI/N(+GI) | `run_sim_multi` | Classes have different arrival, service, patience, or priority rules. |
| Housing allocation mode | `run_sim_multi(..., housing_mode=True)` | Capacity is released over time and each allocated unit is permanently consumed. |

```python
from gi_gi_n_gi_multiclass.core import SimConfig, run_sim
from gi_gi_n_gi_multiclass.dists import Exponential
from gi_gi_n_gi_multiclass.metrics import summary_table
from gi_gi_n_gi_multiclass.policies import FCFS

result = run_sim(
    SimConfig(
        n_servers=10,
        interarrival=Exponential(rate=8.0),
        service=Exponential(rate=1.0),
        patience=Exponential(rate=0.5),
        policy=FCFS(),
        seed=123,
        warmup_time=100.0,
        run_time=500.0,
    )
)
print(summary_table(result))
```

Runnable counterparts of this example are in [`examples/`](examples/).

## Repository guide

```text
src/gi_gi_n_gi_multiclass/   Installable simulation package
  core/                      Event engines, state, configuration, validation
  dists/                     Sampling distributions
  policies/                  Scheduling and allocation rules
  labelling/                 True-to-assigned class classifiers
  metrics/                   Performance measures
  outputs/                   DataFrame conversion and summary tables
  experiments/               Small run and sweep helpers
  fluid/                     Fluid two-threshold numerical solver

examples/                    Short tracked scripts using only public APIs
tests/                       Fast regression tests
docs/                        Design notes and housing-mode configuration guide

00_package_walkthrough/      Package overview notebook
01_singleclass_notebooks/    Single-class policy and theory studies
02_multiclass_notebooks/     Multiclass policy studies
03_homeless_initial_sims/    Early classifier studies
04_homeless_studies/         Applied housing and mortality studies
outputs/                     Versioned study inputs and derived artefacts
```

## Working conventions

- Keep simulation mechanics in `src/`; build new analyses in notebooks or
  `examples/`.
- Construct scenarios with immutable `SimConfig` or `MultiSimConfig` objects.
- Use a fixed seed for a reproducible run; use multiple seeds for reported
  simulation results.
- Treat `customers_to_dataframe(result)` as the common bridge from raw
  simulation records to analysis and plotting.
- The `housing_mode` configuration is a finite-horizon allocation model, not
  a reusable-server queue. See [Housing mode](docs/housing-mode.md).

## Documentation

- [Architecture and public API](docs/architecture.md)
- [Housing-mode arrivals, releases, and eligibility](docs/housing-mode.md)
- [Examples](examples/README.md)

## Scope

This package is a research simulation toolkit. It supports controlled scenario
analysis and model validation; empirical conclusions depend on the inputs,
policy assumptions, and replication design chosen by each study.
