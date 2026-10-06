"""Run a small conventional GI/GI/N+GI simulation with FCFS service."""

from gi_gi_n_gi_multiclass.core import SimConfig, run_sim
from gi_gi_n_gi_multiclass.dists import Exponential
from gi_gi_n_gi_multiclass.metrics import summary_table
from gi_gi_n_gi_multiclass.policies import FCFS


def main() -> None:
    config = SimConfig(
        n_servers=4,
        interarrival=Exponential(rate=3.5),
        service=Exponential(rate=1.0),
        patience=Exponential(rate=0.4),
        policy=FCFS(),
        seed=42,
        warmup_time=25.0,
        run_time=100.0,
    )
    print(summary_table(run_sim(config)).to_string(index=False))


if __name__ == "__main__":
    main()
