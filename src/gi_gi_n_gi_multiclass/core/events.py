"""Deterministically ordered events for the single-class engine.

Events sort by ``(time, priority, sequence)``.  The monotonically increasing
sequence number makes otherwise simultaneous events reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal
import itertools
import heapq

EventType = Literal["ARRIVAL", "SERVICE_END", "ABANDON"]

_counter = itertools.count()

@dataclass(order=True)
class Event:
    time: float
    # tie-breakers ensure deterministic ordering
    priority: int
    seq: int = field(default_factory=lambda: next(_counter), compare=True)
    etype: EventType = field(compare=False, default="ARRIVAL")
    customer_id: int = field(compare=False, default=-1)

class EventQueue:
    """Minimal heap-backed event queue used by :func:`run_sim`."""

    def __init__(self) -> None:
        self._heap: list[Event] = []

    def push(self, ev: Event) -> None:
        """Schedule an event."""
        heapq.heappush(self._heap, ev)

    def pop(self) -> Event:
        """Return the next chronological event."""
        return heapq.heappop(self._heap)

    def __len__(self) -> int:
        return len(self._heap)
