"""Configuration and result records for the single-class simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Literal, Any

class Distribution(Protocol):
    """Minimal sampling interface required by a simulation input."""

    def sample(self, rng: Any) -> float: ...

class Policy(Protocol):
    """Selection interface called when capacity becomes available."""

    name: str
    def select_customer(self, state: "SystemState", now: float) -> Optional[int]: ...

EventType = Literal["ARRIVAL", "SERVICE_END", "ABANDON"]

@dataclass(frozen=True)
class SimConfig:
    """Immutable inputs for one conventional GI/GI/N(+GI) simulation run."""
    n_servers: int
    interarrival: Distribution
    service: Distribution
    patience: Optional[Distribution]
    policy: Policy
    seed: int = 0

    # Horizon controls (choose time-based or arrivals-based; time-based recommended)
    warmup_time: float = 0.0
    run_time: float = 1000.0

    # Logging/collection
    collect_event_log: bool = False

@dataclass
class CustomerRecord:
    """Lifecycle record for one simulated customer."""
    customer_id: int
    arrival_time: float
    service_time: float
    patience_time: Optional[float]
    abandon_time: Optional[float]

    service_start: Optional[float] = None
    service_end: Optional[float] = None
    outcome: Optional[Literal["SERVED", "ABANDONED", "IN_SYSTEM_END"]] = None

@dataclass
class SimResult:
    """Raw records produced by :func:`gi_gi_n_gi_multiclass.core.run_sim`."""
    config: SimConfig
    customers: list[CustomerRecord]
    end_time: float
    event_log: Optional[list[dict]] = None
