# SOKA SJF Cloud Scheduling Simulation

This project runs only Shortest Job First (SJF) on CloudSim Plus.

## Experiment

- Workload sizes: 1,000 through 10,000 cloudlets.
- Repetitions: three per size.
- Total executions: 30 SJF runs.
- `data/workload.csv` must contain at least 10,000 rows. Each dry run uses the first `size` rows directly; no sampling or replacement is performed.
- Static topology: two datacenters, two hosts per datacenter, and eight VMs.
- Static VM placement: VM 0–1 → Host 0, VM 2–3 → Host 1, VM 4–5 → Host 2, VM 6–7 → Host 3.

For each dry run, `summary.csv` reports the mean and standard deviation across the three repetitions. It also contains one overall row with `size=0`, which summarizes all 30 runs.

## Run

```bash
chmod +x run.sh
./run.sh
```

The only accepted algorithm flag is optional SJF:

```bash
./run.sh --algorithm SJF
./run.sh --print-output
```

The runner builds, clears old results, executes all 30 runs, validates the results, and generates ten per-dry-run charts plus overall charts.

## Input

The simulator reads `data/workload.csv` with columns:

```text
task_id,start_time,execution_duration,cpu_request,memory_request_mb
```

At least 10,000 valid source rows are required. The 10,000-cloudlet dry run loads 10,000 rows directly from this file. Smaller dry runs reuse their prefix rows across repetitions, but no row sampling occurs.

## Outputs

```text
results/runs.csv
results/summary.csv
results/dry_run_1000.png ... results/dry_run_10000.png
results/comparison.png
results/overall.png
results/configuration.txt
```

`runs.csv` contains one row per repetition. `summary.csv` contains ten size means plus the overall aggregate. The charts show each dry run separately and the final SJF summary across all sizes.

The scheduler sorts tasks by ascending cloudlet length, then uses the repeat seed to break equal-priority task and VM finish-time ties. CPU and memory feasibility are checked before assignment. VM placement is enforced by `StaticVmAllocationPolicy`, which reads `VmSpec.hostId`.
