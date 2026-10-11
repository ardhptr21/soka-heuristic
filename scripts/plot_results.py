#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

with (RESULTS / "runs.csv").open(newline="") as f:
    runs = list(csv.DictReader(f))
with (RESULTS / "summary.csv").open(newline="") as f:
    summary = list(csv.DictReader(f))

sizes = list(range(1000, 10001, 1000))

def values(rows, field):
    return [float(row[field]) for row in rows]

for size in sizes:
    rows = [r for r in runs if int(r["size"]) == size]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    x = [int(r["repeat"]) for r in rows]
    for ax, field, title, ylabel in [
        (axes[0, 0], "makespan", "Makespan by repetition", "Seconds"),
        (axes[0, 1], "total_cost", "Total cost by repetition", "Cost units"),
        (axes[1, 0], "avg_cpu_utilization", "CPU utilization", "Ratio"),
        (axes[1, 1], "deadline_miss_ratio", "Deadline miss ratio", "Ratio"),
    ]:
        ax.plot(x, values(rows, field), marker="o", color="#4472C4", label="SJF")
        ax.axhline(sum(values(rows, field)) / len(rows), linestyle="--", color="#ED7D31", label="Mean")
        ax.set_title(title)
        ax.set_xlabel("Repeat")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        ax.legend()
    fig.suptitle(f"SJF dry run: {size:,} cloudlets, three repetitions")
    fig.savefig(RESULTS / f"dry_run_{size}.png", dpi=160)
    plt.close(fig)

groups = [r for r in summary if int(r["size"]) in sizes]
overall = next(r for r in summary if int(r["size"]) == 0)
fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
for ax, field, title, ylabel in [
    (axes[0, 0], "makespan_mean", "Mean makespan", "Seconds"),
    (axes[0, 1], "cost_mean", "Mean total cost", "Cost units"),
    (axes[0, 2], "cpu_util_mean", "Mean CPU utilization", "Ratio"),
    (axes[1, 0], "throughput_mean", "Mean throughput", "Cloudlets / second"),
    (axes[1, 1], "imbalance_mean", "Mean load imbalance", "Ratio"),
    (axes[1, 2], "deadline_miss_mean", "Mean deadline miss ratio", "Ratio"),
]:
    ax.plot(sizes, values(groups, field), marker="o", color="#4472C4")
    ax.set_title(title)
    ax.set_xlabel("Cloudlets")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
fig.suptitle("SJF summary across all dry-run sizes")
fig.savefig(RESULTS / "comparison.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
labels = ["Makespan", "Cost", "CPU utilization", "Throughput", "Imbalance", "Deadline misses"]
fields = ["makespan_mean", "cost_mean", "cpu_util_mean", "throughput_mean", "imbalance_mean", "deadline_miss_mean"]
ax.bar(labels, [float(overall[f]) for f in fields], color="#4472C4")
ax.set_title("Overall SJF mean across all 30 runs")
ax.tick_params(axis="x", rotation=25)
ax.grid(axis="y", alpha=0.25)
fig.savefig(RESULTS / "overall.png", dpi=160)
plt.close(fig)
print("Wrote ten dry-run charts, comparison.png, and overall.png")
