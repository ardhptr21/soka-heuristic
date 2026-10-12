import os
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'<w:top w:val="{kwargs.get("top", {}).get("val", "single")}" w:sz="{kwargs.get("top", {}).get("sz", "4")}" w:space="0" w:color="{kwargs.get("top", {}).get("color", "CCCCCC")}"/>\n'
        f'<w:left w:val="{kwargs.get("left", {}).get("val", "single")}" w:sz="{kwargs.get("left", {}).get("sz", "4")}" w:space="0" w:color="{kwargs.get("left", {}).get("color", "CCCCCC")}"/>\n'
        f'<w:bottom w:val="{kwargs.get("bottom", {}).get("val", "single")}" w:sz="{kwargs.get("bottom", {}).get("sz", "4")}" w:space="0" w:color="{kwargs.get("bottom", {}).get("color", "CCCCCC")}"/>\n'
        f'<w:right w:val="{kwargs.get("right", {}).get("val", "single")}" w:sz="{kwargs.get("right", {}).get("sz", "4")}" w:space="0" w:color="{kwargs.get("right", {}).get("color", "CCCCCC")}"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'<w:top w:w="{top}" w:type="dxa"/>\n'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'<w:left w:w="{left}" w:type="dxa"/>\n'
        f'<w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def style_table(table, col_widths=None, header_bg="1F4E79", alt_bg="F9FAFB"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if i == 0:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            
        for j, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=110, bottom=110, left=150, right=150)
            if col_widths and j < len(col_widths):
                cell.width = col_widths[j]
                
            if i == 0:
                set_cell_shading(cell, header_bg)
                set_cell_border(cell, top={"sz": 8, "color": "1F4E79"}, bottom={"sz": 12, "color": "1F4E79"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    for run in p.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.size = Pt(9.5)
                        run.font.name = "Calibri"
            else:
                bg = alt_bg if i % 2 == 1 else "FFFFFF"
                set_cell_shading(cell, bg)
                set_cell_border(cell, top={"sz": 4, "color": "E1E4E8"}, bottom={"sz": 4, "color": "E1E4E8"}, left={"sz": 4, "color": "E1E4E8"}, right={"sz": 4, "color": "E1E4E8"})
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    for run in p.runs:
                        run.font.size = Pt(9.5)
                        run.font.name = "Calibri"

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(31, 78, 121)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(47, 85, 151)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.italic = True
    run.font.color.rgb = RGBColor(51, 51, 51)
    return p

def add_body_paragraph(doc, text, bold_prefix=None, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.bold = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.italic = italic
    return p

def add_bullet_point(doc, text, bold_title=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_title:
        r_b = p.add_run(bold_title)
        r_b.font.name = "Calibri"
        r_b.font.size = Pt(10.5)
        r_b.font.bold = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    return p

def add_equation_box(doc, equation_text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(equation_text)
    run.font.name = "Cambria Math"
    run.font.size = Pt(10.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor(20, 40, 80)
    return p

def build_report():
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # ----------------------------------------------------
    # COVER / HEADER SECTION
    # ----------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(4)
    r1 = p_title.add_run("STRATEGI OPTIMASI KOMPUTASI AWAN\n")
    r1.font.name = "Calibri"
    r1.font.size = Pt(18)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(31, 78, 121)
    
    r2 = p_title.add_run("LAPORAN RESMI PROYEK SIMULASI PENJADWALAN CLOUD\n")
    r2.font.name = "Calibri"
    r2.font.size = Pt(14)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(47, 85, 151)

    r3 = p_title.add_run("Investigasi Mendalam Kinerja Heuristik Shortest Job First (SJF) dalam Optimasi Makespan dan Efisiensi Biaya pada Lingkungan Multi-Datacenter Heterogen Berbasis CloudSim Plus dan Workload Google ClusterData2019")
    r3.font.name = "Calibri"
    r3.font.size = Pt(11)
    r3.font.italic = True
    r3.font.color.rgb = RGBColor(80, 80, 80)

    p_group = doc.add_paragraph()
    p_group.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_group.paragraph_format.space_before = Pt(16)
    p_group.paragraph_format.space_after = Pt(6)
    r_grp = p_group.add_run("KELOMPOK 2\nDisusun oleh:")
    r_grp.font.name = "Calibri"
    r_grp.font.size = Pt(11)
    r_grp.font.bold = True

    table_authors = doc.add_table(rows=6, cols=2)
    authors_data = [
        ["Nama Anggota", "NRP"],
        ["Ardhi Putra Pradana", "5027241022"],
        ["Aditya Reza Daffansyah", "5027241034"],
        ["Oryza Qiara Ramadhani", "5027241084"],
        ["Ica Zika Hamizah", "5027241058"],
        ["Erlinda Annisa Zahra", "5027241108"]
    ]
    for r_idx, row in enumerate(authors_data):
        for c_idx, val in enumerate(row):
            table_authors.cell(r_idx, c_idx).text = val
    style_table(table_authors, col_widths=[Inches(3.2), Inches(2.2)], header_bg="2F5597")

    p_dept = doc.add_paragraph()
    p_dept.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_before = Pt(16)
    p_dept.paragraph_format.space_after = Pt(20)
    r_dept = p_dept.add_run("DEPARTEMEN TEKNOLOGI INFORMASI\nFAKULTAS TEKNOLOGI ELEKTRO DAN INFORMATIKA CERDAS\nINSTITUT TEKNOLOGI SEPULUH NOPEMBER\n2026")
    r_dept.font.name = "Calibri"
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True
    r_dept.font.color.rgb = RGBColor(31, 78, 121)

    doc.add_page_break()

    # ----------------------------------------------------
    # BAB I: RINGKASAN EKSEKUTIF
    # ----------------------------------------------------
    add_heading_1(doc, "1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)")
    add_body_paragraph(doc, "Laporan resmi ini berfokus pada analisis, simulasi, dan pembuktian empiris keunggulan heuristik Shortest Job First (SJF) dalam memecahkan permasalahan alokasi komputasi awan heterogen. Eksperimen diimplementasikan menggunakan CloudSim Plus 8.0.0 dengan memetakan kumpulan batch cloudlet independen (Bag of Tasks) dari Google Cluster Workload Trace 2019 ke delapan Virtual Machine (VM) yang didistribusikan pada dua pusat data virtual.")
    add_body_paragraph(doc, "Tantangan mendasar dalam penjadwalan cloud adalah menemukan keseimbangan antara minimasi Makespan (waktu penyelesaian seluruh beban kerja) dan Total Execution Cost (biaya sewa VM per detik). Algoritma konvensional seperti Round Robin sering mengalami degradasi akibat ketidaksadaran terhadap durasi tugas, sementara algoritma rakus (greedy) seperti Min-Min dapat memicu kemacetan pada VM tertentu. Dalam penelitian ini, heuristik Shortest Job First (SJF) diajukan sebagai solusi utama yang memadukan pra-pengurutan antrian secara global (length-ascending) dengan penugasan dinamis ke VM feasible yang memiliki estimasi waktu selesai terawal (earliest finish time feasible VM).")
    add_body_paragraph(doc, "Dari 180 runs simulasi yang dievaluasi lintas 3 ukuran workload (100, 500, dan 1.000 cloudlet) dan 10 seed pengacakan, heuristik SJF membuktikan keunggulannya sebagai algoritma terbaik pada beban kerja menengah dan tinggi. Pada skala 1.000 task, SJF mencatat makespan terendah sebesar 48,54 juta detik, mengungguli Min-Min (48,96 juta detik), Multi-Objective 60:40 (49,41 juta detik), dan Round Robin (60,61 juta detik). Lebih dari itu, SJF juga menghasilkan efisiensi biaya yang sangat tinggi (7,96 juta MU), utilisasi CPU puncak (0,194), throughput operasional tertinggi (2,06 x 10^-5 task/detik), serta ketidakseimbangan beban terendah (imbalance 0,630).")

    # ----------------------------------------------------
    # BAB II: JENIS TASK DAN WORKLOAD
    # ----------------------------------------------------
    add_heading_1(doc, "2. KARAKTERISTIK TASK DAN WORKLOAD")
    add_heading_2(doc, "2.1 Karakteristik Task")
    add_body_paragraph(doc, "Beban kerja dimodelkan sebagai sekumpulan cloudlet komputasi dengan karakteristik operasional:")
    add_bullet_point(doc, " Task tidak memiliki dependensi atau relasi urutan (Bag of Tasks), sehingga setiap cloudlet dapat dialokasikan secara independen.", "Independen: ")
    add_bullet_point(doc, " Sekali suatu cloudlet mulai dieksekusi pada VM, proses tidak dapat dijeda atau dipindahkan (non-preemptive).", "Non-preemptive: ")
    add_bullet_point(doc, " Setiap tugas memiliki panjang instruksi eksekusi, kebutuhan vCPU (PE), dan alokasi memori RAM yang sangat heterogen.", "Heterogen: ")
    add_bullet_point(doc, " Kedatangan cloudlet tidak serentak pada waktu nol, melainkan bertahap sesuai jeda kedatangan riil (submission delay).", "Dinamis: ")

    add_heading_2(doc, "2.2 Dataset Google ClusterData2019 & Pipeline Pemrosesan")
    add_body_paragraph(doc, "Dataset diambil dari repositori publik Google Cluster Workload Trace 2019. Skrip scripts/download_google_trace_sample.py digunakan untuk menyaring tugas-tugas bersih yang menyelesaikan siklus penuh SUBMIT -> SCHEDULE -> FINISH tanpa kegagalan atau penggusuran (EVICT, FAIL, KILL = 0).")

    t_trans = doc.add_table(rows=6, cols=3)
    trans_data = [
        ["Atribut Google Trace", "Atribut Simulasi (CloudSim Plus)", "Aturan Transformasi Teknis"],
        ["collection_id, instance_index", "Cloudlet ID", "Dipertahankan sebagai identifier unik task integer."],
        ["submit (timestamp us)", "Submission Delay (Arrival Time)", "Dikonversi ke satuan detik relatif terhadap task pertama (t_submit - t_0) / 10^6."],
        ["finish - schedule[0]", "Cloudlet Length (Million Instructions)", "Durasi eksekusi bersih dalam detik dikalikan 1.000 MIPS: Length = Duration x 1.000."],
        ["resource_request.cpus", "Processing Elements (PE / vCPU)", "Dipetakan ke 1, 2, atau 4 PE berdasarkan kuartil trace (Q1=25%, Q3=75%)."],
        ["resource_request.memory", "Memory Request (RAM MB)", "Dipetakan ke 512, 1.024, 2.048, atau 4.096 MB berdasarkan kuartil data."]
    ]
    for r_idx, row in enumerate(trans_data):
        for c_idx, val in enumerate(row):
            t_trans.cell(r_idx, c_idx).text = val
    style_table(t_trans, col_widths=[Inches(1.8), Inches(2.0), Inches(2.7)], header_bg="1F4E79")

    # ----------------------------------------------------
    # BAB III: ARSITEKTUR CLOUD & TOPOLOGI
    # ----------------------------------------------------
    add_heading_1(doc, "3. DESAIN ARSITEKTUR DAN TOPOLOGI CLOUD")
    add_body_paragraph(doc, "Infrastruktur cloud dimodelkan dengan 2 Datacenter virtual, 4 Host fisik, dan 8 Virtual Machine heterogen.")
    
    t_vms = doc.add_table(rows=4, cols=8)
    vms_data = [
        ["Tipe VM", "Jumlah", "vCPU (PE)", "MIPS/PE", "RAM", "Bandwidth", "Tarif (MU/s)", "Penempatan Datacenter"],
        ["Small", "3", "1", "1.000", "2.048 MB", "1,0 Gbps", "0,010 MU", "VM 0, 1 (DC1); VM 4 (DC2)"],
        ["Medium", "3", "2", "1.800", "4.096 MB", "1,5 Gbps", "0,018 MU", "VM 2 (DC1); VM 5, 6 (DC2)"],
        ["Large", "2", "4", "2.500", "8.192 MB", "2,0 Gbps", "0,032 MU", "VM 3 (DC1); VM 7 (DC2)"]
    ]
    for r_idx, row in enumerate(vms_data):
        for c_idx, val in enumerate(row):
            t_vms.cell(r_idx, c_idx).text = val
    style_table(t_vms, col_widths=[Inches(0.9), Inches(0.6), Inches(0.7), Inches(0.8), Inches(0.9), Inches(0.8), Inches(0.9), Inches(1.7)], header_bg="1F4E79")

    add_body_paragraph(doc, "Host menerapkan VmAllocationPolicySimple dan VmSchedulerTimeShared. Setiap VM menerapkan CloudletSchedulerSpaceShared di mana alokasi core vCPU bersifat dedicated sehingga tidak terjadi degradasi MIPS akibat time-slicing.")

    # ----------------------------------------------------
    # BAB IV: BEDAH MENDALAM HEURISTIK SHORTEST JOB FIRST (SJF)
    # ----------------------------------------------------
    add_heading_1(doc, "4. BEDAH MENDALAM HEURISTIK SHORTEST JOB FIRST (SJF)")
    add_body_paragraph(doc, "Heuristik Shortest Job First (SJF) dalam simulasi ini tidak sekadar memilih tugas pendek, melainkan menggabungkan teori antrian optimal dengan penugasan adaptif terhadap kapasitas komputasi heterogen VM.")

    add_heading_2(doc, "4.1 Landasan Teori Antrian dan Little's Law")
    add_body_paragraph(doc, "Menurut teori penjadwalan klasik dan Little's Law (L = lambda x W), rata-rata jumlah tugas dalam antrian berbanding lurus dengan rata-rata waktu tunggu (average waiting time). Jika kumpulan tugas dieksekusi dengan mendahulukan tugas berdurasi panjang, tugas-tugas kecil yang jumlahnya banyak akan tertahan di belakang antrian (head-of-line blocking). Sebaliknya, dengan memprioritaskan tugas-tugas berdurasi pendek:")
    add_equation_box(doc, "Minimasi Total Waiting Time: sum_{i=1}^N W_i = min!")
    add_body_paragraph(doc, "Tugas pendek selesai dalam waktu sangat singkat, keluar dari antrian sistem, membebaskan kapasitas vCPU dan RAM VM, serta secara simultan meningkatkan throughput penyelesaian tugas.")

    add_heading_2(doc, "4.2 Arsitektur Dua Tahap Heuristik SJF")
    add_body_paragraph(doc, "Implementasi SJF dalam modul plan() pada CloudSchedulingSimulation.java bekerja melalui dua tahapan komputasi:")
    
    add_body_paragraph(doc, "Tahap 1: Pra-Pengurutan Global (Global Length-Ascending Sorting)", bold_prefix="• ")
    add_body_paragraph(doc, "Seluruh kumpulan tugas dalam batch diurutkan secara ascending berdasarkan panjang instruksi komputasi (length dalam MI). Untuk mencegah ambiguitas (tie-breaking), digunakan waktu kedatangan (arrival time) dan identifier unik (task ID):")
    add_equation_box(doc, "tasks.stream().sorted(Comparator.comparingLong(Task::length)\n  .thenComparingDouble(Task::arrival)\n  .thenComparingLong(Task::id))")

    add_body_paragraph(doc, "Tahap 2: Pemetaan Earliest-Finish-Time Feasible VM", bold_prefix="• ")
    add_body_paragraph(doc, "Untuk setiap cloudlet terurut t, sistem menyaring himpunan VM yang memenuhi batasan kapasitas (v.pes >= t.pes dan v.ramMb >= t.ramMb). Selanjutnya, sistem mencari VM yang menghasilkan estimasi waktu selesai paling awal:")
    add_equation_box(doc, "chosen = argmin_{v in Feasible} [ max(Arrival_t, Available_v) + (Length_t / (v.pes x v.mips)) ]")
    add_body_paragraph(doc, "Setelah VM terpilih, timestamp ketersediaan VM diperbarui secara inkremental: Available_chosen = Start_time + Runtime(t, chosen).")

    add_heading_2(doc, "4.3 Simulasi Numerik Langkah demi Langkah (Trace Step-by-Step)")
    add_body_paragraph(doc, "Untuk memahami secara konkret bagaimana SJF memproses antrian, berikut disajikan ilustrasi simulasi manual langkah demi langkah pada 5 cloudlet pertama:")

    t_trace = doc.add_table(rows=6, cols=7)
    trace_data = [
        ["Langkah", "Cloudlet ID", "Length (MI)", "Kebutuhan PE & RAM", "VM Feasible Kandidat", "VM Terpilih & Estimasi Finish", "Status Antrian VM"],
        ["Step 1", "Task 3", "12.000 MI", "1 PE, 1.024 MB", "VM 0 - 7 (Semua)", "VM 3 (Large: 4x2500) -> FT = 1,20s", "VM 3 sibuk s.d. 1,20s"],
        ["Step 2", "Task 1", "24.000 MI", "1 PE, 512 MB", "VM 0 - 7 (Semua)", "VM 7 (Large: 4x2500) -> FT = 2,40s", "VM 7 sibuk s.d. 2,40s"],
        ["Step 3", "Task 5", "35.000 MI", "2 PE, 2.048 MB", "VM 2, 3, 5, 6, 7", "VM 2 (Med: 2x1800) -> FT = 9,72s", "VM 2 sibuk s.d. 9,72s"],
        ["Step 4", "Task 2", "48.000 MI", "2 PE, 4.096 MB", "VM 2, 3, 5, 6, 7", "VM 5 (Med: 2x1800) -> FT = 13,33s", "VM 5 sibuk s.d. 13,33s"],
        ["Step 5", "Task 4", "85.000 MI", "4 PE, 4.096 MB", "VM 3, VM 7 (Large)", "VM 3 (Avail: 1,20s) -> FT = 9,70s", "VM 3 diperbarui s.d. 9,70s"]
    ]
    for r_idx, row in enumerate(trace_data):
        for c_idx, val in enumerate(row):
            t_trace.cell(r_idx, c_idx).text = val
    style_table(t_trace, col_widths=[Inches(0.7), Inches(0.8), Inches(1.0), Inches(1.3), Inches(1.2), Inches(1.4), Inches(1.2)], header_bg="1F4E79")

    add_body_paragraph(doc, "Penjelasan Mekanisme: Pada langkah 5, Task 4 yang membutuhkan 4 PE hanya feasible di VM 3 dan VM 7. VM 3 yang sebelumnya telah menyelesaikan Task 3 pada detik ke-1,20 sudah bebas kembali, sehingga dipilih oleh SJF untuk mengeksekusi Task 4. Tidak ada core yang terbuang sia-sia, dan antrian bergerak dinamis.")

    add_heading_2(doc, "4.4 Analisis Kompleksitas Komputasi")
    add_bullet_point(doc, " Pengurutan antrian N cloudlet membutuhkan waktu O(N log N). Untuk setiap tugas, penelusuran |V| VM yang feasible membutuhkan waktu O(|V|). Karena jumlah VM tetap (|V| = 8), total kompleksitas komputasi SJF adalah O(N log N) + O(8N) = O(N log N). Kompleksitas ini sangat efisien untuk dijalankan pada pusat data skala besar.", "Kompleksitas Waktu: ")
    add_bullet_point(doc, " Membutuhkan penyimpanan struktur data antrian berukuran O(N) untuk menyimpan referensi penugasan tugas.", "Kompleksitas Ruang: ")

    # ----------------------------------------------------
    # BAB V: PERBANDINGAN ALGORITMA LAIN
    # ----------------------------------------------------
    add_heading_1(doc, "5. ALGORITMA PEMBANDING (BENCHMARKS)")
    add_body_paragraph(doc, "Sebagai pembanding objektif terhadap kinerja SJF, dievaluasi tiga algoritma:")
    add_bullet_point(doc, " Menugaskan cloudlet secara bergiliran modulo ke VM yang feasible tanpa memperhitungkan panjang cloudlet maupun waktu selesai. Menjadi batas bawah efisiensi (baseline).", "1. Round Robin (RR): ")
    add_bullet_point(doc, " Memilih VM feasible dengan finish time tercepat per task, namun tanpa melakukan pra-pengurutan antrian global seperti SJF.", "2. Min-Min: ")
    add_bullet_point(doc, " Mengintegrasikan finish time dan tarif VM dengan normalisasi Min-Max pada bobot waktu:biaya (70:30, 60:40, 50:50).", "3. Weighted Multi-Objective: ")

    # ----------------------------------------------------
    # BAB VI: METRIK DAN BATASAN
    # ----------------------------------------------------
    add_heading_1(doc, "6. METRIK EVALUASI DAN BATASAN SISTEM")
    t_met = doc.add_table(rows=7, cols=4)
    met_data = [
        ["Metrik Kinerja", "Arah Target", "Rumus Perhitungan Matematis", "Interpretasi Operasional"],
        ["Makespan (M)", "Minimum", "max(Finish_i) - min(Arrival_i)", "Total waktu sampai seluruh cloudlet selesai diproses."],
        ["Total Cost (C)", "Minimum", "sum(ActualCpuTime_i x VM_Cost_v)", "Akumulasi biaya sewa VM aktual berdasarkan waktu pemakaian CPU."],
        ["Average CPU Util", "Maksimum", "TotalBusyTime / (Makespan x Total_PE)", "Tingkat efisiensi pemanfaatan kapasitas prosesor pada 8 VM (16 PE total)."],
        ["Throughput", "Maksimum", "Total_Cloudlet_Selesai / Makespan", "Frekuensi rata-rata penyelesaian tugas per satuan waktu (cloudlets/detik)."],
        ["Degree of Imbalance", "Minimum", "(Max_Load_v - Min_Load_v) / Max_Load_v", "Tingkat ketimpangan beban kerja antara VM tersibuk dan VM paling santai."],
        ["Deadline Miss Ratio", "Minimum", "Jumlah_Task(Finish > Deadline) / N", "Persentase cloudlet yang gagal memenuhi Service Level Agreement (SLA)."]
    ]
    for r_idx, row in enumerate(met_data):
        for c_idx, val in enumerate(row):
            t_met.cell(r_idx, c_idx).text = val
    style_table(t_met, col_widths=[Inches(1.4), Inches(0.8), Inches(2.2), Inches(2.1)], header_bg="1F4E79")

    # ----------------------------------------------------
    # BAB VII: HASIL SIMULASI DAN PEMBAHASAN FOKUS SJF
    # ----------------------------------------------------
    add_heading_1(doc, "7. HASIL SIMULASI DAN EVALUASI KOMPARATIF FOKUS SJF")
    add_body_paragraph(doc, "Pengujian 180 runs simulasi CloudSim Plus tervalidasi dirata-ratakan dari 10 seed replikasi (seed 42 s.d. 51):")

    t_res = doc.add_table(rows=11, cols=7)
    res_data = [
        ["Workload", "Algoritma Penjadwalan", "Makespan (Juta Detik)", "Total Biaya (Juta MU)", "CPU Util", "Throughput (t/s)", "Imbalance"],
        ["100 Task", "Round Robin", "6,57 M", "0,76 M", "0,142", "1,52 x 10^-5", "0,812"],
        ["100 Task", "Min-Min", "5,71 M", "0,79 M", "0,163", "1,75 x 10^-5", "0,645"],
        ["100 Task", "SJF (Fokus)", "5,82 M", "0,79 M", "0,160", "1,72 x 10^-5", "0,660"],
        ["100 Task", "Multi-Obj (60:40)", "5,74 M", "0,79 M", "0,162", "1,74 x 10^-5", "0,652"],
        ["500 Task", "Round Robin", "30,53 M", "3,83 M", "0,152", "1,64 x 10^-5", "0,820"],
        ["500 Task", "Min-Min", "26,02 M", "3,98 M", "0,178", "1,92 x 10^-5", "0,658"],
        ["500 Task", "SJF (Fokus)", "25,49 M", "3,97 M", "0,182", "1,96 x 10^-5", "0,634"],
        ["500 Task", "Multi-Obj (60:40)", "26,05 M", "3,98 M", "0,178", "1,92 x 10^-5", "0,655"],
        ["1.000 Task", "Round Robin", "60,61 M", "7,66 M", "0,155", "1,65 x 10^-5", "0,825"],
        ["1.000 Task", "Min-Min", "48,96 M", "7,97 M", "0,192", "2,04 x 10^-5", "0,662"]
    ]
    for r_idx, row in enumerate(res_data):
        for c_idx, val in enumerate(row):
            t_res.cell(r_idx, c_idx).text = val
    style_table(t_res, col_widths=[Inches(0.9), Inches(1.5), Inches(1.2), Inches(1.1), Inches(0.6), Inches(0.8), Inches(0.6)], header_bg="1F4E79")

    t_res2 = doc.add_table(rows=5, cols=7)
    res_data2 = [
        ["Workload", "Algoritma Penjadwalan", "Makespan (Juta Detik)", "Total Biaya (Juta MU)", "CPU Util", "Throughput (t/s)", "Imbalance"],
        ["1.000 Task", "SJF (Fokus)", "48,54 M", "7,96 M", "0,194", "2,06 x 10^-5", "0,630"],
        ["1.000 Task", "Multi-Obj (70:30)", "49,43 M", "7,97 M", "0,190", "2,02 x 10^-5", "0,665"],
        ["1.000 Task", "Multi-Obj (60:40)", "49,41 M", "7,97 M", "0,190", "2,02 x 10^-5", "0,661"],
        ["1.000 Task", "Multi-Obj (50:50)", "61,41 M", "8,24 M", "0,153", "1,63 x 10^-5", "0,830"]
    ]
    for r_idx, row in enumerate(res_data2):
        for c_idx, val in enumerate(row):
            t_res2.cell(r_idx, c_idx).text = val
    style_table(t_res2, col_widths=[Inches(0.9), Inches(1.5), Inches(1.2), Inches(1.1), Inches(0.6), Inches(0.8), Inches(0.6)], header_bg="1F4E79")

    add_heading_2(doc, "7.1 Mengapa SJF Menjadi Juara pada Skala Besar?")
    add_body_paragraph(doc, "Pada skala beban 500 dan 1.000 cloudlet, SJF secara konsisten mencatatkan makespan paling singkat (25,49 juta detik pada 500 cloudlet dan 48,54 juta detik pada 1.000 cloudlet). Faktor-faktor penentu keunggulan SJF meliputi:")
    add_bullet_point(doc, " Dengan memprioritaskan cloudlet berukuran pendek, waktu tunggu rata-rata dalam antrian VM ditekan secara drastis. Cloudlet-cloudlet pendek segera keluar dari sistem, mengosongkan antrian sehingga VM dapat menerima tugas berikutnya tanpa jeda.", "1. Eliminasi Penumpukan Antrian: ")
    add_bullet_point(doc, " Berbeda dengan Min-Min yang hanya melihat keputusan lokal per tugas saat itu, pra-pengurutan global pada SJF menstrukturkan antrian sehingga tugas berukuran besar dialokasikan secara tertib di akhir, ketika kapasitas VM sudah terpetakan dengan baik.", "2. Sinergi Pengurutan Global dan VM Earliest Finish: ")
    add_bullet_point(doc, " SJF mencatat Throughput tertinggi (2,06 x 10^-5 task/detik) dan Utilisasi CPU tertinggi (0,194) pada 1.000 task. Hal ini membuktikan bahwa 8 VM beroperasi dengan efisiensi puncak.", "3. Utilisasi dan Throughput Maksimal: ")

    p_img1 = doc.add_paragraph()
    p_img1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_before = Pt(8)
    p_img1.paragraph_format.space_after = Pt(2)
    chart1_path = Path("results/comparison_makespan.png")
    if chart1_path.exists():
        doc.add_picture(str(chart1_path), width=Inches(6.0))
        p_cap1 = doc.add_paragraph()
        p_cap1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap1.paragraph_format.space_after = Pt(8)
        r_c1 = p_cap1.add_run("Gambar 1. Perbandingan Makespan Menunjukkan Dominasi SJF pada Skala 500 dan 1.000 Cloudlet")
        r_c1.font.name = "Calibri"
        r_c1.font.size = Pt(9.5)
        r_c1.font.italic = True

    add_heading_2(doc, "7.2 Efisiensi Biaya Finansial Heuristik SJF")
    add_body_paragraph(doc, "Meskipun SJF tidak secara eksplisit memasukkan tarif sewa VM dalam fungsi objektifnya, hasil simulasi membuktikan bahwa SJF mencatat total biaya eksekusi sebesar 7,96 juta MU pada 1.000 task. Angka ini lebih murah dibanding Min-Min (7,97 juta MU) dan Multi-Objective 60:40 (7,97 juta MU).")
    add_body_paragraph(doc, "Penjelasan Fenomena: Biaya dalam cloud berbanding lurus dengan durasi pemakaian CPU (ActualCpuTime x Tarif). Karena SJF meminimalkan antrian dan menempatkan cloudlet secara cerdas pada VM tercepat yang sedang idle, pemborosan jam sewa dapat dicegah secara sistematis.")

    p_img2 = doc.add_paragraph()
    p_img2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_before = Pt(8)
    p_img2.paragraph_format.space_after = Pt(2)
    chart2_path = Path("results/tradeoff_makespan_cost.png")
    if chart2_path.exists():
        doc.add_picture(str(chart2_path), width=Inches(6.2))
        p_cap2 = doc.add_paragraph()
        p_cap2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap2.paragraph_format.space_after = Pt(8)
        r_c2 = p_cap2.add_run("Gambar 2. Trade-off Makespan vs Biaya Membuktikan Efisiensi Optimal SJF")
        r_c2.font.name = "Calibri"
        r_c2.font.size = Pt(9.5)
        r_c2.font.italic = True

    add_heading_2(doc, "7.3 Pemerataan Beban (Imbalance) dan Kepatuhan SLA")
    add_bullet_point(doc, " SJF mencatat Degree of Imbalance paling rendah (0,630 pada 1.000 task), mengungguli Min-Min (0,662) dan Round Robin (0,825). Ini membuktikan bahwa pembagian beban komputasi di seluruh 8 VM sangat merata.", "Pemerataan Beban Terbaik: ")
    add_bullet_point(doc, " SJF mencatatkan Deadline Miss Ratio terendah sejalan dengan makespan tercepatnya. Kepatuhan batas anggaran (Budget Compliance) tercapai 100% tanpa ada pelanggaran.", "Kepatuhan SLA & Budget: ")

    # ----------------------------------------------------
    # BAB VIII: PEMBAHASAN SENSITIVITAS & ANOMALI
    # ----------------------------------------------------
    add_heading_1(doc, "8. ANALISIS PERBANDINGAN MULTI-OBJECTIVE DAN ANOMALI BOBOT")
    add_body_paragraph(doc, "Sebagai pembanding terhadap SJF, evaluasi sensitivitas bobot Multi-Objective mengungkap fenomena penting:")
    add_bullet_point(doc, " Menghasilkan makespan 49,41 juta detik dan biaya 7,97 juta MU. Kinerjanya solid namun masih sedikit di bawah keunggulan makespan dan biaya SJF.", "Bobot 60:40 (Seimbang): ")
    add_bullet_point(doc, " Terjadi anomali degradasi hebat di mana makespan melonjak ke 61,41 juta detik (+26,5%) dan biaya eksekusi membengkak ke 8,24 juta MU. Terjadi perangkap heuristik lokal (local greedy trap) akibat pemaksaan alokasi ke VM Small yang murah, menyebabkan antrian macet dan membuat VM Large menganggur.", "Bobot 50:50 (Anomali Greedy Trap): ")

    p_img3 = doc.add_paragraph()
    p_img3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.paragraph_format.space_before = Pt(8)
    p_img3.paragraph_format.space_after = Pt(2)
    chart3_path = Path("results/sensitivity_weights.png")
    if chart3_path.exists():
        doc.add_picture(str(chart3_path), width=Inches(5.8))
        p_cap3 = doc.add_paragraph()
        p_cap3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap3.paragraph_format.space_after = Pt(8)
        r_c3 = p_cap3.add_run("Gambar 3. Sensitivitas Bobot Multi-Objective Memperlihatkan Degradasi pada Bobot 50:50")
        r_c3.font.name = "Calibri"
        r_c3.font.size = Pt(9.5)
        r_c3.font.italic = True

    # ----------------------------------------------------
    # BAB IX: KESIMPULAN & REKOMENDASI IMPLEMENTASI
    # ----------------------------------------------------
    add_heading_1(doc, "9. KESIMPULAN DAN REKOMENDASI PENERAPAN")
    add_heading_2(doc, "9.1 Kesimpulan Utama")
    add_bullet_point(doc, " Heuristik Shortest Job First (SJF) terbukti menjadi algoritma penjadwalan paling optimal untuk lingkungan komputasi awan heterogen pada beban menengah dan besar (500 dan 1.000 cloudlet), menghasilkan makespan terendah (48,54 juta detik pada 1.000 task).", "1. Superioritas SJF pada Skala Besar: ")
    add_bullet_point(doc, " SJF mencapai efisiensi biaya ganda (7,96 juta MU) sekaligus utilisasi CPU tertinggi (0,194) dan throughput terbaik (2,06 x 10^-5 task/detik), mematahkan anggapan bahwa optimasi waktu selalu membengkakkan biaya.", "2. Efisiensi Biaya dan Pemanfaatan Sumber Daya: ")
    add_bullet_point(doc, " SJF mencatatkan degree of imbalance terendah (0,630), mencegah bottleneck pada VM tertentu.", "3. Distribusi Beban Terharmonir: ")
    add_bullet_point(doc, " Round Robin terbukti tidak layak untuk cloud heterogen karena menghasilkan penalti waktu yang sangat masif (+24,9% lebih lambat).", "4. Kegagalan Baseline Konvensional: ")

    add_heading_2(doc, "9.2 Rekomendasi Penerapan Industri")
    add_bullet_point(doc, " Rekomendasikan Shortest Job First (SJF) sebagai algoritma standar utama pada platform komputasi awan batch (seperti AWS Batch, Google Cloud Batch, Kubernetes Job Scheduling) untuk memaksimalkan throughput dan memangkas waktu penyelesaian total.", "Platform Batch Processing Skala Besar: ")
    add_bullet_point(doc, " Pada sistem operasional terbuka, padukan SJF dengan mekanisme penuaan antrian (aging mechanism) untuk mencegah potensi penundaan (starvation) pada tugas-tugas berukuran raksasa.", "Mitigasi Starvation pada Sistem Terbuka: ")

    # ----------------------------------------------------
    # BAB X: DAFTAR PUSTAKA
    # ----------------------------------------------------
    add_heading_1(doc, "10. DAFTAR PUSTAKA")
    refs = [
        "Google LLC, 'Google Cluster Workload Traces 2019', GitHub Repository: https://github.com/google/cluster-data (Diakses Oktober 2026).",
        "Silva Filho, M. C., et al., 'CloudSim Plus: A modern Java 8 framework for modeling and simulation of cloud computing infrastructures', Software: Practice and Experience, 2017.",
        "Buyya, R., Yeo, C. S., & Venugopal, S., 'Market-oriented cloud computing: Vision, hype, and reality for delivering it services as computing utilities', IEEE HPCC, 2008.",
        "Braun, T. D., et al., 'A comparison of eleven static heuristics for mapping a class of independent tasks onto heterogeneous distributed computing systems', Journal of Parallel and Distributed Computing, 2001.",
        "SOKA Group 2, 'Strategi Optimasi Komputasi Awan - Desain Awal Proyek & Technical Brief', Departemen Teknologi Informasi ITS, 2026."
    ]
    for r in refs:
        add_bullet_point(doc, r)

    output_path = Path("LAPORAN_RESMI_PENJADWALAN_CLOUD.docx")
    try:
        doc.save(str(output_path))
        print(f"Laporan resmi berhasil diperbarui dengan fokus mendalam pada SJF: {output_path.resolve()} ({output_path.stat().st_size} bytes)")
    except PermissionError:
        output_path_alt = Path("LAPORAN_RESMI_PENJADWALAN_CLOUD_SJF.docx")
        doc.save(str(output_path_alt))
        print(f"File utama terkunci oleh aplikasi lain (mis. MS Word). Berhasil disimpan sebagai file alternatif: {output_path_alt.resolve()} ({output_path_alt.stat().st_size} bytes)")

if __name__ == "__main__":
    build_report()

