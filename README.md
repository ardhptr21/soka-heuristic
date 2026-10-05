# Cloud Scheduling Simulation

This project implements the SOKA Group 2 design brief as a reproducible Java/CloudSim Plus experiment.

## Model

- 2 datacenters, 4 hosts and 8 heterogeneous VMs.
- VM types: 3 Small (1 vCPU, 1,000 MIPS, 2 GB, 0.010 MU/s), 3 Medium (2 vCPU, 1,800 MIPS, 4 GB, 0.018 MU/s), and 2 Large (4 vCPU, 2,500 MIPS, 8 GB, 0.032 MU/s).
- Independent, non-preemptive cloudlets with dynamic submission delays.
- Algorithms: Round Robin, Min-Min, Shortest Job First (SJF) and weighted multi-objective scheduling.
- Workloads: 100, 500 and 1,000 cloudlets; seeds 42 through 51.
- Objective weights: 0.70:0.30, 0.60:0.40 and 0.50:0.50.
- Outputs: per-run CSV, aggregate mean/stddev CSV, and a configuration snapshot.

## Run on the server

```bash
chmod +x run.sh
./run.sh
```

The runner builds the project, clears the previous `results/` directory by default, runs all experiments, validates the CSV output, and generates the charts. SJF sorts cloudlets by ascending length and assigns each cloudlet to the earliest-finishing feasible VM.

To simulate only one algorithm, pass its name. The default `ALL` runs 180 experiments; Round Robin, Min-Min, and SJF each run 30 experiments, while Multi-objective runs 90 experiments because it evaluates three weight combinations:

```bash
./run.sh --algorithm ROUND_ROBIN
./run.sh --algorithm MIN_MIN
./run.sh --algorithm SJF
./run.sh --algorithm MULTI_OBJECTIVE
./run.sh --algorithm SJF,MIN_MIN
```

Multiple algorithms can be selected with a comma-separated list. `ALL` cannot be combined with individual algorithm names.

The runner hides the verbose CloudSim `INFO` messages from the terminal. To print only the detailed cloudlet table and key summaries, run:

```bash
./run.sh --algorithm SJF --print-output
```

With `--algorithm SJF`, the detailed table is printed for the selected representative run. With no algorithm selector, representative tables for all four algorithms are printed. Terminal output is also saved to `simulation.log`.

To show the raw CloudSim event log as well, use:

```bash
./run.sh --show-info
```

Use `./run.sh --keep-previous` when you want to archive the previous results instead of clearing them.

The default run generates a deterministic demo workload when `data/workload.csv` is absent. To obtain a real Google ClusterData2019 sample directly from the public GCS bucket, run:

```bash
python3 scripts/download_google_trace_sample.py --cell a --format parquet --limit 1000 --max-shards 4 --output data/workload_google2019.csv
cp data/workload_google2019.csv data/workload.csv
./run.sh
```

The extractor reads compact public Parquet shards and keeps only clean, non-preempted tasks with one SUBMIT, one SCHEDULE, and one FINISH event. It then applies the documented quartile transformations. The full trace is not downloaded.

The simulator accepts CSV files with columns:

```text
task_id,start_time,execution_duration,cpu_request,memory_request_mb
```

The preprocessing rules are: submission time is relative to the first task, cloudlet length is duration x 1,000 MIPS, CPU requests are mapped to 1/2/4 PEs, and memory is mapped to 512/1024/2048/4096 MB.

## Important implementation decisions

- CPU feasibility compares requested PEs to VM vCPUs; the brief's CPU-vs-RAM wording is treated as a typo.
- VM placement is explicit: DC1 receives 2 Small, 1 Medium and 1 Large; DC2 receives 1 Small, 2 Medium and 1 Large.
- Cloudlet cost is actual simulated CPU time multiplied by the selected VM's MU/s tariff.
- Deadline is arrival time + 1.5 x runtime on a Medium VM.
- Budget is 120% of the cheapest feasible theoretical execution cost for the same workload.
- The scheduler's finish estimate includes the predicted VM queue, while CloudSim Plus performs the actual event simulation.

Results are written to `results/`.

Generate the requested charts and validate the experiment:

```bash
python3 scripts/validate_results.py
python3 scripts/plot_results.py
```
