#!/usr/bin/env python3
import csv
import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def read_summary():
    with (RESULTS / "summary.csv").open(newline="") as f:
        return list(csv.DictReader(f))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", default="ALL")
    selected_algorithm = parser.parse_args().algorithm.upper()
    rows = read_summary()
    base = [r for r in rows if r["time_weight"] == "0.60"]
    all_algorithms = ["ROUND_ROBIN", "MIN_MIN", "SJF", "MULTI_OBJECTIVE"]
    algorithms = all_algorithms if selected_algorithm == "ALL" else selected_algorithm.split(",")
    labels = {"ROUND_ROBIN": "Round Robin", "MIN_MIN": "Min-Min", "SJF": "SJF", "MULTI_OBJECTIVE": "Multi-objective"}
    colors = {"ROUND_ROBIN": "#4472C4", "MIN_MIN": "#ED7D31", "SJF": "#A5A5A5", "MULTI_OBJECTIVE": "#70AD47"}

    fig, axes = plt.subplots(3, 2, figsize=(13, 12), constrained_layout=True)
    for row, size in enumerate((100, 500, 1000)):
        selected = [r for r in base if int(r["size"]) == size]
        x = list(range(len(algorithms)))
        ax = axes[row, 0]
        ax2 = ax.twinx()
        makespan = [float(next(r for r in selected if r["algorithm"] == a)["makespan_mean"]) for a in algorithms]
        cost = [float(next(r for r in selected if r["algorithm"] == a)["cost_mean"]) for a in algorithms]
        ax.bar([i - 0.18 for i in x], makespan, 0.36, color="#5B9BD5", label="Makespan")
        ax2.bar([i + 0.18 for i in x], cost, 0.36, color="#FFC000", label="Execution cost")
        ax.set_title(f"Workload: {size} cloudlets")
        ax.set_ylabel("Makespan (s)")
        ax2.set_ylabel("Cost (MU)")
        ax.set_xticks(x, [labels[a] for a in algorithms], rotation=15)
        ax.grid(axis="y", alpha=0.25)
        if row == 0:
            ax.legend(loc="upper left")
            ax2.legend(loc="upper right")

        ax = axes[row, 1]
        util = [float(next(r for r in selected if r["algorithm"] == a)["cpu_util_mean"]) for a in algorithms]
        throughput = [float(next(r for r in selected if r["algorithm"] == a)["throughput_mean"]) for a in algorithms]
        imbalance = [float(next(r for r in selected if r["algorithm"] == a)["imbalance_mean"]) for a in algorithms]
        miss = [float(next(r for r in selected if r["algorithm"] == a)["deadline_miss_mean"]) for a in algorithms]
        ax.bar([i - 0.27 for i in x], util, 0.18, label="CPU utilization")
        ax.bar([i - 0.09 for i in x], imbalance, 0.18, label="Imbalance")
        ax.bar([i + 0.09 for i in x], miss, 0.18, label="Deadline miss")
        ax2 = ax.twinx()
        ax2.bar([i + 0.27 for i in x], throughput, 0.18, color="#A5A5A5", label="Throughput")
        ax.set_title(f"Supporting metrics: {size} cloudlets")
        ax.set_ylabel("Ratios")
        ax2.set_ylabel("Cloudlets/s")
        ax.set_xticks(x, [labels[a] for a in algorithms], rotation=15)
        ax.grid(axis="y", alpha=0.25)
        if row == 0:
            ax.legend(loc="upper left", fontsize=8)
            ax2.legend(loc="upper right", fontsize=8)
    fig.suptitle("Cloud Scheduling Simulation Results", fontsize=16)
    fig.savefig(RESULTS / "comparison.png", dpi=180)
    plt.close(fig)

    sensitivity = [r for r in rows if r["algorithm"] == "MULTI_OBJECTIVE"]
    if not sensitivity:
        print("Wrote comparison.png; sensitivity.png skipped because Multi-objective was not selected.")
        return
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)
    for ax, size in zip(axes, (100, 500, 1000)):
        selected = [r for r in sensitivity if int(r["size"]) == size]
        labels_w = [f'{r["time_weight"]}:{r["cost_weight"]}' for r in selected]
        ax.plot(labels_w, [float(r["makespan_mean"]) for r in selected], marker="o", label="Makespan")
        ax2 = ax.twinx()
        ax2.plot(labels_w, [float(r["cost_mean"]) for r in selected], marker="s", color="#ED7D31", label="Cost")
        ax.set_title(f"{size} cloudlets")
        ax.set_xlabel("Time:cost weight")
        ax.set_ylabel("Makespan (s)")
        ax2.set_ylabel("Cost (MU)")
        ax.grid(alpha=0.25)
    fig.suptitle("Multi-objective Weight Sensitivity")
    fig.savefig(RESULTS / "sensitivity.png", dpi=180)
    plt.close(fig)
    print("Wrote comparison.png and sensitivity.png")

if __name__ == "__main__":
    main()
