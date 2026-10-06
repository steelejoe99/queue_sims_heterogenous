# Examples

Run these scripts from the repository root after installing the package in
editable mode:

```bash
python examples/single_class_fcfs.py
python examples/multiclass_priority.py
python examples/housing_arrivals.py
```

They are intentionally small and use only public package imports. They are
tracked examples, not generated outputs or notebook exports.

| Script | Demonstrates |
|---|---|
| `single_class_fcfs.py` | Conventional GI/GI/N+GI with FCFS and summary metrics. |
| `multiclass_priority.py` | Reusable-server queue with strict class priority and FCFS within class. |
| `housing_arrivals.py` | Consumable housing allocations with annual batches, monthly batches, and renewal arrivals. |
