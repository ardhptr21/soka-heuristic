#!/usr/bin/env python3
import csv
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "results" / "runs.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))

assert os.environ.get("SIM_ALGORITHM", "SJF").upper() == "SJF"
assert len(rows) == 30, len(rows)
assert {r["algorithm"] for r in rows} == {"SJF"}
assert {int(r["size"]) for r in rows} == set(range(1000, 10001, 1000))
assert {int(r["repeat"]) for r in rows} == {1, 2, 3}
assert all(int(r["invalid_assignments"]) == 0 for r in rows)
for r in rows:
    for field in ("makespan", "total_cost", "avg_cpu_utilization", "throughput", "degree_imbalance", "deadline_miss_ratio", "budget"):
        assert float(r[field]) >= 0, (r, field)

with (root / "results" / "summary.csv").open(newline="") as f:
    summary = list(csv.DictReader(f))
assert len(summary) == 11
assert {int(r["size"]) for r in summary} == {0, *range(1000, 10001, 1000)}
assert all(int(r["runs"]) == 30 if int(r["size"]) == 0 else int(r["runs"]) == 3 for r in summary)
print("Validated 30 SJF runs, ten workload sizes, three repetitions per size, and the overall aggregate.")
