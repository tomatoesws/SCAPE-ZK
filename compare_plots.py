from __future__ import annotations

import os

import sys

import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, HERE)

from baselines import xauth, subbaselines as sb

import scape_zk_loader as scz

plt.rcParams.update({

    "figure.figsize": (8.5, 5.0),

    "figure.dpi": 120,

    "axes.grid": True,

    "grid.alpha": 0.25,

    "axes.spines.top": False,

    "axes.spines.right": False,

    "font.size": 11,

})

SCAPE_COLOR = "#c2185b"

SCAPE_MARKER = dict(marker="*", s=220, zorder=10, color=SCAPE_COLOR,

                    edgecolor="black", linewidth=0.8,

                    label="SCAPE-ZK (measured)")

def fig1_proof_gen_vs_nproofs() -> str:

    ns = [100, 500, 1_000, 2_000, 5_000, 10_000]

    fig, ax = plt.subplots()

    for name, fn in sb.SSLXIOMT_PEERS.items():

        y_s = [fn(n) / 1000.0 for n in ns]

        ax.plot(ns, y_s, marker="o", label=name)

    xauth_total_per_user_s = xauth.derived_total_gen_ms() / 1000.0

    ax.plot(ns, [xauth_total_per_user_s * n for n in ns],

            linestyle="--", marker="x", label="XAuth (per-proof user cost)")

    scape_total_ms = scz.scape_zk_total_ms()

    if scape_total_ms:

        y_scape = [scape_total_ms * n / 1000.0 for n in ns]

        ax.plot(ns, y_scape, linestyle=":", color=SCAPE_COLOR,

                label=f"SCAPE-ZK ({scape_total_ms:.2f} ms/session)")

        ax.scatter([1_000], [scape_total_ms * 1_000 / 1000.0], **SCAPE_MARKER)

    ax.set_xlabel("Number of proofs")

    ax.set_ylabel("Total proof time (seconds)")

    ax.set_title("Proof generation + verification vs number of proofs")

    ax.set_yscale("log")

    ax.legend(fontsize=9, loc="upper left")

    out = os.path.join(HERE, "fig1_proof_gen_vs_nproofs.png")

    fig.tight_layout()

    fig.savefig(out)

    plt.close(fig)

    return out

def fig2_verify_per_cert() -> str:

    labels = []

    values = []

    for name, fn in sb.XAUTH_PEERS.items():

        labels.append(name)

        values.append(fn(1))

    labels.append("SSL-XIoMT")

    values.append(6.94)

    labels.append("Scheme [30]")

    values.append(sb.SCHEME30_SHOWCRED_PEERS["Scheme [30]"](10, 5))

    from baselines import scheme30 as s30

    labels.append("Scheme [30] verify")

    values.append(s30.simulate(n_attrs=10, n_issuers=5)["verify"].comp_ms)

    scape_v = scz.scape_zk_verify_ms()

    if scape_v is not None:

        labels.append("SCAPE-ZK")

        values.append(scape_v)

    colors = ["#455a64"] * (len(labels) - 1) + [SCAPE_COLOR]

    fig, ax = plt.subplots()

    bars = ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.5)

    for b, v in zip(bars, values):

        ax.text(b.get_x() + b.get_width()/2, v, f"{v:.2f}",

                ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Verification latency (ms) — lower is better")

    ax.set_title("Per-certificate / per-proof verification latency")

    plt.xticks(rotation=25, ha="right")

    ax.set_yscale("log")

    out = os.path.join(HERE, "fig2_verify_per_cert.png")

    fig.tight_layout()

    fig.savefig(out)

    plt.close(fig)

    return out

def fig3_comm_vs_attrs_issuers() -> str:

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.0))

    n_ks = list(range(5, 55, 5))

    for name, fn in sb.SCHEME30_COMM_PEERS.items():

        ys = [fn(k, 5) for k in n_ks]

        axL.plot(n_ks, ys, marker="o", label=name)

    scape_B = scz.scape_zk_auth_comm_bytes()

    if scape_B is not None:

        axL.axhline(scape_B, linestyle="--", color=SCAPE_COLOR,

                    label=f"SCAPE-ZK measured ({scape_B:,} B)")

    axL.set_xlabel("Disclosed attributes n_k")

    axL.set_ylabel("Authentication comm. (bytes)")

    axL.set_title("Comm. overhead vs disclosed attributes (n_I=5)")

    axL.set_yscale("log")

    axL.legend(fontsize=8)

    n_Is = [5, 10, 15, 20, 25, 30, 35, 40]

    for name, fn in sb.SCHEME30_SHOWCRED_PEERS.items():

        ys = [fn(10, i) for i in n_Is]

        axR.plot(n_Is, ys, marker="s", label=name)

    axR.set_xlabel("Number of issuers n_I")

    axR.set_ylabel("ShowCred latency (ms)")

    axR.set_title("ShowCred latency vs #issuers (n_k=10)")

    axR.legend(fontsize=8)

    out = os.path.join(HERE, "fig3_comm_vs_attrs_issuers.png")

    fig.tight_layout()

    fig.savefig(out)

    plt.close(fig)

    return out

def fig4_mmht_storage_vs_leaves() -> str:

    ns = [4, 8, 16, 32, 64, 128, 256, 512]

    xauth_bytes = [xauth.mmht_size(n) for n in ns]

    paper_anchors = {

        4: 503, 8: 1007, 16: int(1.97 * 1024), 32: int(3.95 * 1024),

        64: int(7.92 * 1024), 128: int(15.8 * 1024),

    }

    fig, ax = plt.subplots()

    ax.plot(ns, xauth_bytes, marker="o", label="XAuth model (125·n + 6.4·(n-1))")

    ax.scatter(list(paper_anchors.keys()), list(paper_anchors.values()),

               marker="D", color="#ff9800", s=60, zorder=5,

               label="XAuth paper Table 3 (anchors)")

    y_scape = [scz.scape_zk_storage_bytes_for_records(n) for n in ns]

    y_scape = [y for y in y_scape if y is not None]

    if y_scape and len(y_scape) == len(ns):

        ax.plot(ns, y_scape, linestyle="--", marker="*", color=SCAPE_COLOR,

                label="SCAPE-ZK (IPFS_put + aggregation, scaled)")

    ax.set_xlabel("Number of leaf nodes / records")

    ax.set_ylabel("Storage bytes")

    ax.set_title("Storage cost vs data volume")

    ax.set_xscale("log", base=2)

    ax.set_yscale("log")

    ax.legend(fontsize=9)

    out = os.path.join(HERE, "fig4_mmht_storage_vs_leaves.png")

    fig.tight_layout()

    fig.savefig(out)

    plt.close(fig)

    return out

def main() -> None:

    outputs = [

        fig1_proof_gen_vs_nproofs(),

        fig2_verify_per_cert(),

        fig3_comm_vs_attrs_issuers(),

        fig4_mmht_storage_vs_leaves(),

    ]

    print("Wrote:")

    for o in outputs:

        print(f"  {o}")

if __name__ == "__main__":

    main()
