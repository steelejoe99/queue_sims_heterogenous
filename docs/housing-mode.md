# Housing Allocation Mode

Housing mode is enabled with `MultiSimConfig(housing_mode=True)`. It uses the
multiclass event engine but changes the capacity model:

- `n_servers` is the number of units released at each housing-release epoch.
- A selected customer is marked `SERVED` for compatibility with the common
  metrics, but their allocation consumes a unit permanently.
- `initial_housing_stock` supplies units available at time zero.
- `eligibility_delay` prevents allocation until the delay has elapsed.
- Customers can abandon before becoming eligible or while waiting.

## Arrival choices

### Periodic batches

Use batches when a cohort arrives together. `batch_arrival_counts` is ordered
exactly as `classes`.

```python
MultiSimConfig(
    ...,
    housing_mode=True,
    housing_arrival_mode="batch",
    batch_arrival_counts=[80, 120],
    batch_interval=1.0,          # annual batches in year units
    first_batch_time=0.0,
    last_batch_time=5.0,
)
```

For monthly batches, use `batch_interval=1.0 / 12.0` and express the final
batch time in the same units. No changes to the engine are needed.

### Standard renewal arrivals

Use renewal arrivals when applicants arrive individually. Each true class uses
its own `CustomerClass.interarrival` distribution.

```python
MultiSimConfig(
    ...,
    housing_mode=True,
    housing_arrival_mode="renewal",
    last_arrival_time=5.0,
)
```

## Housing releases

Housing releases are independent of the arrival mode:

```python
MultiSimConfig(
    ...,
    n_servers=100,                 # units per release
    first_housing_release=1.0,
    housing_release_interval=1.0,  # annual releases
    initial_housing_stock=0,
)
```

At each release, the policy selects from eligible waiting customers until the
newly available stock is exhausted. In strict priority studies,
`PriorityFCFS(priority_order=[0, 1])` gives assigned class `0` priority and
uses FCFS within that class.

## Output interpretation

Housing allocations are labelled `SERVED` so reusable-queue and housing-mode
metrics can use one common vocabulary. In housing studies, interpret `SERVED`
as *housed or allocated*, not as a temporary service completion.

The short runnable housing configurations live in
[`examples/housing_arrivals.py`](../examples/housing_arrivals.py).
