"""Mutable single-class queue state owned by the event engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
import heapq

@dataclass
class SystemState:
    """State visible to single-class policies at each scheduling decision."""
    n_servers: int
    now: float = 0.0
    idle_servers: int = 0

    # Waiting queue holds customer ids; policy decides selection based on times
    waiting: set[int] = field(default_factory=set)

    # Customer attributes needed for policies
    arrival_time: Dict[int, float] = field(default_factory=dict)

    # Active flags for lazy cancellation of abandonment
    active: Dict[int, bool] = field(default_factory=dict)

    # For stats
    in_service: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.idle_servers = self.n_servers

    def add_waiting(self, cid: int, arrival: float) -> None:
        """Register a newly arrived customer as eligible to wait or abandon."""
        self.waiting.add(cid)
        self.arrival_time[cid] = arrival
        self.active[cid] = True

    def start_service(self, cid: int) -> None:
        """Move a waiting customer into service and consume one server."""
        self.waiting.discard(cid)
        self.in_service.add(cid)
        self.active[cid] = False  # no longer eligible to abandon
        self.idle_servers -= 1

    def end_service(self, cid: int) -> None:
        """Release the server used by a completed service."""
        self.in_service.discard(cid)
        self.idle_servers += 1

    def abandon(self, cid: int) -> None:
        """Remove a still-waiting customer after their patience expires."""
        self.waiting.discard(cid)
        self.active[cid] = False
