"""Helpers for constructing a realistic initial state for housing studies."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

from gi_gi_n_gi_multiclass.core.engine_multi import run_sim_multi
from gi_gi_n_gi_multiclass.core.types_multi import InitialQueueCustomer, MultiSimConfig


@dataclass(frozen=True)
class HousingQueueSnapshot:
    """Customer-level unresolved queue state at an observed simulation time."""

    customers: tuple[InitialQueueCustomer, ...]
    prehistory_time: float
    time_to_next_housing_release: float
    available_housing: int


def generate_housing_queue_snapshot(
    cfg: MultiSimConfig,
    target_population: int,
    *,
    max_prehistory_time: float = 100.0,
) -> HousingQueueSnapshot:
    """Run an empty system until its unresolved population reaches a target.

    The returned customer-level snapshot preserves the selection-relevant
    history and the residual patience of every survivor. The supplied config
    must describe the baseline prehistory and must not itself contain an
    initial queue. This lets a later intervention study begin with a backlog
    without discarding the historical ages that drive FCFS ordering.
    """
    if not cfg.housing_mode:
        raise ValueError("prehistory snapshots require housing_mode=True")
    if cfg.housing_arrival_mode != "renewal":
        raise ValueError("prehistory snapshots currently require renewal arrivals")
    if cfg.initial_queue is not None:
        raise ValueError("prehistory must start with an empty queue")
    if target_population <= 0:
        raise ValueError("target_population must be positive")
    if max_prehistory_time <= 0:
        raise ValueError("max_prehistory_time must be positive")

    prehistory_cfg = replace(
        cfg,
        warmup_time=0.0,
        run_time=float(max_prehistory_time),
        last_arrival_time=float(max_prehistory_time),
        initial_housing_stock=0,
        collect_event_log=False,
    )
    result = run_sim_multi(prehistory_cfg, _stop_at_population=int(target_population))
    survivors = [customer for customer in result.customers if customer.outcome == "IN_SYSTEM_END"]
    if len(survivors) < target_population:
        raise RuntimeError(
            f"queue reached only {len(survivors)} people within "
            f"{max_prehistory_time:g} years"
        )

    snapshot_time = result.end_time
    initial_customers = []
    for customer in survivors:
        residual_patience = None
        if customer.abandon_time is not None:
            residual_patience = max(0.0, customer.abandon_time - snapshot_time)
        initial_customers.append(
            InitialQueueCustomer(
                true_class_id=customer.true_class_id,
                assigned_class_id=customer.assigned_class_id,
                age=max(0.0, snapshot_time - customer.arrival_time),
                residual_patience=residual_patience,
                remaining_eligibility=max(
                    0.0,
                    (customer.eligibility_time or customer.arrival_time) - snapshot_time,
                ),
            )
        )

    interval = cfg.housing_release_interval
    first = cfg.first_housing_release
    if snapshot_time < first:
        next_release = first
    else:
        periods = math.floor((snapshot_time - first) / interval) + 1
        next_release = first + periods * interval

    return HousingQueueSnapshot(
        customers=tuple(sorted(initial_customers, key=lambda customer: -customer.age)),
        prehistory_time=snapshot_time,
        time_to_next_housing_release=next_release - snapshot_time,
        available_housing=result.final_idle_servers,
    )
