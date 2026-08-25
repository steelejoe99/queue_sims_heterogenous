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
    if cfg.classify_initial_queue and cfg.classifier is None:
        raise ValueError("classify_initial_queue requires a classifier")

    if cfg.housing_mode:
        if cfg.housing_arrival_mode not in {"batch", "renewal"}:
            raise ValueError("housing_arrival_mode must be 'batch' or 'renewal'")
        if cfg.housing_arrival_mode == "batch":
            if cfg.batch_arrival_counts is None:
                raise ValueError("batch_arrival_counts must be provided in batch housing mode")
            if len(cfg.batch_arrival_counts) != len(cfg.classes):
                raise ValueError("batch_arrival_counts must match number of classes")
            if any(int(x) < 0 or int(x) != x for x in cfg.batch_arrival_counts):
                raise ValueError("batch_arrival_counts must contain nonnegative integers")
            if cfg.batch_interval <= 0:
                raise ValueError("batch_interval must be > 0")
            if cfg.first_batch_time < 0:
                raise ValueError("first_batch_time must be >= 0")
            if cfg.last_batch_time is not None and cfg.last_batch_time < cfg.first_batch_time:
                raise ValueError("last_batch_time must be >= first_batch_time")
        elif cfg.last_arrival_time is not None and cfg.last_arrival_time < 0:
            raise ValueError("last_arrival_time must be >= 0")
        if cfg.initial_queue is not None:
            for customer in cfg.initial_queue:
                if not 0 <= customer.true_class_id < len(cfg.classes):
                    raise ValueError("initial customer true_class_id is out of range")
                if not 0 <= customer.assigned_class_id < len(cfg.classes):
                    raise ValueError("initial customer assigned_class_id is out of range")
                if customer.age < 0:
                    raise ValueError("initial customer age must be nonnegative")
                if customer.residual_patience is not None and customer.residual_patience < 0:
                    raise ValueError("initial customer residual_patience must be nonnegative")
                if customer.remaining_eligibility < 0:
                    raise ValueError("initial customer remaining_eligibility must be nonnegative")
        if cfg.housing_release_interval <= 0:
            raise ValueError("housing_release_interval must be > 0")
        if cfg.first_housing_release < 0:
            raise ValueError("first_housing_release must be >= 0")
        if cfg.initial_housing_stock < 0:
            raise ValueError("initial_housing_stock must be >= 0")
        if cfg.eligibility_delay < 0:
            raise ValueError("eligibility_delay must be >= 0")

    for i, c in enumerate(cfg.classes):
        if c.name is None or str(c.name).strip() == "":
            raise ValueError(f"class {i} has empty name")
        # Distributions validate themselves on sample/mean
