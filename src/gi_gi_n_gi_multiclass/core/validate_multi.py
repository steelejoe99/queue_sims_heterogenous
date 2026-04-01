from __future__ import annotations

from gi_gi_n_gi_multiclass.core.types_multi import MultiSimConfig

def validate_multi_config(cfg: MultiSimConfig) -> None:
    if cfg.n_servers <= 0:
        raise ValueError("n_servers must be > 0")
    if cfg.run_time <= 0:
        raise ValueError("run_time must be > 0")
    if cfg.warmup_time < 0:
        raise ValueError("warmup_time must be >= 0")
    if len(cfg.classes) <= 0:
        raise ValueError("classes must be non-empty")
    if getattr(cfg, "classifier", None) is not None:
        if cfg.classifier.n_classes != len(cfg.classes):
            raise ValueError("classifier size must match number of classes")

    for i, c in enumerate(cfg.classes):
        if c.name is None or str(c.name).strip() == "":
            raise ValueError(f"class {i} has empty name")
        # Distributions validate themselves on sample/mean
