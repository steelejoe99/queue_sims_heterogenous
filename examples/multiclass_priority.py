"""Run a multiclass reusable-server queue with strict assigned-class priority."""

from gi_gi_n_gi_multiclass.core import CustomerClass, MultiSimConfig, run_sim_multi
from gi_gi_n_gi_multiclass.dists import Exponential
from gi_gi_n_gi_multiclass.outputs import customers_to_dataframe
from gi_gi_n_gi_multiclass.policies import PriorityFCFS


def main() -> None:
    classes = [
        CustomerClass(
            "priority",
            interarrival=Exponential(rate=1.0),
            service=Exponential(rate=1.0),
            patience=Exponential(rate=0.25),
        ),
        CustomerClass(
            "standard",
            interarrival=Exponential(rate=1.5),
            service=Exponential(rate=1.0),
            patience=Exponential(rate=0.5),
        ),
    ]
    result = run_sim_multi(
        MultiSimConfig(
            n_servers=3,
            classes=classes,
            policy=PriorityFCFS(priority_order=[0, 1]),
            seed=42,
            warmup_time=25.0,
            run_time=100.0,
        )
    )
    customers = customers_to_dataframe(result)
    print(customers.groupby(["true_class_id", "outcome"]).size().rename("customers"))


if __name__ == "__main__":
    main()
