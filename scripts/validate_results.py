#!/usr/bin/env python3
import csv
import os
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "results" / "runs.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
selected = os.environ.get("SIM_ALGORITHM", "ALL").upper()
expected_algorithms = {"ROUND_ROBIN", "MIN_MIN", "SJF", "MULTI_OBJECTIVE"} if selected == "ALL" else set(selected.split(","))
expected_rows = 180 if selected == "ALL" else sum(90 if algorithm == "MULTI_OBJECTIVE" else 30 for algorithm in expected_algorithms)
assert len(rows) == expected_rows, len(rows)
assert {int(r["size"]) for r in rows} == {100, 500, 1000}
assert {int(r["seed"]) for r in rows} == set(range(42, 52))
assert {r["algorithm"] for r in rows} == expected_algorithms
assert all(int(r["invalid_assignments"]) == 0 for r in rows)
for r in rows:
    for field in ("makespan", "total_cost", "avg_cpu_utilization", "throughput", "degree_imbalance", "deadline_miss_ratio"):
        assert float(r[field]) >= 0, (r, field)
print(f"Validated {len(rows)} runs; all assignments valid and metrics non-negative.")
