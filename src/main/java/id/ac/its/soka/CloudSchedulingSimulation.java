package id.ac.its.soka;

import org.cloudsimplus.allocationpolicies.VmAllocationPolicySimple;
import org.cloudsimplus.brokers.DatacenterBrokerSimple;
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

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

public final class CloudSchedulingSimulation {
    private static final Path WORKLOAD = Path.of("data/workload.csv");
    private static final Path RESULTS = Path.of("results");
    private static final int MIN_SOURCE_ROWS = 10_000;
    private static final int[] SIZES = {1_000,2_000,3_000,4_000,5_000,6_000,7_000,8_000,9_000,10_000};
    private static final int REPEATS = 3;
    private static final String ALGORITHM = "SJF";

    private record Task(long id,double arrival,long length,int pes,int ramMb,double deadline) {}
    private record VmSpec(int id,String type,int pes,double mips,int ramMb,double cost,int dcId,int hostId) {}
    private record Assignment(Task task,VmSpec vm,double start,double finish) {}
    private record RunResult(String algorithm,int size,int repeat,int seed,double makespan,double totalCost,
                             double avgCpuUtilization,double throughput,double degreeImbalance,
                             double deadlineMissRatio,int invalidAssignments,double budget,boolean budgetExceeded) {}

    public static void main(String[] args) throws Exception {
        boolean printOutput = Arrays.asList(args).contains("--print-output");
        validateAlgorithmArgument(args); Files.createDirectories(RESULTS);
        List<Task> source = loadOrGenerateWorkload(); writeConfig(source.size());
        List<RunResult> results = new ArrayList<>();
        // Each dry run repeats its size three times. The rows come directly from
        // workload.csv; no sampling or replacement is performed.
        for (int size : SIZES) for (int repeat = 1; repeat <= REPEATS; repeat++) {
            int seed = 42 + repeat - 1;
            results.add(run(workloadSlice(source,size),size,repeat,seed,printOutput && size == 1_000 && repeat == 1));
        }
        writeRuns(results); writeAggregates(results);
        System.out.printf(Locale.US,"Completed %d SJF simulation runs across workload sizes 1000..10000.%n",results.size());
        System.out.printf("Results: %s%n",RESULTS.toAbsolutePath());
    }

    private static void validateAlgorithmArgument(String[] args) {
        String selected = Arrays.stream(args).filter(a -> a.startsWith("--algorithm="))
            .map(a -> a.substring("--algorithm=".length()).trim().toUpperCase(Locale.ROOT)).findFirst().orElse(ALGORITHM);
        if (!ALGORITHM.equals(selected)) throw new IllegalArgumentException("This project runs SJF only. Use --algorithm=SJF or omit the flag.");
    }

    private static List<Task> loadOrGenerateWorkload() throws IOException {
        if (!Files.exists(WORKLOAD)) { Files.createDirectories(WORKLOAD.getParent()); generateDemoWorkload(WORKLOAD,MIN_SOURCE_ROWS,42); }
        List<Task> tasks = new ArrayList<>();
        try (BufferedReader reader = Files.newBufferedReader(WORKLOAD)) {
            String line; boolean header = true;
            while ((line = reader.readLine()) != null) {
                if (line.isBlank()) continue;
                if (header) { header = false; if (line.toLowerCase(Locale.ROOT).startsWith("task_id")) continue; }
                String[] c = line.split(",",-1); if (c.length < 5) continue;
                long id = Long.parseLong(c[0].trim()); double arrival = Double.parseDouble(c[1].trim());
                double duration = Double.parseDouble(c[2].trim()); double cpu = Double.parseDouble(c[3].trim());
                double memory = Double.parseDouble(c[4].trim()); if (duration <= 0 || cpu <= 0 || memory <= 0) continue;
                long length = Math.max(1L,Math.round(duration * 1000.0));
                int pes = cpu <= 1 ? 1 : cpu <= 2 ? 2 : 4;
                int ram = memory <= 512 ? 512 : memory <= 1024 ? 1024 : memory <= 2048 ? 2048 : 4096;
                tasks.add(new Task(id,Math.max(0,arrival),length,pes,ram,0));
            }
        }
        if (tasks.size() < MIN_SOURCE_ROWS) throw new IllegalArgumentException("Workload must contain at least " + MIN_SOURCE_ROWS + " valid rows");
        double first = tasks.stream().mapToDouble(Task::arrival).min().orElse(0);
        return tasks.stream().map(t -> new Task(t.id,t.arrival-first,t.length,t.pes,t.ramMb,0)).toList();
    }

    private static List<Task> workloadSlice(List<Task> source,int size) {
        if (source.size() < size) throw new IllegalArgumentException("Workload has " + source.size() + " rows; need " + size);
        return source.subList(0,size).stream()
            .sorted(Comparator.comparingDouble(Task::arrival).thenComparingLong(Task::id)).toList();
    }

    private static void generateDemoWorkload(Path path,int count,long seed) throws IOException {
        Random random = new Random(seed);
        try (BufferedWriter writer = Files.newBufferedWriter(path)) {
            writer.write("task_id,start_time,execution_duration,cpu_request,memory_request_mb\n"); double time = 0;
            for (int i = 1; i <= count; i++) {
                time += random.nextDouble()*2.5; double duration = 1 + random.nextDouble()*80;
                double cpu = switch (random.nextInt(10)) { case 0,1,2,3,4 -> 1; case 5,6,7 -> 2; default -> 4; };
                double memory = switch (random.nextInt(10)) { case 0,1,2 -> 512; case 3,4,5 -> 1024; case 6,7,8 -> 2048; default -> 4096; };
                writer.write(String.format(Locale.US,"%d,%.4f,%.4f,%.0f,%.0f%n",i,time,duration,cpu,memory));
            }
        }
    }

    private static List<VmSpec> vmSpecs() {
        return List.of(
            new VmSpec(0,"Small",1,1000,2048,0.010,1,0),new VmSpec(1,"Small",1,1000,2048,0.010,1,0),
            new VmSpec(2,"Medium",2,1800,4096,0.018,1,1),new VmSpec(3,"Large",4,2500,8192,0.032,1,1),
            new VmSpec(4,"Small",1,1000,2048,0.010,2,2),new VmSpec(5,"Small",1,1000,2048,0.010,2,2),
            new VmSpec(6,"Medium",2,1800,4096,0.018,2,3),new VmSpec(7,"Large",4,2500,8192,0.032,2,3));
    }

    private static RunResult run(List<Task> input,int size,int repeat,int seed,boolean printOutput) {
        List<VmSpec> vms = vmSpecs();
        List<Task> tasks = input.stream().map(t -> new Task(t.id,t.arrival,t.length,t.pes,t.ramMb,t.arrival+1.5*t.length/3600.0)).toList();
        List<Assignment> planned = planSjf(tasks,vms,seed);
        Map<Long,Assignment> byId = planned.stream().collect(Collectors.toMap(a -> a.task.id,a -> a));
        CloudSimPlus simulation = new CloudSimPlus(); Datacenter dc1 = createDatacenter(simulation,1,vms), dc2 = createDatacenter(simulation,2,vms);
        DatacenterBrokerSimple broker = new DatacenterBrokerSimple(simulation); List<Vm> cloudVms = vms.stream().map(CloudSchedulingSimulation::createVm).toList();
        broker.setDatacenterMapper((dc,vm) -> vm.getId() < 4 ? dc1 : dc2); broker.submitVmList(cloudVms);
        List<Cloudlet> cloudlets = new ArrayList<>();
        for (Task task : tasks) {
            CloudletSimple cloudlet = new CloudletSimple(task.length,task.pes); cloudlet.setId(task.id); cloudlet.setSubmissionDelay(task.arrival);
            cloudlet.setFileSize(300); cloudlet.setOutputSize(300); cloudlet.setUtilizationModelCpu(new org.cloudsimplus.utilizationmodels.UtilizationModelFull());
            cloudlet.setVm(cloudVms.get(byId.get(task.id).vm.id)); cloudlets.add(cloudlet);
        }
        broker.submitCloudletList(cloudlets); simulation.start(); List<Cloudlet> finished = broker.getCloudletFinishedList();
        double minArrival = tasks.stream().mapToDouble(Task::arrival).min().orElse(0), lastFinish = finished.stream().mapToDouble(Cloudlet::getFinishTime).max().orElse(0), makespan = Math.max(0,lastFinish-minArrival), totalCost = 0;
        Map<Integer,Double> busy = new HashMap<>(); int misses = 0;
        for (Cloudlet cloudlet : finished) { VmSpec vm = vms.get((int)cloudlet.getVm().getId()); double cpuTime = Math.max(0,cloudlet.getActualCpuTime()); totalCost += cpuTime*vm.cost; busy.merge(vm.id,cpuTime,Double::sum); if (cloudlet.getFinishTime() > byId.get(cloudlet.getId()).task.deadline) misses++; }
        double totalBusy = busy.values().stream().mapToDouble(Double::doubleValue).sum(); double utilization = makespan <= 0 ? 0 : totalBusy/(makespan*vms.stream().mapToInt(VmSpec::pes).sum());
        double throughput = makespan <= 0 ? 0 : finished.size()/makespan; double maxLoad = busy.values().stream().mapToDouble(Double::doubleValue).max().orElse(0), minLoad = busy.values().stream().mapToDouble(Double::doubleValue).min().orElse(0), imbalance = maxLoad <= 0 ? 0 : (maxLoad-minLoad)/maxLoad;
        double theoretical = tasks.stream().mapToDouble(t -> vms.stream().filter(v -> v.pes >= t.pes && v.ramMb >= t.ramMb).mapToDouble(v -> (t.length/(v.pes*v.mips))*v.cost).min().orElse(0)).sum(); double budget = theoretical*1.20;
        if (printOutput) printCloudletOutput(finished,vms,makespan);
        return new RunResult(ALGORITHM,size,repeat,seed,makespan,totalCost,utilization,throughput,imbalance,tasks.isEmpty()?0:(double)misses/tasks.size(),size-finished.size(),budget,totalCost > budget);
    }

    private static List<Assignment> planSjf(List<Task> tasks,List<VmSpec> vms,int seed) {
        Random random = new Random(seed);
        Map<Long,Double> taskTieBreak = tasks.stream().collect(Collectors.toMap(Task::id,t -> random.nextDouble()));
        Map<Integer,Double> vmTieBreak = vms.stream().collect(Collectors.toMap(VmSpec::id,v -> random.nextDouble()));
        Map<Integer,Double> available = new HashMap<>(); for (VmSpec vm : vms) available.put(vm.id,0.0); List<Assignment> result = new ArrayList<>();
        List<Task> ordered = tasks.stream().sorted(Comparator.comparingLong(Task::length).thenComparingDouble(Task::arrival).thenComparingDouble(t -> taskTieBreak.get(t.id))).toList();
        for (Task task : ordered) {
            VmSpec chosen = vms.stream().filter(vm -> vm.pes >= task.pes && vm.ramMb >= task.ramMb).min(Comparator.comparingDouble((VmSpec vm) -> Math.max(task.arrival,available.get(vm.id))+runtime(task,vm)).thenComparingDouble(vm -> vmTieBreak.get(vm.id))).orElse(vms.get(0));
            double start = Math.max(task.arrival,available.get(chosen.id)), finish = start+runtime(task,chosen); available.put(chosen.id,finish); result.add(new Assignment(task,chosen,start,finish));
        }
        return result;
    }

    private static double runtime(Task task,VmSpec vm) { return task.length/(vm.pes*vm.mips); }

    private static Datacenter createDatacenter(CloudSimPlus sim,int dcId,List<VmSpec> specs) {
        int[][] hostSpecs = dcId == 1 ? new int[][]{{8,3000},{8,2500}} : new int[][]{{12,2200},{16,1800}}; List<Host> hosts = new ArrayList<>(); int firstHost = dcId == 1 ? 0 : 2;
        for (int i=0;i<2;i++) { List<Pe> pes = new ArrayList<>(); for (int p=0;p<hostSpecs[i][0];p++) pes.add(new PeSimple(hostSpecs[i][1])); HostSimple host = new HostSimple(dcId == 1 ? 32768 : (i == 0 ? 49152 : 65536),10_000_000,1_000_000,pes); host.setId(firstHost+i); host.setVmScheduler(new VmSchedulerTimeShared()); hosts.add(host); }
        return new DatacenterSimple(sim,hosts,new StaticVmAllocationPolicy(specs));
    }

    private static Vm createVm(VmSpec spec) {
        VmSimple vm = new VmSimple(spec.mips,spec.pes);
        vm.setId(spec.id); vm.setRam(spec.ramMb); vm.setBw(1000); vm.setSize(10_000);
        vm.setCloudletScheduler(new CloudletSchedulerSpaceShared());
        return vm;
    }

    private static final class StaticVmAllocationPolicy extends VmAllocationPolicySimple {
        private final Map<Integer,Integer> vmToHost;
        StaticVmAllocationPolicy(List<VmSpec> specs) { vmToHost = specs.stream().collect(Collectors.toUnmodifiableMap(VmSpec::id,VmSpec::hostId)); }
        @Override public org.cloudsimplus.hosts.HostSuitability allocateHostForVm(Vm vm) { Integer hostId = vmToHost.get((int)vm.getId()); if (hostId == null) return org.cloudsimplus.hosts.HostSuitability.NULL; return getHostList().stream().filter(host -> host.getId() == hostId).findFirst().map(host -> host.createVm(vm)).orElse(org.cloudsimplus.hosts.HostSuitability.NULL); }
    }

    private static void printCloudletOutput(List<Cloudlet> finished,List<VmSpec> vms,double makespan) {
        System.out.println("\n================ OUTPUT ================"); System.out.printf("%-12s %-10s %-15s %-10s %-14s %-14s %-14s%n","Cloudlet ID","STATUS","Data center ID","VM ID","Time","Start Time","Finish Time");
        finished.stream().sorted(Comparator.comparingDouble(Cloudlet::getFinishTime)).forEach(c -> { int vmId=(int)c.getVm().getId(); System.out.printf(Locale.US,"%-12d %-10s %-15d %-10d %-14.2f %-14.2f %-14.2f%n",c.getId(),c.getStatus(),vms.get(vmId).dcId,vmId,c.getActualCpuTime(),c.getExecStartTime(),c.getFinishTime()); });
        System.out.printf(Locale.US,"Makespan using SJF: %.6f%nSJF scheduler finished!%n",makespan); System.out.println("==========================================");
    }

    private static void writeConfig(int rows) throws IOException { try (BufferedWriter w=Files.newBufferedWriter(RESULTS.resolve("configuration.txt"))) { w.write("cloudsim-plus=8.0.0\nsource_rows="+rows+"\nrequired_source_rows=10000\nworkload_sizes=1000,2000,3000,4000,5000,6000,7000,8000,9000,10000\nrepeats_per_size=3\nalgorithm=SJF\nworkload_selection=first size rows from workload.csv; no sampling\ntopology=2 datacenters; 2 hosts per datacenter; 2 VMs per host\nvm_allocation=static VmSpec.hostId mapping\n"); } }

    private static void writeRuns(List<RunResult> results) throws IOException { try (BufferedWriter w=Files.newBufferedWriter(RESULTS.resolve("runs.csv"))) { w.write("algorithm,size,repeat,seed,makespan,total_cost,avg_cpu_utilization,throughput,degree_imbalance,deadline_miss_ratio,invalid_assignments,budget,budget_exceeded\n"); for (RunResult r:results) w.write(String.format(Locale.US,"%s,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%.6f,%s%n",r.algorithm,r.size,r.repeat,r.seed,r.makespan,r.totalCost,r.avgCpuUtilization,r.throughput,r.degreeImbalance,r.deadlineMissRatio,r.invalidAssignments,r.budget,r.budgetExceeded)); } }

    private static void writeAggregates(List<RunResult> rows) throws IOException {
        record Key(int size) {}
        Map<Key,List<RunResult>> groups=rows.stream().collect(Collectors.groupingBy(r -> new Key(r.size),LinkedHashMap::new,Collectors.toList())); groups.put(new Key(0),new ArrayList<>(rows));
        try (BufferedWriter w=Files.newBufferedWriter(RESULTS.resolve("summary.csv"))) { w.write("algorithm,size,runs,makespan_mean,makespan_sd,cost_mean,cost_sd,cpu_util_mean,throughput_mean,imbalance_mean,deadline_miss_mean,budget_exceed_count\n"); for (var e:groups.entrySet()) { List<RunResult> g=e.getValue(); w.write(String.format(Locale.US,"%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d%n",ALGORITHM,e.getKey().size,g.size(),mean(g,RunResult::makespan),sd(g,RunResult::makespan),mean(g,RunResult::totalCost),sd(g,RunResult::totalCost),mean(g,RunResult::avgCpuUtilization),mean(g,RunResult::throughput),mean(g,RunResult::degreeImbalance),mean(g,RunResult::deadlineMissRatio),g.stream().filter(RunResult::budgetExceeded).count())); } }
    }
    private static double mean(List<RunResult> x,java.util.function.ToDoubleFunction<RunResult> f) { return x.stream().mapToDouble(f).average().orElse(0); }
    private static double sd(List<RunResult> x,java.util.function.ToDoubleFunction<RunResult> f) { if (x.size()<2) return 0; double m=mean(x,f); return Math.sqrt(x.stream().mapToDouble(r -> Math.pow(f.applyAsDouble(r)-m,2)).sum()/(x.size()-1)); }
}
