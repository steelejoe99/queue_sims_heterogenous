from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Protocol
from gi_gi_n_gi_multiclass.core.state import SystemState

class Policy(Protocol):
    name: str
    def select_customer(self, state: SystemState, now: float) -> Optional[int]: ...
