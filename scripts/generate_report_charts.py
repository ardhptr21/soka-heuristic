import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("results", exist_ok=True)
results_dir = Path("results")

# Setup styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

# Data definition based on validated 180 simulation runs
algorithms = ['Round Robin', 'Min-Min', 'SJF', 'Multi-Obj (60:40)']
colors = ['#4472C4', '#ED7D31', '#2CA02C', '#70AD47']

# 1. Comparison Makespan across workloads (juta detik)
workloads = ['100 Cloudlets', '500 Cloudlets', '1.000 Cloudlets']
makespan_data = {
    'Round Robin': [6.57, 30.53, 60.61],
    'Min-Min': [5.71, 26.02, 48.96],
    'SJF': [5.82, 25.49, 48.54],
    'Multi-Obj (70:30)': [5.73, 26.01, 49.43],
    'Multi-Obj (60:40)': [5.74, 26.05, 49.41]
}

fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(workloads))
width = 0.17

ax.bar(x - 2*width + width/2, makespan_data['Round Robin'], width, label='Round Robin', color='#4A90E2', edgecolor='black', linewidth=0.5)
ax.bar(x - width + width/2, makespan_data['Min-Min'], width, label='Min-Min', color='#F5A623', edgecolor='black', linewidth=0.5)
ax.bar(x + width/2, makespan_data['SJF'], width, label='SJF', color='#27AE60', edgecolor='black', linewidth=0.5)
ax.bar(x + width + width/2, makespan_data['Multi-Obj (60:40)'], width, label='Multi-Obj (60:40)', color='#9B51E0', edgecolor='black', linewidth=0.5)

ax.set_title('Perbandingan Makespan Lintas Skala Workload (Rata-rata 10 Replikasi)', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Ukuran Workload (Jumlah Cloudlet)', fontsize=10, fontweight='bold')
ax.set_ylabel('Makespan (Juta Detik)', fontsize=10, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(workloads, fontsize=10)
ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
ax.grid(axis='y', linestyle='--', alpha=0.5)

for p in ax.patches:
    h = p.get_height()
    if h > 0:
        ax.annotate(f"{h:.2f}M", (p.get_x() + p.get_width() / 2., h),
                    ha='center', va='bottom', fontsize=7.5, xytext=(0, 2),
                    textcoords='offset points', fontweight='semibold')

plt.tight_layout()
fig.savefig(results_dir / "comparison_makespan.png", dpi=300)
plt.close(fig)

# 2. Trade-off Makespan vs Cost pada 1.000 Cloudlet
labels_all = ['Round Robin', 'Min-Min', 'SJF', 'Multi (70:30)', 'Multi (60:40)', 'Multi (50:50)']
ms_1000 = [60.61, 48.96, 48.54, 49.43, 49.41, 61.41]
cost_1000 = [7.66, 7.97, 7.96, 7.97, 7.97, 8.24]

fig, ax1 = plt.subplots(figsize=(9, 4.5))

color_ms = '#2980B9'
color_cost = '#E67E22'

x_idx = np.arange(len(labels_all))
w_bar = 0.35

rects1 = ax1.bar(x_idx - w_bar/2, ms_1000, w_bar, label='Makespan (Juta Detik)', color=color_ms, edgecolor='black', linewidth=0.5)
ax1.set_ylabel('Makespan (Juta Detik)', color=color_ms, fontsize=10, fontweight='bold')
ax1.tick_params(axis='y', labelcolor=color_ms)
ax1.set_xticks(x_idx)
ax1.set_xticklabels(labels_all, fontsize=9, rotation=10)
ax1.set_ylim(40, 70)

ax2 = ax1.twinx()
rects2 = ax2.bar(x_idx + w_bar/2, cost_1000, w_bar, label='Execution Cost (Juta MU)', color=color_cost, edgecolor='black', linewidth=0.5)
ax2.set_ylabel('Biaya Eksekusi (Juta MU)', color=color_cost, fontsize=10, fontweight='bold')
ax2.tick_params(axis='y', labelcolor=color_cost)
ax2.set_ylim(6.5, 9.0)

for r in rects1:
    h = r.get_height()
    ax1.annotate(f"{h:.2f}M", (r.get_x() + r.get_width() / 2., h),
                 ha='center', va='bottom', fontsize=8, xytext=(0, 2),
                 textcoords='offset points', color='#1B4F72', fontweight='bold')

for r in rects2:
    h = r.get_height()
    ax2.annotate(f"{h:.2f}M", (r.get_x() + r.get_width() / 2., h),
                 ha='center', va='bottom', fontsize=8, xytext=(0, 2),
                 textcoords='offset points', color='#935116', fontweight='bold')

plt.title('Trade-Off Makespan vs Total Execution Cost pada 1.000 Cloudlet', fontsize=12, fontweight='bold', pad=12)
plt.tight_layout()
fig.savefig(results_dir / "tradeoff_makespan_cost.png", dpi=300)
plt.close(fig)

# 3. Sensitivity Analysis Multi-Objective Weights
fig, ax = plt.subplots(figsize=(7.5, 4.2))
weights = ['70:30\n(Time:Cost)', '60:40\n(Time:Cost)', '50:50\n(Time:Cost)']
ms_sens = [49.43, 49.41, 61.41]
cost_sens = [7.97, 7.97, 8.24]

ax.plot(weights, ms_sens, marker='o', linewidth=2.5, markersize=8, color='#2980B9', label='Makespan (Juta Detik)')
for i, txt in enumerate(ms_sens):
    ax.annotate(f"{txt:.2f}M s", (weights[i], ms_sens[i]), xytext=(0, 8), textcoords='offset points',
                ha='center', fontweight='bold', color='#1B4F72')

ax.set_ylabel('Makespan (Juta Detik)', color='#2980B9', fontsize=10, fontweight='bold')
ax.tick_params(axis='y', labelcolor='#2980B9')
ax.set_ylim(45, 68)

ax_c = ax.twinx()
ax_c.plot(weights, cost_sens, marker='s', linewidth=2.5, markersize=8, color='#E67E22', linestyle='--', label='Cost (Juta MU)')
for i, txt in enumerate(cost_sens):
    ax_c.annotate(f"{txt:.2f}M MU", (weights[i], cost_sens[i]), xytext=(0, -15), textcoords='offset points',
                  ha='center', fontweight='bold', color='#935116')

ax_c.set_ylabel('Execution Cost (Juta MU)', color='#E67E22', fontsize=10, fontweight='bold')
ax_c.tick_params(axis='y', labelcolor='#E67E22')
ax_c.set_ylim(7.5, 8.6)

plt.title('Sensitivitas Bobot Multi-Objective terhadap Makespan & Biaya (1.000 Cloudlet)', fontsize=11, fontweight='bold', pad=12)
plt.tight_layout()
fig.savefig(results_dir / "sensitivity_weights.png", dpi=300)
plt.close(fig)

print("Charts successfully generated in results/")
