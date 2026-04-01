from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Set, Iterable

@dataclass
class MultiSystemState:
    n_servers: int
    n_classes: int
    now: float = 0.0
    idle_servers: int = 0

    # waiting customers per class
    waiting_by_class: list[Set[int]] = field(default_factory=list)

    # customer attributes
    arrival_time: Dict[int, float] = field(default_factory=dict)
    class_id: Dict[int, int] = field(default_factory=dict)

    # active waiting flag (True iff still waiting and can abandon)
    active_waiting: Dict[int, bool] = field(default_factory=dict)

    # in-service tracking
    in_service: Set[int] = field(default_factory=set)
    in_service_by_class: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.idle_servers = self.n_servers
        if not self.waiting_by_class:
            self.waiting_by_class = [set() for _ in range(self.n_classes)]
        if not self.in_service_by_class:
            self.in_service_by_class = [0 for _ in range(self.n_classes)]

    def add_waiting(self, cid: int, cls: int, arrival: float) -> None:
        self.waiting_by_class[cls].add(cid)
        self.arrival_time[cid] = arrival
        self.class_id[cid] = cls
        self.active_waiting[cid] = True

    def start_service(self, cid: int) -> None:
        cls = self.class_id[cid]
        self.waiting_by_class[cls].discard(cid)
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
        self.active_waiting[cid] = False

    def has_waiting(self) -> bool:
        return any(len(q) > 0 for q in self.waiting_by_class)

    def waiting_customers(self, cls: int) -> Iterable[int]:
        return self.waiting_by_class[cls]
