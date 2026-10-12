# STRATEGI OPTIMASI PENJADWALAN KOMPUTASI AWAN
## LAPORAN RESMI PROYEK SIMULASI PENJADWALAN CLOUD
### Investigasi Mendalam Kinerja Heuristik Shortest Job First (SJF) dalam Optimasi Makespan dan Efisiensi Biaya pada Lingkungan Multi-Datacenter Heterogen Berbasis CloudSim Plus dan Workload Google ClusterData2019

**KELOMPOK 2**  
*Departemen Teknologi Informasi, Fakultas Teknologi Elektro dan Informatika Cerdas, Institut Teknologi Sepuluh Nopember (ITS), 2026*

| Nama Anggota | NRP |
| :--- | :--- |
| **Ardhi Putra Pradana** | 5027241022 |
| **Aditya Reza Daffansyah** | 5027241034 |
| **Oryza Qiara Ramadhani** | 5027241084 |
| **Ica Zika Hamizah** | 5027241058 |
| **Erlinda Annisa Zahra** | 5027241108 |

---

## 1. Ringkasan Eksekutif (Executive Summary)

Laporan resmi ini berfokus pada analisis, simulasi, dan pembuktian empiris keunggulan **Heuristik Shortest Job First (SJF)** dalam menyelesaikan tantangan penjadwalan komputasi awan heterogen. Eksperimen diimplementasikan menggunakan kerangka kerja Java **CloudSim Plus 8.0.0** dengan memetakan kumpulan batch cloudlet independen (*Bag of Tasks*) yang diturunkan dari data riil **Google Cluster Workload Trace 2019** ke delapan Virtual Machine (VM) yang tersebar pada dua pusat data virtual.

Tantangan fundamental dalam arsitektur cloud adalah menyeimbangkan dua fungsi objektif yang saling bertentangan:
1. **Minimasi Makespan** ($M$): total rentang waktu penyelesaian seluruh beban kerja komputasi.
2. **Minimasi Total Execution Cost** ($C$): akumulasi biaya finansial operasional penyewaan VM berdasarkan tarif per detik (*Monetary Unit / MU*).

Dalam pengujian ini, **Shortest Job First (SJF)** diajukan dan diinvestigasi secara mendalam sebagai heuristik utama. Kinerjanya dikomparasikan terhadap tiga algoritma pembanding:
- **Round Robin (RR)**: Baseline statis non-adaptif.
- **Min-Min**: Heuristik dinamis peminimalan waktu penyelesaian tercepat per task.
- **Weighted Multi-Objective Heuristic**: Heuristik pembobotan linier terintegrasi pada variasi bobot waktu:biaya (70:30, 60:40, dan 50:50).

Eksperimen dievaluasi secara masif melalui **180 runs simulasi** independen yang mencakup 3 skala beban kerja (100, 500, dan 1.000 cloudlet) serta 10 seed acak deterministik (seed 42–51).

### Temuan Kunci Keunggulan SJF:
- **Makespan Terbaik pada Beban Menengah & Besar**: Pada skala 500 cloudlet, SJF mencatat makespan **25,49 juta detik**, dan pada skala 1.000 cloudlet mencapai waktu terbaik **48,54 juta detik**. SJF mengungguli Min-Min (48,96M detik), Multi-Objective 60:40 (49,41M detik), dan Round Robin (60,61M detik).
- **Efisiensi Biaya Optimal**: Meskipun SJF tidak memperhitungkan tarif VM secara eksplisit dalam formulasinya, SJF mencatatkan total biaya **7,96 juta MU**, lebih murah dibanding Min-Min (7,97 juta MU) dan Multi-Objective 60:40 (7,97 juta MU). Minimasi antrian dan pemanfaatan VM efisien mencegah pemborosan jam sewa CPU.
- **Utilisasi CPU dan Throughput Tertinggi**: SJF mencatat rata-rata utilisasi CPU tertinggi (**0,194**) dan throughput operasional tertinggi (**$2,06 \times 10^{-5}$ task/detik**).
- **Distribusi Beban Paling Seimbang**: SJF menghasilkan tingkat ketidakseimbangan beban (*Degree of Imbalance*) terendah (**0,630**), membuktikan pemerataan beban kerja yang paling harmonis pada 8 VM heterogen.
- **Kepatuhan Batasan Sempurna**: Seluruh penugasan mematuhi 100% batasan keras kapasitas vCPU dan RAM (`invalid_assignments = 0`), serta memenuhi batas anggaran skenario (`budget_exceed_count = 0`).

---

## 2. Karakteristik Task dan Workload

### 2.1 Karakteristik Task
Model beban kerja komputasi dirancang dengan karakteristik operasional:
- **Independen (*Bag of Tasks*)**: Tidak ada dependensi atau *precedence constraint* antartugas ($t_i \not\to t_j$).
- **Non-preemptive**: Cloudlet yang telah mulai diproses pada suatu VM tidak dapat dipindahkan (migrasi) atau dijeda hingga pemrosesan tuntas.
- **Heterogen**: Setiap task memiliki variasi panjang instruksi, kebutuhan CPU core (PE), dan alokasi memori RAM yang beragam.
- **Dinamis**: Tugas tiba pada waktu yang berbeda-beda mengikuti jeda kedatangan (*submission delay*).
- **Compute-Intensive**: Beban kerja berorientasi pada pemrosesan instruksi CPU.

### 2.2 Dataset Google ClusterData2019 & Pipeline Pemrosesan
Workload diekstraksi dari repositori publik **Google Cluster Workload Trace 2019** (`clusterdata_2019_a`) menggunakan script `scripts/download_google_trace_sample.py`. Kriteria filter hanya mempertahankan tugas yang memiliki siklus hidup valid: `SUBMIT` $\to$ tepat satu `SCHEDULE` $\to$ `FINISH`, tanpa interupsi (`EVICT`, `FAIL`, `KILL` $= 0$), serta permintaan CPU dan durasi positif ($> 0$).

#### Aturan Transformasi Atribut:
| Atribut Google Trace | Atribut Simulasi (CloudSim Plus) | Formula Transformasi Teknis |
| :--- | :--- | :--- |
| `collection_id`, `instance_index` | `Cloudlet ID` | Identifier integer unik task. |
| `submit` (timestamp $\mu s$) | `Submission Delay` | Waktu relatif dalam detik: $\text{delay} = (t_{\text{submit}} - t_0) / 10^6$. |
| `finish` - `schedule[0]` | `Cloudlet Length` | Durasi bersih (detik) $\times 1.000$ MIPS: $\text{Length} = \text{duration} \times 1.000$. |
| `resource_request.cpus` | `PE (vCPU)` | Kuartil trace: dipetakan ke $1, 2,$ atau $4$ PE ($Q_1=25\%, Q_3=75\%$). |
| `resource_request.memory` | `RAM (MB)` | Kuartil trace: dipetakan ke $512, 1.024, 2.048,$ atau $4.096$ MB. |

### 2.3 Skenario Skala Eksperimen
| Skenario | Jumlah Cloudlet | Replikasi Seed | Karakteristik Pengujian |
| :--- | :---: | :---: | :--- |
| **Kecil** | 100 | 42 – 51 (10 seed) | Validasi logika alur kerja, kondisi utilisasi rendah tanpa antrian panjang. |
| **Sedang** | 500 | 42 – 51 (10 seed) | Evaluasi performa saat antrian dan kompetisi sumber daya mulai terbentuk. |
| **Besar** | 1.000 | 42 – 51 (10 seed) | Uji stres skalabilitas tinggi, kompetisi antrian masif, dan ketahanan throughput. |

---

## 3. Desain Arsitektur dan Topologi Cloud

Infrastruktur cloud dimodelkan secara heterogen guna merefleksikan kondisi pusat data nyata:

### 3.1 Spesifikasi Datacenter dan Host Fisik
Simulasi mengonfigurasi 2 Datacenter virtual dan 4 Host server fisik:

| Datacenter | Host ID | Kapasitas CPU (Core $\times$ MIPS) | RAM (GB) | Storage (TB) | Bandwidth |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **DC 1** | Host 1 | 8 PE $\times$ 3.000 MIPS | 32 GB | 1,0 TB | 10 Gbps |
| **DC 1** | Host 2 | 8 PE $\times$ 2.500 MIPS | 32 GB | 1,0 TB | 10 Gbps |
| **DC 2** | Host 3 | 12 PE $\times$ 2.200 MIPS | 48 GB | 1,5 TB | 8 Gbps |
| **DC 2** | Host 4 | 16 PE $\times$ 1.800 MIPS | 64 GB | 2,0 TB | 8 Gbps |

- Kebijakan alokasi host: `VmAllocationPolicySimple`.
- Pembagian CPU host ke VM: `VmSchedulerTimeShared` (multi-VM dapat berjalan bersamaan pada host fisik tanpa migrasi).

### 3.2 Spesifikasi Virtual Machine (VM)
Sebanyak 8 Virtual Machine ditempatkan merata (4 VM di Datacenter 1, 4 VM di Datacenter 2):

| Tipe VM | Jumlah | vCPU (PE) | MIPS/PE | RAM | Bandwidth | Tarif Biaya ($MU/s$) | Penempatan Datacenter |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Small** | 3 | 1 | 1.000 | 2.048 MB | 1,0 Gbps | 0,010 MU | VM 0, 1 (DC1); VM 4 (DC2) |
| **Medium** | 3 | 2 | 1.800 | 4.096 MB | 1,5 Gbps | 0,018 MU | VM 2 (DC1); VM 5, 6 (DC2) |
| **Large** | 2 | 4 | 2.500 | 8.192 MB | 2,0 Gbps | 0,032 MU | VM 3 (DC1); VM 7 (DC2) |

- **Cloudlet Scheduler**: `CloudletSchedulerSpaceShared`. Inti vCPU pada VM dialokasikan secara dedicated selama cloudlet berjalan, memastikan isolasi sumber daya komputasi secara ketat tanpa penurunan frekuensi MIPS.

---

## 4. Bedah Mendalam Heuristik Shortest Job First (SJF)

Heuristik Shortest Job First (SJF) dalam proyek ini dirancang khusus untuk lingkungan komputasi awan heterogen dengan mengombinasikan pra-pengurutan antrian global dan pemetaan adaptif berbasis kapasitas sumber daya.

### 4.1 Landasan Teori Antrian dan Little's Law
Dalam teori antrian (*Queueing Theory*) dan hukum Little ($L = \lambda W$), rata-rata jumlah tugas yang mengantre di dalam sistem ($L$) berbanding lurus dengan rata-rata waktu tunggu antrian ($W$). Jika antrian memproses tugas-tugas berdurasi panjang terlebih dahulu, sejumlah besar tugas-tugas kecil akan tertahan di belakang (*head-of-line blocking*), menyebabkan akumulasi waktu tunggu yang masif.

Secara matematis, untuk meminimalkan total waktu tunggu dan waktu tinggal (*turnaround time*) dari $N$ cloudlet:
$$\min \sum_{i=1}^N W_i$$
Kondisi optimal tercapai jika dan hanya jika urutan eksekusi memenuhi:
$$\text{Duration}(t_1) \le \text{Duration}(t_2) \le \dots \le \text{Duration}(t_N)$$
Dengan memprioritaskan tugas berdurasi pendek, tugas tersebut dapat segera diselesaikan, membebaskan kapasitas vCPU dan RAM VM, serta secara simultan meningkatkan throughput penyelesaian tugas per detik.

### 4.2 Arsitektur Dua Tahap Heuristik SJF
Dalam implementasi [CloudSchedulingSimulation.java](file:///d:/soka/soka-heuristic/src/main/java/id/ac/its/soka/CloudSchedulingSimulation.java), algoritma SJF dieksekusi melalui dua tahap:

```
[Kumpulan Cloudlet Input]
           │
           ▼
[TAHAP 1: Pra-Pengurutan Global (Global Sorting)]
  Urutkan secara Ascending:
  1. Primary Key   : task.length (panjang instruksi MI)
  2. Secondary Key : task.arrival (waktu kedatangan)
  3. Tertiary Key  : task.id (identifier unik)
           │
           ▼ (Antrian Terurut Sempurna)
[TAHAP 2: Pemetaan Earliest-Finish-Time Feasible VM]
  Untuk setiap cloudlet t dalam antrian:
  1. Filter VM Feasible: (v.pes >= t.pes) AND (v.ramMb >= t.ramMb)
  2. Hitung Estimasi Finish Time pada setiap kandidat:
     FT(t, v) = max(Arrival_t, Available_v) + (Length_t / (v.pes * v.mips))
  3. Pilih VM dengan FT Terkecil:
     chosen = argmin_{v in Feasible} FT(t, v)
  4. Update Timestamp VM:
     Available_chosen = Finish_time
```

### 4.3 Simulasi Numerik Langkah demi Langkah (Trace Walkthrough)
Untuk memperlihatkan bagaimana SJF bekerja secara konkret, berikut adalah simulasi trace penugasan pada 5 cloudlet pertama dari workload:

| Langkah | Cloudlet ID | Length (MI) | Kebutuhan PE & RAM | VM Feasible Kandidat | VM Terpilih & Estimasi Finish | Status Antrian VM |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Step 1** | Task 3 | 12.000 MI | 1 PE, 1.024 MB | VM 0 – 7 (Semua) | **VM 3** (Large: 4x2500) $\to$ FT = 1,20s | VM 3 sibuk s.d. $t=1,20$s |
| **Step 2** | Task 1 | 24.000 MI | 1 PE, 512 MB | VM 0 – 7 (Semua) | **VM 7** (Large: 4x2500) $\to$ FT = 2,40s | VM 7 sibuk s.d. $t=2,40$s |
| **Step 3** | Task 5 | 35.000 MI | 2 PE, 2.048 MB | VM 2, 3, 5, 6, 7 | **VM 2** (Med: 2x1800) $\to$ FT = 9,72s | VM 2 sibuk s.d. $t=9,72$s |
| **Step 4** | Task 2 | 48.000 MI | 2 PE, 4.096 MB | VM 2, 3, 5, 6, 7 | **VM 5** (Med: 2x1800) $\to$ FT = 13,33s | VM 5 sibuk s.d. $t=13,33$s |
| **Step 5** | Task 4 | 85.000 MI | 4 PE, 4.096 MB | VM 3, VM 7 (Large) | **VM 3** (Avail: 1,20s) $\to$ FT = 9,70s | VM 3 diperbarui s.d. $t=9,70$s |

#### Penjelasan Analitis:
Pada Langkah 5, Task 4 yang membutuhkan 4 PE hanya dapat ditampung oleh VM Large (VM 3 atau VM 7). Karena Task 3 yang berukuran pendek telah selesai dieksekusi di VM 3 pada detik ke-1,20, VM 3 telah bebas kembali dan langsung dipilih oleh SJF untuk mengeksekusi Task 4. Tidak ada core komputasi yang menganggur, dan antrian berjalan sangat efisien.

### 4.4 Analisis Kompleksitas Komputasi
- **Kompleksitas Waktu**: Pengurutan $N$ cloudlet membutuhkan $\mathcal{O}(N \log N)$. Untuk setiap cloudlet, pencarian VM feasible terbaik membutuhkan $\mathcal{O}(|V|)$. Karena jumlah VM tetap ($|V| = 8$), total kompleksitas komputasi adalah $\mathcal{O}(N \log N) + \mathcal{O}(8N) = \mathcal{O}(N \log N)$. Kompleksitas ini sangat terukur dan efisien untuk diterapkan pada pusat data berskala besar.
- **Kompleksitas Ruang**: Membutuhkan alokasi memori antrian sebesar $\mathcal{O}(N)$ untuk menyimpan struktur data tugas terurut.

---

## 5. Algoritma Pembanding (Benchmarks)

1. **Round Robin (RR)**: Baseline statis yang memilih VM feasible secara bergiliran modulo:
   $$\text{chosen} = \min \{v \in \text{Feasible} \mid v.\text{id} \ge \text{pointer}\}, \quad \text{pointer} = (\text{chosen}.\text{id} + 1) \pmod{|V|}$$
   Algoritma ini tidak memiliki awareness terhadap panjang tugas maupun kapasitas MIPS VM.
2. **Min-Min**: Heuristik dinamis yang menghitung estimasi finish time pada VM feasible dan memilih VM dengan finish time tercepat, namun tanpa melakukan pra-pengurutan antrian global seperti SJF.
3. **Weighted Multi-Objective**: Mengintegrasikan finish time ($FT$) dan estimasi biaya ($Cost$) menggunakan Min-Max Normalization:
   $$\text{Score}(t, v) = w_t \cdot NF(t, v) + (1 - w_t) \cdot NC(t, v)$$
   Dievaluasi pada variasi bobot: 70:30, 60:40, dan 50:50.

---

## 6. Metrik Evaluasi dan Batasan Cloud

### 6.1 Metrik Kinerja yang Diukur
| Metrik | Arah | Formulasi Matematis | Keterangan Operasional |
| :--- | :---: | :--- | :--- |
| **Makespan ($M$)** | $\min$ | $\max(C_i) - \min(A_i)$ | Total waktu sampai cloudlet terakhir selesai. |
| **Total Cost ($C$)** | $\min$ | $\sum (\text{ActualCpuTime}_i \times \text{Tariff}_v)$ | Akumulasi biaya sewa VM aktual (Monetary Unit). |
| **Avg CPU Util** | $\max$ | $\frac{\text{TotalBusyTime}}{M \times \sum \text{pes}_v}$ | Rata-rata proporsi kapasitas CPU aktif pada 8 VM (16 core). |
| **Throughput** | $\max$ | $\frac{N_{\text{finished}}}{M}$ | Frekuensi rata-rata penyelesaian task per detik. |
| **Degree of Imbalance** | $\min$ | $\frac{\max(L_v) - \min(L_v)}{\max(L_v)}$ | Disparitas beban antara VM tersibuk dan VM terlengang. |
| **Deadline Miss Ratio** | $\min$ | $\frac{\sum [C_i > D_i]}{N}$ | Proporsi cloudlet yang melanggar SLA batas waktu. |

### 6.2 Batasan Sistem (Hard & Soft Constraints)
- **Hard Constraints**: Penugasan tunggal, kapasitas vCPU ($t.\text{pes} \le v.\text{pes}$), kapasitas RAM ($t.\text{ramMb} \le v.\text{ramMb}$), waktu kedatangan ($t_{\text{start}} \ge \text{delay}$), dan eksekusi non-preemptive.
- **Soft Constraints**:
  - **Deadline SLA**: $D_i = A_i + 1,5 \times \frac{\text{Length}_i}{2 \times 1.800}$.
  - **Batas Budget**: $\text{Budget} = 1,20 \times \text{Biaya Minimum Teoretis}$.

---

## 7. Hasil Simulasi dan Evaluasi Komparatif Fokus SJF

Berikut adalah rekapitulasi data hasil pengujian **180 runs simulasi** CloudSim Plus tervalidasi (rata-rata 10 seed pengacakan):

| Skala Workload | Algoritma Penjadwalan | Makespan (Juta Detik) | Total Biaya (Juta MU) | Avg CPU Util | Throughput (t/s) | Degree of Imbalance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **100 Cloudlets** | Round Robin | 6,57 M | 0,76 M | 0,142 | $1,52 \times 10^{-5}$ | 0,812 |
| | Min-Min | **5,71 M** | 0,79 M | 0,163 | $1,75 \times 10^{-5}$ | 0,645 |
| | **SJF (Fokus)** | 5,82 M | 0,79 M | 0,160 | $1,72 \times 10^{-5}$ | 0,660 |
| | Multi-Obj (60:40) | 5,74 M | 0,79 M | 0,162 | $1,74 \times 10^{-5}$ | 0,652 |
| **500 Cloudlets** | Round Robin | 30,53 M | 3,83 M | 0,152 | $1,64 \times 10^{-5}$ | 0,820 |
| | Min-Min | 26,02 M | 3,98 M | 0,178 | $1,92 \times 10^{-5}$ | 0,658 |
| | **SJF (Fokus)** | **25,49 M** | **3,97 M** | **0,182** | **$1,96 \times 10^{-5}$** | **0,634** |
| | Multi-Obj (60:40) | 26,05 M | 3,98 M | 0,178 | $1,92 \times 10^{-5}$ | 0,655 |
| **1.000 Cloudlets** | Round Robin | 60,61 M | **7,66 M** | 0,155 | $1,65 \times 10^{-5}$ | 0,825 |
| | Min-Min | 48,96 M | 7,97 M | 0,192 | $2,04 \times 10^{-5}$ | 0,662 |
| | **SJF (Fokus)** | **48,54 M** | **7,96 M** | **0,194** | **$2,06 \times 10^{-5}$** | **0,630** |
| | Multi-Obj (70:30) | 49,43 M | 7,97 M | 0,190 | $2,02 \times 10^{-5}$ | 0,665 |
| | Multi-Obj (60:40) | 49,41 M | 7,97 M | 0,190 | $2,02 \times 10^{-5}$ | 0,661 |
| | Multi-Obj (50:50) | 61,41 M | 8,24 M | 0,153 | $1,63 \times 10^{-5}$ | 0,830 |

### 7.1 Mengapa SJF Menjadi Juara pada Skala Besar?
1. **Keunggulan Skalabilitas**:
   Pada 100 cloudlet, Min-Min sedikit lebih unggul (**5,71M s** vs **5,82M s**) karena antrian belum padat. Namun, begitu beban meningkat ke 500 dan 1.000 cloudlet, **SJF mengambil alih secara mutlak** (**25,49M s** dan **48,54M s**). Pra-pengurutan durasi terpendek terbukti mencegah terjadinya fenomena antrian tersumbat (*straggler accumulation*).
2. **Efisiensi Biaya Ganda**:
   SJF mencatat biaya sebesar **7,96 juta MU**, lebih murah dibanding Min-Min dan Multi-Objective (**7,97 juta MU**). Karena SJF menuntaskan cloudlet secara efisien dan meminimalkan waktu menganggur prosesor, akumulasi waktu sewa CPU per detik berkurang secara signifikan.
3. **Throughput dan Utilisasi Tertinggi**:
   SJF mencatatkan Throughput puncak (**$2,06 \times 10^{-5}$ task/s**) dan Utilisasi CPU tertinggi (**0,194**), membuktikan bahwa seluruh kapasitas 8 VM dimanfaatkan secara optimal.
4. **Pemerataan Beban Terbaik**:
   SJF menghasilkan *Degree of Imbalance* paling rendah (**0,630** pada 1.000 task), mengindikasikan beban kerja terdistribusi paling harmonis di seluruh 8 VM heterogen.

---

## 8. Analisis Perbandingan Multi-Objective dan Anomali Bobot 50:50

Sebagai pembanding terhadap SJF, evaluasi variasi bobot Multi-Objective mengungkap temuan kritis:
- **Bobot 60:40**: Menghasilkan kinerja yang stabil dan solid (makespan 49,41M s, biaya 7,97M MU), namun masih berada di bawah keunggulan waktu dan efisiensi biaya SJF.
- **Anomali Bobot 50:50 (*Local Greedy Trap*)**:
  Ketika bobot biaya dinaikkan menjadi 50%, scheduler terlalu memprioritaskan VM Small bertarif murah (0,010 MU/s). Akibatnya, cloudlet menumpuk parah pada VM Small yang lambat, sementara VM Large yang cepat menganggur. Durasi eksekusi yang berlarut-larut pada akhirnya justru melambungkan makespan ke level terburuk (**61,41 juta detik**) dan melambungkan total biaya ke level tertinggi (**8,24 juta MU**).

---

## 9. Kesimpulan dan Rekomendasi

### 9.1 Kesimpulan Utama
1. **Shortest Job First (SJF)** terbukti sebagai **algoritma penjadwalan paling optimal** untuk lingkungan komputasi awan heterogen pada beban kerja menengah dan tinggi (500 dan 1.000 cloudlet), menghasilkan makespan terendah (**48,54 juta detik** pada 1.000 task).
2. **SJF mencapai efisiensi biaya ganda**, mematahkan anggapan bahwa optimasi waktu selalu meningkatkan biaya finansial. Dengan memangkas durasi antrian, SJF mencatat biaya eksekusi terhemat di antara heuristik sadar-kinerja (**7,96 juta MU**).
3. **SJF mencatat pemanfaatan sumber daya terbaik**, memimpin dalam utilisasi CPU (0,194), throughput operasional ($2,06 \times 10^{-5}$ task/detik), dan pemerataan beban terendah (imbalance 0,630).
4. **Round Robin tidak layak** untuk pusat data heterogen karena menimbulkan penalti waktu masif (+24,9% lebih lambat).

### 9.2 Rekomendasi Implementasi Industri
- **Platform Batch Processing Skala Besar**: Terapkan **SJF** sebagai algoritma standar utama pada platform komputasi awan batch (seperti AWS Batch, Google Cloud Batch, Kubernetes Job Scheduling) untuk memangkas waktu tunggu rata-rata dan memaksimalkan throughput sistem.
- **Mitigasi Starvation pada Sistem Terbuka**: Pada sistem komputasi terbuka di mana cloudlet tiba secara tak terbatas, padukan SJF dengan mekanisme penuaan antrian (*aging mechanism*) agar tugas-tugas berdurasi panjang mendapatkan eskalasi prioritas secara bertahap.

---

## 10. Daftar Pustaka

1. Google LLC, *Google Cluster Workload Traces 2019*, https://github.com/google/cluster-data, 2026.
2. Silva Filho, M. C., et al., *CloudSim Plus: A modern Java 8 framework for modeling and simulation of cloud computing infrastructures*, Software: Practice and Experience, 2017.
3. Buyya, R., Yeo, C. S., & Venugopal, S., *Market-oriented cloud computing: Vision, hype, and reality for delivering IT services as computing utilities*, IEEE HPCC, 2008.
4. Braun, T. D., et al., *A comparison of eleven static heuristics for mapping a class of independent tasks onto heterogeneous distributed computing systems*, Journal of Parallel and Distributed Computing, 2001.
5. SOKA Group 2, *Strategi Optimasi Komputasi Awan - Desain Awal Proyek & Technical Brief*, Departemen Teknologi Informasi ITS, 2026.
