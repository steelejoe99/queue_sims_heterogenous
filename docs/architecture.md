# Architecture and Public API

## Design boundary

The event engines are the package's behavioural core. They own simulation time,
event ordering, random draws, customer state transitions, and capacity
accounting. A study should configure an engine and inspect its result rather
than editing an engine.

```text
configuration + distributions + policy
                 |
                 v
             core engine
                 |
                 v
       customer records / event log
                 |
                 v
       outputs, metrics, plots, notebooks
```

## Main components

| Location | Responsibility | Public starting points |
|---|---|---|
| `core/` | Event queues, mutable state, config validation, result records | `run_sim`, `run_sim_multi` |
| `dists/` | Random sampling distributions | `Exponential`, `ErlangK`, `Weibull`, `LogNormal`, `Deterministic` |
| `policies/` | Customer selection when capacity is available | `FCFS`, `LCFS`, `TIQ`, `PriorityFCFS`, `NaiveFCFS`, `MostlyFCFS`, `MTIQ` |
| `labelling/` | Maps a true class to an observed or assigned class | `ConfusionMatrixClassifier` |
| `outputs/` | Converts records into tabular data | `customers_to_dataframe`, `event_log_to_dataframe` |
| `metrics/` | Computes performance measures | `summary_table`, `time_average_L`, abandonment metrics |
| `experiments/` | Small conventional repeat-run helpers | `run_once`, `sweep` |
| `fluid/` | Fluid-model threshold calculation | `solve_two_threshold_fluid` |

## Simulation lifecycle

1. Create one or more `CustomerClass` definitions or a single `SimConfig`.
2. Choose a policy. Policies may inspect current state but do not draw random
   values or schedule events.
3. Run the relevant engine.
4. Convert `result.customers` with `customers_to_dataframe`.
5. Compute metrics or create figures outside the engine.

## Reproducibility

Each engine separates random streams for arrivals, service requirements,
patience, and class assignment. Consequently, a fixed seed creates a
repeatable run and changing the classifier does not inadvertently change the
underlying arrival stream.

For reported studies, vary the seed and aggregate outcomes. A single seed is
appropriate for a diagnostic or a reproducible worked example, not for a
precision claim.

## Extending the package

Add a distribution by implementing `sample(rng) -> float` and, when useful,
`mean`, `cdf`, `survival`, `pdf`, and `hazard`. Add a policy by implementing
`select_customer(state, now) -> customer_id | None`.

If a feature changes event ordering or a state transition, add a focused test
under `tests/` before changing an engine. This keeps policy experiments and
the housing studies insulated from internal changes.
