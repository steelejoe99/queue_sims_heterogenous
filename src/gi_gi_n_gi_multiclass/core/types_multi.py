from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Literal, Sequence

from gi_gi_n_gi_multiclass.core.types import Distribution


class MultiPolicy(Protocol):
    name: str

    def select_customer(self, state: "MultiSystemState", now: float) -> Optional[int]: ...


@dataclass(frozen=True)
class CustomerClass:
    name: str
    interarrival: Distribution
    service: Distribution
    patience: Optional[Distribution] = None

    # Optional cost parameters (used later for Bassamboo-style objectives)
    holding_cost: float = 1.0
    abandon_penalty: float = 1.0


@dataclass(frozen=True)
class MultiSimConfig:
    n_servers: int
    classes: Sequence[CustomerClass]
    policy: MultiPolicy
    seed: int = 0

    warmup_time: float = 0.0
    run_time: float = 1000.0

    classifier: Optional[object] = None
    collect_event_log: bool = False

    # Optional consumable-housing mode. The default preserves the original
    # reusable-server queue exactly.
    housing_mode: bool = False

    # Housing arrivals can either be periodic true-class batches or ordinary
    # renewal arrivals driven by each CustomerClass.interarrival distribution.
    # Batch mode remains the default for backwards compatibility.
    housing_arrival_mode: Literal["batch", "renewal"] = "batch"

    # In batch mode, one batch of true-class arrivals is added every
    # batch_interval. Counts are ordered exactly as `classes`. For example,
    # use 1.0 for annual batches or 1.0 / 12.0 for monthly batches.
    batch_arrival_counts: Optional[Sequence[int]] = None
    batch_interval: float = 1.0
    first_batch_time: float = 0.0
    last_batch_time: Optional[float] = None

    # In renewal mode, arrivals stop after this time. If omitted, arrivals
    # continue through the simulation end time.
    last_arrival_time: Optional[float] = None

    # Optional true-class counts already waiting at simulation time zero.
    # These people follow the usual eligibility and abandonment rules.
    initial_queue_counts: Optional[Sequence[int]] = None

    # In housing mode, `n_servers` is the number of housing units released at
    # each housing epoch. Units are consumed permanently when allocated.
    housing_release_interval: float = 1.0
    first_housing_release: float = 1.0
    initial_housing_stock: int = 0

    # Customers can abandon immediately, but cannot be selected for housing
    # until this delay has elapsed.
    eligibility_delay: float = 1.0


@dataclass
class MultiCustomerRecord:
    customer_id: int
    class_id: int

    arrival_time: float
    service_time: float
    patience_time: Optional[float]
    abandon_time: Optional[float]

    service_start: Optional[float] = None
    service_end: Optional[float] = None
    eligibility_time: Optional[float] = None

    true_class_id: int = 0
    assigned_class_id: int = 0

    outcome: Optional[Literal["SERVED", "ABANDONED", "IN_SYSTEM_END"]] = None


@dataclass
class MultiSimResult:
    config: MultiSimConfig
    customers: list[MultiCustomerRecord]
    end_time: float
    event_log: Optional[list[dict]] = None


# forward declaration for type checkers
from gi_gi_n_gi_multiclass.core.multi_state import MultiSystemState  # noqa: E402
