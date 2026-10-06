"""Compare annual batches, monthly batches, and renewal arrivals in housing mode."""

from __future__ import annotations

from dataclasses import replace

from gi_gi_n_gi_multiclass.core import CustomerClass, MultiSimConfig, run_sim_multi
from gi_gi_n_gi_multiclass.dists import Exponential, LogNormal
from gi_gi_n_gi_multiclass.outputs import customers_to_dataframe
from gi_gi_n_gi_multiclass.policies import PriorityFCFS


def base_config() -> MultiSimConfig:
    """Return shared two-class housing inputs expressed in years."""
    classes = [
        CustomerClass(
            "chronic",
            interarrival=Exponential(rate=80.0),
            service=Exponential(rate=1.0),
            patience=LogNormal(meanlog=1.1, sdlog=0.85),
        ),
        CustomerClass(
            "non_chronic",
            interarrival=Exponential(rate=120.0),
            service=Exponential(rate=1.0),
            patience=LogNormal(meanlog=0.9, sdlog=0.95),
        ),
    ]
    return MultiSimConfig(
        n_servers=100,  # Units added at each housing release.
        classes=classes,
        policy=PriorityFCFS(priority_order=[0, 1]),
        seed=42,
        run_time=2.0,
        housing_mode=True,
        first_housing_release=1.0,
        housing_release_interval=1.0,
        eligibility_delay=0.5,
    )


def print_outcomes(label: str, config: MultiSimConfig) -> None:
    customers = customers_to_dataframe(run_sim_multi(config))
    counts = customers["outcome"].value_counts().to_dict()
    print(f"{label}: arrivals={len(customers)}, outcomes={counts}")


def main() -> None:
    base = base_config()

    # All applicants in a cohort arrive together once each year.
    annual_batches = replace(
        base,
        housing_arrival_mode="batch",
        batch_arrival_counts=[80, 120],
        batch_interval=1.0,
        first_batch_time=0.0,
        last_batch_time=1.0,
    )

    # Smaller cohorts arrive monthly. Counts are per monthly batch.
    monthly_batches = replace(
        base,
        housing_arrival_mode="batch",
        batch_arrival_counts=[7, 10],
        batch_interval=1.0 / 12.0,
        first_batch_time=0.0,
        last_batch_time=11.0 / 12.0,
    )

    # Applicants arrive individually according to each class's interarrival law.
    renewal_arrivals = replace(
        base,
        housing_arrival_mode="renewal",
        last_arrival_time=1.0,
    )

    for label, config in [
        ("annual batches", annual_batches),
        ("monthly batches", monthly_batches),
        ("renewal arrivals", renewal_arrivals),
    ]:
        print_outcomes(label, config)


if __name__ == "__main__":
    main()
