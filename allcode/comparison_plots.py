from __future__ import annotations

import csv

import os

import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, HERE)

from baselines import xauth, sslxiomt, scheme30

plt.rcParams.update(

    {

        "figure.dpi": 120,

        "savefig.dpi": 200,

        "axes.grid": True,

        "grid.alpha": 0.25,

        "grid.linestyle": "--",

        "axes.spines.top": False,

        "axes.spines.right": False,

        "font.size": 10,

        "axes.titlesize": 11,

        "axes.labelsize": 10,

        "legend.fontsize": 9,

        "xtick.labelsize": 9,

        "ytick.labelsize": 9,

    }

)

SCAPE_COLOR = "#c2185b"

BASE_COLORS = {

    "XAuth": "#37474f",

    "SSL-XIoMT": "#78909c",

    "Scheme [30]": "#b0bec5",

}

HATCHES = {

    "XAuth": "//",

    "SSL-XIoMT": "..",

    "Scheme [30]": "xx",

}

def build_data_table() -> dict:

    SCAPE = dict(

        compute_ms=869.062,

        comm_bytes=12_080,

        onchain_ms=None,

        onchain_bytes=740,

    )

    xa = xauth.simulate(n_certs_in_mmht=128, n_users_per_session=1)

    xauth_compute = xa["storage"].comp_ms + xa["verify"].comp_ms + xa["inquiry"].comp_ms

    xauth_comm = xa["proof_gen"].comm_bytes + xa["inquiry"].comm_bytes

    xauth_onchain_ms = xauth._ANCHOR_MS

    xauth_onchain_bytes = xa["storage"].comm_bytes

    sl = sslxiomt.simulate(n_proofs=1, concurrent_users=1, data_kb=1, n_attrs=10)

    sslxiomt_vc_issue_ms = 1209.7

    sslxiomt_verify_ms = 1000.0 / 918.0

    sslxiomt_compute = (

        sslxiomt_vc_issue_ms

        + sl["proof_total"].comp_ms

        + sslxiomt_verify_ms

        + sl["e2e"].comp_ms

    )

    sslxiomt_comm = 5_500

    sslxiomt_onchain_ms = 0.0

    sslxiomt_onchain_bytes = 0

    sc = scheme30.simulate(n_attrs=10, n_issuers=5, n_updates=1, n_users_batch=1)

    scheme30_compute = sc["showcred"].comp_ms + sc["verify"].comp_ms

    scheme30_comm = sc["showcred"].comm_bytes + sc["verify"].comm_bytes

    scheme30_onchain_ms = sc["update"].comp_ms

    scheme30_onchain_bytes = sc["update"].comm_bytes

    return {

        "SCAPE-ZK": SCAPE,

        "XAuth": dict(

            compute_ms=xauth_compute,

            comm_bytes=xauth_comm,

            onchain_ms=xauth_onchain_ms,

            onchain_bytes=xauth_onchain_bytes,

        ),

        "SSL-XIoMT": dict(

            compute_ms=sslxiomt_compute,

            comm_bytes=sslxiomt_comm,

            onchain_ms=sslxiomt_onchain_ms,

            onchain_bytes=sslxiomt_onchain_bytes,

        ),

        "Scheme [30]": dict(

            compute_ms=scheme30_compute,

            comm_bytes=scheme30_comm,

            onchain_ms=scheme30_onchain_ms,

            onchain_bytes=scheme30_onchain_bytes,

        ),

    }

def fig5_headline_normalized(data: dict) -> list[str]:



    axes = [

        ("Computation\n(per flow, ms)", "compute_ms"),

        ("Communication\n(per flow, bytes)", "comm_bytes"),

    ]

    schemes = ["XAuth", "SSL-XIoMT", "Scheme [30]"]

    ratios = {s: [] for s in schemes}

    raws = {s: [] for s in schemes}

    raw_scape = []

    for label, key in axes:

        scape = data["SCAPE-ZK"][key] or 1e-9

        raw_scape.append(data["SCAPE-ZK"][key])

        for s in schemes:

            v = data[s][key]

            raws[s].append(v)

            ratios[s].append(v / scape if scape else float("nan"))

    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    x = np.arange(len(axes))

    width = 0.25

    for i, s in enumerate(schemes):

        offset = (i - 1) * width

        bars = ax.bar(

            x + offset,

            ratios[s],

            width,

            color=BASE_COLORS[s],

            hatch=HATCHES[s],

            edgecolor="black",

            linewidth=0.6,

            label=s,

        )

        for j, b in enumerate(bars):

            r = ratios[s][j]

            raw = raws[s][j]

            unit = "ms" if "ms" in axes[j][0] else "B"

            label_txt = f"{r:.2f}×\n({raw:,.0f} {unit})"

            ax.text(

                b.get_x() + b.get_width() / 2,

                b.get_height(),

                label_txt,

                ha="center",

                va="bottom",

                fontsize=8,

                color="black",

            )

    ax.axhline(1.0, color=SCAPE_COLOR, linewidth=2.0, linestyle="--",

               label="SCAPE-ZK = 1.0 (reference)")

    sec = ax.secondary_xaxis("top")

    sec.set_xticks(x)

    sec.set_xticklabels(

        [f"SCAPE-ZK\n{raw_scape[i]:,.0f} {('ms' if 'ms' in axes[i][0] else 'B')}"

         for i in range(len(axes))],

        color=SCAPE_COLOR, fontweight="bold", fontsize=8,

    )

    ax.set_xticks(x)

    ax.set_xticklabels([a[0] for a in axes])

    ax.set_ylabel("Cost relative to SCAPE-ZK (lower bar = SCAPE-ZK loses)")

    ax.set_title(

        "SCAPE-ZK vs. baselines — reported per-flow cost axes\n"

        "(bars > 1 favour SCAPE-ZK; bars < 1 favour the baseline)"

    )

    ax.set_yscale("log")

    ax.set_ylim(0.005, 500)

    ax.legend(loc="upper right", framealpha=0.9, ncol=2)

    out_png = os.path.join(HERE, "fig5_headline_normalized.png")

    out_pdf = os.path.join(HERE, "fig5_headline_normalized.pdf")

    fig.tight_layout()

    fig.savefig(out_png)

    fig.savefig(out_pdf)

    plt.close(fig)

    return [out_png, out_pdf]

def fig6_comm_per_phase(data: dict) -> list[str]:


    phases = [

        ("Reg User→Issuer", 572),

        ("Reg Issuer→User", 2172),

        ("Session User→Verif", 1348),

        ("Session Verif→User", 492),

        ("Request User→Verif", 1348),

        ("Request Verif→User", 652),

        ("Aggregation→Chain", 740),

        ("Revocation→Chain", 724),

        ("PRE delegate", 540),

        ("PRE request", 652),

        ("IPFS put", 1420),

        ("IPFS get", 1420),

    ]

    labels = [p[0] for p in phases]

    values = [p[1] for p in phases]

    total = sum(values)

    fig, ax = plt.subplots(figsize=(10.0, 5.0))

    bar_colors = [SCAPE_COLOR if "Request" in l or "Session" in l else "#90a4ae"

                  for l in labels]

    bars = ax.bar(labels, values, color=bar_colors, edgecolor="black", linewidth=0.5)

    for b, v in zip(bars, values):

        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}",

                ha="center", va="bottom", fontsize=8)

    for s in ["XAuth", "SSL-XIoMT", "Scheme [30]"]:

        v = data[s]["comm_bytes"]

        ax.axhline(v, color=BASE_COLORS[s], linestyle=":", linewidth=1.6,

                   label=f"{s} total per flow ≈ {v:,} B")

    ax.axhline(total, color=SCAPE_COLOR, linestyle="--", linewidth=1.6,

               label=f"SCAPE-ZK total per flow = {total:,} B")

    ax.set_ylabel("Bytes on the wire (per flow)")

    ax.set_title("SCAPE-ZK communication overhead, per protocol phase\n"

                 "(MODELED, validated by tshark on Win11 + Npcap; sheet 05)")

    plt.xticks(rotation=30, ha="right")

    ax.legend(loc="upper right", fontsize=8)

    out_png = os.path.join(HERE, "fig6_comm_per_phase.png")

    out_pdf = os.path.join(HERE, "fig6_comm_per_phase.pdf")

    fig.tight_layout()

    fig.savefig(out_png)

    fig.savefig(out_pdf)

    plt.close(fig)

    return [out_png, out_pdf]

def fig7_cpcp_amortization() -> list[str]:



    session_setup_ms = 44.945 + 501.051 + 101.507

    per_request_ms = 115.654 + 4.583

    pre_per_request_ms = 1.628 + 99.693

    request_total_ms = per_request_ms + pre_per_request_ms

    ks = np.arange(1, 101)

    amortized_scape = (session_setup_ms + ks * request_total_ms) / ks

    xauth_per_req = 1323.0 + 9.0 + 1320.0

    sslxiomt_per_req = 1209.7 + 6.94 + 1.09 + 100.0

    scheme30_per_req = 23.07 + 31.42

    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    ax.plot(ks, amortized_scape, color=SCAPE_COLOR, linewidth=2.2,

            label=f"SCAPE-ZK amortized (Session $\\div$ k + Request)")

    ax.axhline(request_total_ms, color=SCAPE_COLOR, linestyle=":",

               label=f"SCAPE-ZK steady-state floor = {request_total_ms:.1f} ms")

    ax.axhline(xauth_per_req, color=BASE_COLORS["XAuth"], linestyle="--",

               label=f"XAuth per-auth = {xauth_per_req:.0f} ms")

    ax.axhline(sslxiomt_per_req, color=BASE_COLORS["SSL-XIoMT"], linestyle="--",

               label=f"SSL-XIoMT per-auth = {sslxiomt_per_req:.0f} ms")

    ax.axhline(scheme30_per_req, color=BASE_COLORS["Scheme [30]"], linestyle="--",

               label=f"Scheme [30] per-auth = {scheme30_per_req:.1f} ms")

    crossover_idx = np.argmax(amortized_scape <= scheme30_per_req)

    if crossover_idx > 0:

        k_cross = ks[crossover_idx]

        ax.axvline(k_cross, color="grey", linestyle=":", linewidth=0.8)

        ax.annotate(

            f"crossover\nk = {k_cross}",

            xy=(k_cross, scheme30_per_req),

            xytext=(k_cross + 5, scheme30_per_req * 4),

            fontsize=8,

            arrowprops=dict(arrowstyle="->", color="grey"),

        )

    ax.set_xlabel("Number of requests per session (k)")

    ax.set_ylabel("Amortized cost per request (ms) — lower is better")

    ax.set_title("Two-tier CPCP amortization advantage\n"

                 "(SCAPE-ZK pays Session prove once; baselines pay per request)")

    ax.set_yscale("log")

    ax.legend(loc="upper right", fontsize=8)

    ax.set_xlim(1, 100)

    out_png = os.path.join(HERE, "fig7_cpcp_amortization.png")

    out_pdf = os.path.join(HERE, "fig7_cpcp_amortization.pdf")

    fig.tight_layout()

    fig.savefig(out_png)

    fig.savefig(out_pdf)

    plt.close(fig)

    return [out_png, out_pdf]

def fig8_comm_reduction_pct(data: dict) -> list[str]:



    scape_core = 572 + 2172 + 1348 + 492 + 1348 + 652

    scape_extended = 740 + 724 + 540 + 652 + 1420 + 1420

    scape_total = scape_core + scape_extended

    schemes = ["XAuth", "SSL-XIoMT", "Scheme [30]"]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.5, 4.6))

    ax = axL

    x = np.arange(len(schemes) + 1)

    labels = ["SCAPE-ZK"] + schemes

    core_vals = [scape_core] + [data[s]["comm_bytes"] for s in schemes]

    ext_vals = [scape_extended] + [0, 0, 0]

    bars1 = ax.bar(x, core_vals, color=[SCAPE_COLOR] + [BASE_COLORS[s] for s in schemes],

                   hatch=["", *[HATCHES[s] for s in schemes]], edgecolor="black",

                   linewidth=0.6, label="Core auth (Reg + Session + Request)")

    bars2 = ax.bar(x, ext_vals, bottom=core_vals,

                   color=SCAPE_COLOR, alpha=0.45, edgecolor="black", linewidth=0.5,

                   label="Extended (Aggregation, Revocation, PRE, IPFS)")

    for b, v, e in zip(bars1, core_vals, ext_vals):

        total = v + e

        ax.text(b.get_x() + b.get_width() / 2, total, f"{int(total):,} B",

                ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)

    ax.set_xticklabels(labels)

    ax.set_ylabel("Bytes on the wire per flow")

    ax.set_title("Communication overhead per flow\n(scope-aligned breakdown)")

    ax.legend(loc="upper right", fontsize=8)

    ax2 = axR

    pcts = []

    annots = []

    for s in schemes:

        v = data[s]["comm_bytes"]

        pct = 100.0 * (v - scape_core) / v if v > 0 else float("nan")

        pcts.append(pct)

        annots.append((scape_core, v, pct))

    colors = [BASE_COLORS[s] for s in schemes]

    bars = ax2.bar(schemes, pcts, color=colors, hatch="//", edgecolor="black", linewidth=0.6)

    for b, (sc_b, b_b, pct), s in zip(bars, annots, schemes):

        arrow = "↓" if pct >= 0 else "↑"

        ax2.text(

            b.get_x() + b.get_width() / 2,

            b.get_height() + (4 if b.get_height() >= 0 else -8),

            f"{arrow}{abs(pct):.1f}%\nSCAPE core {sc_b:,} B\nvs {s} {b_b:,} B",

            ha="center",

            va="bottom" if b.get_height() >= 0 else "top",

            fontsize=8,

        )

    ax2.axhline(0, color="black", linewidth=0.8)

    ax2.axhspan(62.5, 92.79, alpha=0.15, color="green",

                label="Scheme [30] headline range (62.5–92.79 %)")

    ax2.set_ylabel("Comm reduction (%) — SCAPE-ZK core vs baseline\n"

                   "(positive = SCAPE-ZK uses fewer bytes)")

    ax2.set_title("Comms reduction, scope-aligned (Reg + Session + Request only)")

    ax2.legend(loc="lower right", fontsize=8)

    lo = min(min(pcts) - 30, -100)

    ax2.set_ylim(lo, 100)

    out_png = os.path.join(HERE, "fig8_comm_reduction_pct.png")

    out_pdf = os.path.join(HERE, "fig8_comm_reduction_pct.pdf")

    fig.tight_layout()

    fig.savefig(out_png)

    fig.savefig(out_pdf)

    plt.close(fig)

    return [out_png, out_pdf]

def write_audit_csv(data: dict) -> str:

    out = os.path.join(HERE, "comparison_table_day6.csv")

    with open(out, "w", newline="") as f:

        w = csv.writer(f)

        w.writerow(

            [

                "Scheme",

                "compute_ms_per_flow",

                "comm_bytes_per_flow",

                "onchain_ms_per_flow",

                "onchain_bytes_per_flow",

                "scope_notes",

            ]

        )

        notes = {

            "SCAPE-ZK": "v13 sheet 11 row 11 1000-run E2E mean + sheet 05 row 16; on-chain cost not reported because Sheet 04 was not measured",

            "XAuth": "Per-auth flow excludes 89.7s registration proof_gen (one-time per user); MMHT n=128",

            "SSL-XIoMT": "vc_issue + proof + verify + e2e; comm ESTIMATED (paper does not break out per-phase bytes)",

            "Scheme [30]": "ShowCred + Verify at n_k=10, n_I=5; Update treated as on-chain operation",

        }

        for s in ["SCAPE-ZK", "XAuth", "SSL-XIoMT", "Scheme [30]"]:

            d = data[s]

            w.writerow(

                [

                    s,

                    f"{d['compute_ms']:.2f}",

                    f"{d['comm_bytes']:.0f}",

                    "" if d["onchain_ms"] is None else f"{d['onchain_ms']:.2f}",

                    f"{d['onchain_bytes']:.0f}",

                    notes[s],

                ]

            )

    return out

def main() -> None:

    data = build_data_table()

    audit = write_audit_csv(data)

    outputs = []

    outputs += fig5_headline_normalized(data)

    outputs += fig6_comm_per_phase(data)

    outputs += fig7_cpcp_amortization()

    outputs += fig8_comm_reduction_pct(data)

    print("Audit CSV: ", audit)

    print("Wrote figures:")

    for o in outputs:

        print(f"  {o}")

if __name__ == "__main__":

    main()
