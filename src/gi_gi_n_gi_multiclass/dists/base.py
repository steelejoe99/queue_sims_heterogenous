from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any, Optional

class Distribution(Protocol):
    def sample(self, rng: Any) -> float: ...
    def mean(self) -> Optional[float]: ...
