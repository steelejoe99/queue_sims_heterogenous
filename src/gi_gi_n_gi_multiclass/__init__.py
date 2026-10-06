"""Event-driven queueing simulations with abandonment and class priorities.

The package has two complementary engines:

* :func:`core.run_sim` for a conventional single-class GI/GI/N(+GI) queue.
* :func:`core.run_sim_multi` for multiclass, classifier, and consumable-housing
  experiments.

The public modules are intentionally small.  Simulation studies should compose
configuration objects, distributions, policies, and metrics rather than modify
the event engines directly.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    "dists",
    "experiments",
    "fluid",
    "labelling",
    "metrics",
    "outputs",
    "plotting",
    "policies",
]
