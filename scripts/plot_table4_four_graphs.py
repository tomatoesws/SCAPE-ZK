import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'lines.linewidth': 2.5,
    'axes.labelsize': 14,
    'axes.titlesize': 15,
    'figure.dpi': 300
})

colors = ['#E31A1C', '#1F78B4', '#33A02C', '#FF7F00', '#6A3D9A']
markers = ['s', 'o', '^', 'D', 'P']
styles = ['-', '-', '-', '-', '-']


def plot_line(ax, x, y, label, color, marker, ls):
    ax.plot(
        x,
        y,
        label=label,
        color=color,
        marker=marker,
        linestyle=ls,
        markersize=8,
        markeredgecolor='black',
        markeredgewidth=0.5,
    )
    for xi, yi in zip(x, y):
        ax.annotate(
            f"{yi:.3f}",
            (xi, yi),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            va="bottom",
            fontsize=9,
            color=color,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7),
        )


def finalize(ax, title, xlabel, ylabel, is_log=False, x_ticks=None):
    ax.set_title(title, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontweight='bold')
    ax.set_ylabel(ylabel, fontweight='bold')

    if x_ticks is not None:
        ax.set_xticks(x_ticks)

    if is_log:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

    ax.grid(True, which='both', linestyle='-', alpha=0.4)
    ax.legend(
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        borderaxespad=0.,
        frameon=True,
        fontsize=11,
    )
    plt.tight_layout()


n_range = [5, 10, 20, 50]
batch_range = [1, 10, 50, 100, 200]

# 1. Proof Generation (Setup)
fig1, ax1 = plt.subplots(figsize=(12, 6))
data1 = {
    'XAuth [6]': [89700.0, 89700.0, 89700.0, 89700.0],
    'SSL-XIoMT [8]': [6.94, 6.94, 6.94, 6.94],
    'Scheme [30]': [34.028639, 36.323984, 40.914674, 54.686744],
    'SCAPE-ZK (Ours)': [686.389, 752.726, 842.840, 1134.440]
}
for i, (label, values) in enumerate(data1.items()):
    plot_line(ax1, n_range, values, label, colors[i], markers[i], styles[i])
finalize(
    ax1,
    "Proof Generation Latency",
    "Number of Attributes",
    "Execution Time (ms)",
    is_log=True,
    x_ticks=n_range,
)
plt.savefig('results/figures/graph_1_proof_gen_setup.png')
plt.close(fig1)

# 2. Amortized Proof Generation
fig2, ax2 = plt.subplots(figsize=(12, 6))
data2 = {
    'XAuth [6]': [89700.0, 89700.0, 89700.0, 89700.0],
    'SSL-XIoMT [8]': [6.94, 6.94, 6.94, 6.94],
    'Scheme [30]': [18.394849, 20.690194, 20.690194, 20.690194],
    'SCAPE-ZK (Ours)': [156.803860, 158.130600, 159.932880, 165.764880]
}
for i, (label, values) in enumerate(data2.items()):
    plot_line(ax2, n_range, values, label, colors[i], markers[i], styles[i])
finalize(
    ax2,
    "Amortized Proof Generation Latency",
    "Number of Attributes",
    "Execution Time (ms)",
    is_log=True,
    x_ticks=n_range,
)
plt.savefig('results/figures/graph_2_amortized.png')
plt.close(fig2)

# 3. Encryption Latency
fig3, ax3 = plt.subplots(figsize=(12, 6))
data3 = {
    'SSL-XIoMT [8]': [34.947978, 39.527593, 48.686823, 76.164513],
    'SCAPE-ZK (Ours)': [13.091700, 25.152800, 48.545200, 117.571200]
}
for i, (label, values) in enumerate(data3.items()):
    plot_line(ax3, n_range, values, label, colors[i + 1], markers[i + 1], styles[i + 1])
finalize(
    ax3,
    "Encryption Latency",
    "Number of Attributes",
    "Execution Time (ms)",
    x_ticks=n_range,
)
plt.savefig('results/figures/graph_3_encryption.png')
plt.close(fig3)

# 4. Verification Latency
fig4, ax4 = plt.subplots(figsize=(12, 6))
data4 = {
    'XAuth [6]': [9.0, 90.0, 450.0, 900.0, 1800.0],
    'SSL-XIoMT [8]': [1.089325, 10.893246, 54.466231, 108.932462, 217.864924],
    'Scheme [30]': [30.843951, 30.863886, 30.952486, 31.063236, 31.284736],
    'SCAPE-ZK (Ours)': [13.293, 13.293, 13.293, 13.293, 13.293]
}
for i, (label, values) in enumerate(data4.items()):
    plot_line(ax4, batch_range, values, label, colors[i], markers[i], styles[i])
finalize(
    ax4,
    "Proof Verification Latency",
    "Batch Size",
    "Execution Time (ms)",
    is_log=True,
    x_ticks=batch_range,
)
plt.savefig('results/figures/graph_4_verification.png')
plt.close(fig4)

print('Saved results/figures/graph_1_proof_gen_setup.png')
print('Saved results/figures/graph_2_amortized.png')
print('Saved results/figures/graph_3_encryption.png')
print('Saved results/figures/graph_4_verification.png')
