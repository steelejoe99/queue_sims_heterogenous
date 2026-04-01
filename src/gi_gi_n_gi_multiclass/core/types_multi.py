from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Any, Literal, Sequence

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
