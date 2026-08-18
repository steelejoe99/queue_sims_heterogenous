from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Deque, Dict, Optional, Set, Iterable


@dataclass
class MultiSystemState:
    n_servers: int
    n_classes: int
    now: float = 0.0
    idle_servers: int = 0

    # waiting customers per assigned class. In housing mode these are only the
    # customers whose eligibility delay has elapsed.
    waiting_by_class: list[Set[int]] = field(default_factory=list)

    # Arrival order is retained separately so FCFS selection does not scan a
    # large waiting set for every housing placement. Departures are removed
    # lazily when the policy inspects the front of the queue.
    waiting_order_by_class: list[Deque[int]] = field(default_factory=list)

    # customer attributes
    arrival_time: Dict[int, float] = field(default_factory=dict)
    class_id: Dict[int, int] = field(default_factory=dict)
    eligibility_time: Dict[int, float] = field(default_factory=dict)

    # active waiting flag is True while a customer remains in the system and
    # can still abandon, including during the ineligible waiting period.
    active_waiting: Dict[int, bool] = field(default_factory=dict)
    pending_eligibility: Set[int] = field(default_factory=set)

    # in-service tracking. In housing mode this records permanently allocated
    # units and is useful to policies that depend on cumulative allocations.
    in_service: Set[int] = field(default_factory=set)
    in_service_by_class: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.idle_servers = self.n_servers
        if not self.waiting_by_class:
            self.waiting_by_class = [set() for _ in range(self.n_classes)]
        if not self.waiting_order_by_class:
            self.waiting_order_by_class = [deque() for _ in range(self.n_classes)]
        if not self.in_service_by_class:
            self.in_service_by_class = [0 for _ in range(self.n_classes)]

    def add_waiting(self, cid: int, cls: int, arrival: float) -> None:
        self.waiting_by_class[cls].add(cid)
        self.waiting_order_by_class[cls].append(cid)
        self.arrival_time[cid] = arrival
        self.class_id[cid] = cls
        self.active_waiting[cid] = True

    def add_ineligible(self, cid: int, cls: int, arrival: float, eligible_at: float) -> None:
        self.arrival_time[cid] = arrival
        self.class_id[cid] = cls
        self.eligibility_time[cid] = eligible_at
        self.active_waiting[cid] = True
        self.pending_eligibility.add(cid)

    def make_eligible(self, cid: int) -> bool:
        if not self.active_waiting.get(cid, False):
            self.pending_eligibility.discard(cid)
            return False
        cls = self.class_id[cid]
        self.pending_eligibility.discard(cid)
        self.waiting_by_class[cls].add(cid)
        self.waiting_order_by_class[cls].append(cid)
        return True

    def start_service(self, cid: int) -> None:
        cls = self.class_id[cid]
        self.waiting_by_class[cls].discard(cid)
        self.pending_eligibility.discard(cid)
        self.in_service.add(cid)
        self.active_waiting[cid] = False
        self.idle_servers -= 1
        self.in_service_by_class[cls] += 1

    def end_service(self, cid: int) -> None:
        cls = self.class_id[cid]
        self.in_service.discard(cid)
        self.idle_servers += 1
        self.in_service_by_class[cls] -= 1

    def abandon(self, cid: int) -> None:
        cls = self.class_id[cid]
        self.waiting_by_class[cls].discard(cid)
        self.pending_eligibility.discard(cid)
        self.active_waiting[cid] = False

    def add_capacity(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("capacity addition must be nonnegative")
        self.idle_servers += int(amount)

    def has_waiting(self) -> bool:
        return any(len(q) > 0 for q in self.waiting_by_class)

    def waiting_customers(self, cls: int) -> Iterable[int]:
        return self.waiting_by_class[cls]

    def oldest_waiting(self, cls: int) -> Optional[int]:
        """Return the oldest active customer in a class, if one exists."""
        order = self.waiting_order_by_class[cls]
        active = self.waiting_by_class[cls]
        while order and order[0] not in active:
            order.popleft()
        return order[0] if order else None
