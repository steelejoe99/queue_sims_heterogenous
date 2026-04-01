from __future__ import annotations
from .types import SimConfig

def validate_config(cfg: SimConfig) -> None:
    if cfg.n_servers <= 0:
        raise ValueError("n_servers must be positive")
    if cfg.run_time <= 0:
        raise ValueError("run_time must be positive")
    if cfg.warmup_time < 0:
        raise ValueError("warmup_time must be nonnegative")
    if cfg.interarrival is None or cfg.service is None:
        raise ValueError("interarrival and service distributions are required")
