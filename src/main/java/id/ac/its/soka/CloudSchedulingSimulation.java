package id.ac.its.soka;

import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.Datacenter;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.schedulers.cloudlet.CloudletSchedulerSpaceShared;
import org.cloudsimplus.schedulers.vm.VmSchedulerTimeShared;
import org.cloudsimplus.vms.Vm;
import org.cloudsimplus.vms.VmSimple;
import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.allocationpolicies.VmAllocationPolicySimple;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

public final class CloudSchedulingSimulation {
    // The workload is read from CSV, and reproducible artifacts are written to results/.
    private static final Path WORKLOAD = Path.of("data/workload.csv");
    private static final Path RESULTS = Path.of("results");

    // These sizes and seeds define the repeated experiment runs.
    private static final int[] SIZES = {100, 500, 1000};
    private static final int[] SEEDS = {42,43,44,45,46,47,48,49,50,51};

    // The cost weight is calculated as 1 - timeWeight.
    private static final double[] TIME_WEIGHTS = {0.70, 0.60, 0.50};

    // Algorithms included in the scheduling comparison.
    private static final String[] ALGORITHMS = {"ROUND_ROBIN", "MIN_MIN", "SJF", "MULTI_OBJECTIVE"};

    private record Task(long id, double arrival, long length, int pes, int ramMb, double deadline) {}
    private record VmSpec(int id, String type, int pes, double mips, int ramMb, double cost, int datacenter) {}
    private record Assignment(Task task, VmSpec vm, double start, double finish) {}
    private record RunResult(String algorithm, int size, int seed, double timeWeight, double makespan,
                             double totalCost, double avgCpuUtilization, double throughput,
                             double degreeImbalance, double deadlineMissRatio, int invalidAssignments,
                             double budget, boolean budgetExceeded) {}

    public static void main(String[] args) throws Exception {
        boolean printOutput = Arrays.asList(args).contains("--print-output");
        Set<String> selectedAlgorithms = selectedAlgorithms(args);
        Files.createDirectories(RESULTS);
        List<Task> source = loadOrGenerateWorkload();
        writeConfig(source.size());
        List<RunResult> results = new ArrayList<>();
        // Each workload size is repeated for every seed and algorithm. The
        // multi-objective scheduler also evaluates all three weight combinations.
        for (int size : SIZES) {
            for (int seed : SEEDS) {
                List<Task> randomized = sampledWorkload(source, size, seed);
                for (String algorithm : ALGORITHMS) {
                    if (!selectedAlgorithms.contains("ALL") && !selectedAlgorithms.contains(algorithm)) continue;
                    double[] weights = algorithm.equals("MULTI_OBJECTIVE") ? TIME_WEIGHTS : new double[]{0.60};
                    for (double timeWeight : weights) {
                        boolean printThisRun = printOutput
                            && size == 100
                            && seed == 42
                            && (!algorithm.equals("MULTI_OBJECTIVE") || timeWeight == 0.60);
                        results.add(run(randomized, size, seed, algorithm, timeWeight, printThisRun));
                    }
                }
            }
        }
        writeRuns(results);
        writeAggregates(results);
        System.out.printf(Locale.US, "Completed %d simulation runs. Results: %s%n", results.size(), RESULTS.toAbsolutePath());
    }

    private static Set<String> selectedAlgorithms(String[] args) {
        String value = Arrays.stream(args)
            .filter(arg -> arg.startsWith("--algorithm="))
            .map(arg -> arg.substring("--algorithm=".length()).trim().toUpperCase(Locale.ROOT))
            .findFirst()
            .orElse("ALL");
        Set<String> selected = new LinkedHashSet<>(Arrays.asList(value.split(",")));
        if (selected.contains("ALL") && selected.size() > 1) {
            throw new IllegalArgumentException("ALL cannot be combined with another algorithm.");
        }
        if (!selected.stream().allMatch(name -> name.equals("ALL") || Arrays.asList(ALGORITHMS).contains(name))) {
            throw new IllegalArgumentException(
                "Unknown algorithm in '" + value + "'. Use ALL, ROUND_ROBIN, MIN_MIN, SJF, or MULTI_OBJECTIVE.");
        }
        return selected;
    }

    private static List<Task> loadOrGenerateWorkload() throws IOException {
        if (!Files.exists(WORKLOAD)) {
            Files.createDirectories(WORKLOAD.getParent());
            generateDemoWorkload(WORKLOAD, 1000, 42);
        }
        List<Task> tasks = new ArrayList<>();
        try (BufferedReader r = Files.newBufferedReader(WORKLOAD)) {
            String line; boolean header = true;
            while ((line = r.readLine()) != null) {
                if (line.isBlank()) continue;
                if (header) { header = false; if (line.toLowerCase(Locale.ROOT).startsWith("task_id")) continue; }
                String[] c = line.split(",");
                if (c.length < 5) continue;
                long id = Long.parseLong(c[0].trim());
                double arrival = Double.parseDouble(c[1].trim());
                double duration = Double.parseDouble(c[2].trim());
                double cpu = Double.parseDouble(c[3].trim());
                double memory = Double.parseDouble(c[4].trim());
                // The CSV columns are task_id, start_time, execution_duration,
                // cpu_request, and memory_request_mb.
                if (duration <= 0 || cpu <= 0) continue;
                long length = Math.max(1L, Math.round(duration * 1000.0));
                int pes = cpu <= 1.0 ? 1 : cpu <= 2.0 ? 2 : 4;
                int ram = memory <= 512 ? 512 : memory <= 1024 ? 1024 : memory <= 2048 ? 2048 : 4096;
                tasks.add(new Task(id, Math.max(0, arrival), length, pes, ram, 0));
            }
        }
        if (tasks.size() < 1000) throw new IllegalArgumentException("Workload must contain at least 1000 valid rows");
        double first = tasks.stream().mapToDouble(Task::arrival).min().orElse(0);
        return tasks.stream().map(t -> new Task(t.id, t.arrival - first, t.length, t.pes, t.ramMb, 0)).toList();
    }

    private static void generateDemoWorkload(Path path, int count, long seed) throws IOException {
        Random random = new Random(seed);
        try (BufferedWriter w = Files.newBufferedWriter(path)) {
            w.write("task_id,start_time,execution_duration,cpu_request,memory_request_mb\n");
            double time = 0;
            for (int i = 1; i <= count; i++) {
                time += random.nextDouble() * 2.5;
                double duration = 1 + random.nextDouble() * 80;
                double cpu = switch (random.nextInt(10)) { case 0,1,2,3,4 -> 1; case 5,6,7 -> 2; default -> 4; };
                double memory = switch (random.nextInt(10)) { case 0,1,2 -> 512; case 3,4,5 -> 1024; case 6,7,8 -> 2048; default -> 4096; };
                w.write(String.format(Locale.US, "%d,%.4f,%.4f,%.0f,%.0f%n", i, time, duration, cpu, memory));
            }
        }
    }

    private static List<Task> sampledWorkload(List<Task> tasks, int size, int seed) {
        List<Task> copy = new ArrayList<>(tasks);
        Collections.shuffle(copy, new Random(seed));
        copy = new ArrayList<>(copy.subList(0, size));
        return copy.stream().sorted(Comparator.comparingDouble(Task::arrival).thenComparingLong(Task::id)).toList();
    }

    private static List<VmSpec> vmSpecs() {
        // Each VM definition includes its vCPU count, MIPS, RAM, price, and datacenter.
        return List.of(
            new VmSpec(0,"Small",1,1000,2048,0.010,1), new VmSpec(1,"Small",1,1000,2048,0.010,1),
            new VmSpec(2,"Medium",2,1800,4096,0.018,1), new VmSpec(3,"Large",4,2500,8192,0.032,1),
            new VmSpec(4,"Small",1,1000,2048,0.010,2), new VmSpec(5,"Medium",2,1800,4096,0.018,2),
            new VmSpec(6,"Medium",2,1800,4096,0.018,2), new VmSpec(7,"Large",4,2500,8192,0.032,2));
    }

    private static RunResult run(List<Task> input, int size, int seed, String algorithm, double timeWeight,
                                 boolean printOutput) {
        List<VmSpec> vms = vmSpecs();
        double mediumRuntime = input.stream().mapToDouble(t -> t.length / (2 * 1800.0)).toArray().length == 0 ? 1 : 1;
        // A task's deadline is its arrival time plus 1.5 times the estimated
        // runtime on the reference Medium VM (1,800 MIPS x 2 PEs).
        List<Task> tasks = input.stream().map(t -> new Task(t.id,t.arrival,t.length,t.pes,t.ramMb,t.arrival + 1.5 * t.length / 3600.0)).toList();
        List<Assignment> planned = plan(tasks, vms, algorithm, timeWeight);
        Map<Long, Assignment> byId = planned.stream().collect(Collectors.toMap(a -> a.task.id, a -> a));
        CloudSimPlus simulation = new CloudSimPlus();
        Datacenter dc1 = createDatacenter(simulation, 1);
        Datacenter dc2 = createDatacenter(simulation, 2);
        DatacenterBrokerSimple broker = new DatacenterBrokerSimple(simulation);
        List<Vm> cloudVms = vms.stream().map(s -> createVm(s)).toList();
        broker.setDatacenterMapper((dc, vm) -> vm.getId() < 4 ? dc1 : dc2);
        broker.submitVmList(cloudVms);
        List<Cloudlet> cloudlets = new ArrayList<>();
        for (Task t : tasks) {
            Assignment a = byId.get(t.id);
            CloudletSimple c = new CloudletSimple(t.length, t.pes);
            c.setId(t.id);
            c.setSubmissionDelay(t.arrival);
            c.setFileSize(300);
            c.setOutputSize(300);
            c.setUtilizationModelCpu(new org.cloudsimplus.utilizationmodels.UtilizationModelFull());
            c.setVm(cloudVms.get(a.vm.id));
            cloudlets.add(c);
        }
        broker.submitCloudletList(cloudlets);
        simulation.start();
        List<Cloudlet> finished = broker.getCloudletFinishedList();
        double minArrival = tasks.stream().mapToDouble(Task::arrival).min().orElse(0);
        double lastFinish = finished.stream().mapToDouble(Cloudlet::getFinishTime).max().orElse(0);
        double makespan = Math.max(0, lastFinish - minArrival);
        if (printOutput) printCloudletOutput(finished, vms, algorithm, makespan);
        double totalCost = 0;
        Map<Integer, Double> vmBusy = new HashMap<>();
        int misses = 0;
        for (Cloudlet c : finished) {
            VmSpec s = vms.get((int)c.getVm().getId());
            double cpuTime = Math.max(0, c.getActualCpuTime());
            totalCost += cpuTime * s.cost;
            vmBusy.merge((int)s.id, cpuTime, Double::sum);
            if (c.getFinishTime() > byId.get(c.getId()).task.deadline) misses++;
        }
        double totalBusy = vmBusy.values().stream().mapToDouble(Double::doubleValue).sum();
        double avgUtil = makespan <= 0 ? 0 : totalBusy / (makespan * vms.stream().mapToInt(VmSpec::pes).sum());
        double throughput = makespan <= 0 ? 0 : finished.size() / makespan;
        double maxLoad = vmBusy.values().stream().mapToDouble(Double::doubleValue).max().orElse(0);
        double minLoad = vmBusy.values().stream().mapToDouble(Double::doubleValue).min().orElse(0);
        double imbalance = maxLoad <= 0 ? 0 : (maxLoad - minLoad) / maxLoad;
        double theoretical = tasks.stream().mapToDouble(t -> {
            return vms.stream().filter(v -> v.pes >= t.pes && v.ramMb >= t.ramMb).mapToDouble(v -> (t.length / (v.pes * v.mips)) * v.cost).min().orElse(0);
        }).sum();
        // The budget is 120% of the cheapest feasible theoretical cost. Actual
        // cost uses simulated CPU time multiplied by the selected VM tariff.
        double budget = theoretical * 1.20;
        return new RunResult(algorithm,size,seed,timeWeight,makespan,totalCost,avgUtil,throughput,imbalance,
            tasks.isEmpty()?0:(double)misses/tasks.size(), size-finished.size(), budget, totalCost > budget);
    }

    private static void printCloudletOutput(List<Cloudlet> finished, List<VmSpec> vms,
                                            String algorithm, double makespan) {
        System.out.println();
        System.out.println("================ OUTPUT ================");
        System.out.printf("%-12s %-10s %-15s %-10s %-14s %-14s %-14s%n",
            "Cloudlet ID", "STATUS", "Data center ID", "VM ID", "Time", "Start Time", "Finish Time");
        List<Cloudlet> ordered = finished.stream()
            .sorted(Comparator.comparingDouble(Cloudlet::getFinishTime))
            .toList();
        for (Cloudlet cloudlet : ordered) {
            int vmId = (int) cloudlet.getVm().getId();
            int datacenterId = vms.get(vmId).datacenter;
            System.out.printf(Locale.US, "%02d           %-10s %02d              %02d        %10.2f      %10.2f      %10.2f%n",
                cloudlet.getId(), cloudlet.getStatus(), datacenterId, vmId,
                cloudlet.getActualCpuTime(), cloudlet.getExecStartTime(), cloudlet.getFinishTime());
        }
        System.out.printf(Locale.US, "Makespan using %s: %.6f%n", algorithm, makespan);
        System.out.printf("%s scheduler finished!%n", algorithm);
        System.out.println("==========================================");
    }

    private static List<Assignment> plan(List<Task> tasks, List<VmSpec> vms, String algorithm, double timeWeight) {
        // This method contains the Round Robin, Min-Min, SJF, and weighted
        // multi-objective assignment policies.
        Map<Integer, Double> available = new HashMap<>();
        for (VmSpec v : vms) available.put(v.id, 0.0);
        int rr = 0;
        List<Assignment> result = new ArrayList<>();
        List<Task> orderedTasks = algorithm.equals("SJF")
            ? tasks.stream()
                .sorted(Comparator.comparingLong(Task::length)
                    .thenComparingDouble(Task::arrival)
                    .thenComparingLong(Task::id))
                .toList()
            : tasks;
        for (Task t : orderedTasks) {
            List<VmSpec> feasible = vms.stream().filter(v -> v.pes >= t.pes && v.ramMb >= t.ramMb).toList();
            if (feasible.isEmpty()) { result.add(new Assignment(t, vms.get(0), t.arrival, t.arrival)); continue; }
            VmSpec chosen;
            if (algorithm.equals("ROUND_ROBIN")) {
                final int rrStart = rr;
                chosen = feasible.stream().filter(v -> v.id >= rrStart).findFirst().orElse(feasible.get(0));
                rr = (chosen.id + 1) % vms.size();
            } else if (algorithm.equals("MIN_MIN")) {
                chosen = feasible.stream().min(Comparator.comparingDouble(v -> Math.max(t.arrival, available.get(v.id)) + runtime(t,v))).orElse(feasible.get(0));
            } else if (algorithm.equals("SJF")) {
                // Shortest Job First: process the shortest cloudlets first,
                // then use the earliest-finishing feasible VM for each one.
                chosen = feasible.stream()
                    .min(Comparator.comparingDouble(v -> Math.max(t.arrival, available.get(v.id)) + runtime(t, v)))
                    .orElse(feasible.get(0));
            } else {
                double minFinish = feasible.stream().mapToDouble(v -> Math.max(t.arrival,available.get(v.id)) + runtime(t,v)).min().orElse(0);
                double maxFinish = feasible.stream().mapToDouble(v -> Math.max(t.arrival,available.get(v.id)) + runtime(t,v)).max().orElse(minFinish);
                double minCost = feasible.stream().mapToDouble(v -> runtime(t,v)*v.cost).min().orElse(0);
                double maxCost = feasible.stream().mapToDouble(v -> runtime(t,v)*v.cost).max().orElse(minCost);
                chosen = feasible.stream().min(Comparator.comparingDouble(v -> {
                    double finish = Math.max(t.arrival,available.get(v.id)) + runtime(t,v);
                    double cost = runtime(t,v)*v.cost;
                    double nf = maxFinish == minFinish ? 0 : (finish-minFinish)/(maxFinish-minFinish);
                    double nc = maxCost == minCost ? 0 : (cost-minCost)/(maxCost-minCost);
                    return timeWeight*nf + (1-timeWeight)*nc;
                })).orElse(feasible.get(0));
            }
            double start = Math.max(t.arrival, available.get(chosen.id));
            double finish = start + runtime(t, chosen);
            available.put(chosen.id, finish);
            result.add(new Assignment(t,chosen,start,finish));
        }
        return result;
    }

    // Runtime is derived from the cloudlet length and the VM's processing capacity.
    private static double runtime(Task t, VmSpec v) { return t.length / (v.pes * v.mips); }

    private static Datacenter createDatacenter(CloudSimPlus sim, int dcId) {
        // The simulation uses two heterogeneous datacenters with different host
        // PE, MIPS, RAM, and bandwidth values.
        int[][] specs = dcId == 1 ? new int[][]{{8,3000},{8,2500}} : new int[][]{{12,2200},{16,1800}};
        List<Host> hosts = new ArrayList<>();
        for (int i=0;i<specs.length;i++) {
            List<Pe> pes = new ArrayList<>();
            for (int p=0;p<specs[i][0];p++) pes.add(new PeSimple(specs[i][1]));
            HostSimple h = new HostSimple(dcId == 1 ? 32768 : (i == 0 ? 49152 : 65536), 10_000_000, 1_000_000, pes);
            h.setVmScheduler(new VmSchedulerTimeShared());
            hosts.add(h);
        }
        return new DatacenterSimple(sim, hosts, new VmAllocationPolicySimple());
    }

    private static Vm createVm(VmSpec s) {
        // Create the CloudSim VM and attach the space-shared cloudlet scheduler.
        return new VmSimple(s.mips, s.pes).setRam(s.ramMb).setBw(1000).setSize(10_000)
            .setCloudletScheduler(new CloudletSchedulerSpaceShared());
    }

    private static void writeConfig(int rows) throws IOException {
        // Keep a copy of the main experiment settings beside the CSV results.
        try (BufferedWriter w = Files.newBufferedWriter(RESULTS.resolve("configuration.txt"))) {
            w.write("cloudsim-plus=8.0.0\nworkload_rows="+rows+"\nworkload_sizes=100,500,1000\nseeds=42..51\n");
            w.write("algorithms=ROUND_ROBIN,MIN_MIN,SJF,MULTI_OBJECTIVE\nweights=0.70:0.30,0.60:0.40,0.50:0.50\n");
            w.write("host_scheduler=VmSchedulerTimeShared\ncloudlet_scheduler=CloudletSchedulerSpaceShared\n");
        }
    }

    private static void writeRuns(List<RunResult> results) throws IOException {
        try (BufferedWriter w = Files.newBufferedWriter(RESULTS.resolve("runs.csv"))) {
            w.write("algorithm,size,seed,time_weight,cost_weight,makespan,total_cost,avg_cpu_utilization,throughput,degree_imbalance,deadline_miss_ratio,invalid_assignments,budget,budget_exceeded\n");
            for (RunResult r : results) w.write(String.format(Locale.US,"%s,%d,%d,%.2f,%.2f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%.6f,%s%n",r.algorithm,r.size,r.seed,r.timeWeight,1-r.timeWeight,r.makespan,r.totalCost,r.avgCpuUtilization,r.throughput,r.degreeImbalance,r.deadlineMissRatio,r.invalidAssignments,r.budget,r.budgetExceeded));
        }
    }

    private static void writeAggregates(List<RunResult> rows) throws IOException {
        record Key(String algorithm,int size,double weight) {}
        Map<Key,List<RunResult>> groups = rows.stream().collect(Collectors.groupingBy(r -> new Key(r.algorithm,r.size,r.timeWeight), LinkedHashMap::new, Collectors.toList()));
        try (BufferedWriter w = Files.newBufferedWriter(RESULTS.resolve("summary.csv"))) {
            w.write("algorithm,size,time_weight,cost_weight,runs,makespan_mean,makespan_sd,cost_mean,cost_sd,cpu_util_mean,throughput_mean,imbalance_mean,deadline_miss_mean,budget_exceed_count\n");
            for (var e : groups.entrySet()) { var g=e.getValue(); w.write(String.format(Locale.US,"%s,%d,%.2f,%.2f,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d%n",e.getKey().algorithm,e.getKey().size,e.getKey().weight,1-e.getKey().weight,g.size(),mean(g.stream().mapToDouble(RunResult::makespan).boxed().toList()),sd(g.stream().mapToDouble(RunResult::makespan).boxed().toList()),mean(g.stream().mapToDouble(RunResult::totalCost).boxed().toList()),sd(g.stream().mapToDouble(RunResult::totalCost).boxed().toList()),mean(g.stream().mapToDouble(RunResult::avgCpuUtilization).boxed().toList()),mean(g.stream().mapToDouble(RunResult::throughput).boxed().toList()),mean(g.stream().mapToDouble(RunResult::degreeImbalance).boxed().toList()),mean(g.stream().mapToDouble(RunResult::deadlineMissRatio).boxed().toList()),g.stream().filter(RunResult::budgetExceeded).count())); }
        }
    }
    private static double mean(List<Double> x) { return x.stream().mapToDouble(Double::doubleValue).average().orElse(0); }
    private static double sd(List<Double> x) { if (x.size()<2) return 0; double m=mean(x); return Math.sqrt(x.stream().mapToDouble(v -> (v-m)*(v-m)).sum()/(x.size()-1)); }
}
