from __future__ import annotations

from html import escape

from pathlib import Path

from .paper_metrics import PAPER_FACTS

OUT_DIR = Path(__file__).resolve().parent / "figures"

def svg_text(x: int, y: int, text: str, cls: str = "label", anchor: str = "start") -> str:

    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(text)}</text>'

def write_svg(name: str, body: str, width: int = 1000, height: int = 620) -> None:

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
.title {{ font: 700 28px Georgia, serif; fill: #1b2a41; }}
.subtitle {{ font: 400 16px Georgia, serif; fill: #465362; }}
.axis {{ font: 500 14px 'Courier New', monospace; fill: #334; }}
.label {{ font: 600 16px Georgia, serif; fill: #223; }}
.value {{ font: 700 16px 'Courier New', monospace; fill: #102a43; }}
.note {{ font: 400 15px Georgia, serif; fill: #4f5d75; }}
.small {{ font: 400 13px Georgia, serif; fill: #4f5d75; }}
.grid {{ stroke: #d9e2ec; stroke-width: 1; }}
</style>
{body}
</svg>
"""

    (OUT_DIR / name).write_text(svg, encoding="utf-8")

def proof_figure() -> None:

    facts = PAPER_FACTS["proof_generation_verification"]

    max_value = facts["scheme_31_seconds"]

    left = 130

    baseline = 500

    width = 180

    gap = 90

    def bar_height(value: float) -> float:

        return (value / max_value) * 320

    scheme31_h = bar_height(facts["scheme_31_seconds"])

    scheme29_h = bar_height(facts["scheme_29_seconds"])

    ssl_min_h = bar_height(facts["ssl_xiomt_seconds_min"])

    ssl_max_h = bar_height(facts["ssl_xiomt_seconds_max"])

    body = [

        svg_text(60, 60, "Proof Gen. + Verification Time", "title"),

        svg_text(60, 88, "Only values explicitly stated in the paper text are plotted", "subtitle"),

    ]

    for tick in (0, 100, 200, 300, 400, 500):

        y = baseline - bar_height(tick)

        body.append(f'<line x1="120" y1="{y}" x2="860" y2="{y}" class="grid"/>')

        body.append(svg_text(105, int(y + 5), str(tick), "axis", "end"))

    body.extend(

        [

            f'<rect x="{left}" y="{baseline - scheme31_h}" width="{width}" height="{scheme31_h}" fill="#9f1239" rx="8"/>',

            svg_text(left + width / 2, baseline + 30, "Scheme [31]", "label", "middle"),

            svg_text(left + width / 2, int(baseline - scheme31_h - 10), "522.3 s", "value", "middle"),

        ]

    )

    x2 = left + width + gap

    body.extend(

        [

            f'<rect x="{x2}" y="{baseline - scheme29_h}" width="{width}" height="{scheme29_h}" fill="#d97706" rx="8"/>',

            svg_text(x2 + width / 2, baseline + 30, "Scheme [29]", "label", "middle"),

            svg_text(x2 + width / 2, int(baseline - scheme29_h - 10), "109.7 s", "value", "middle"),

        ]

    )

    x3 = x2 + width + gap

    body.extend(

        [

            f'<rect x="{x3}" y="{baseline - ssl_max_h}" width="{width}" height="{ssl_max_h - ssl_min_h}" fill="#0f766e" rx="8"/>',

            f'<rect x="{x3}" y="{baseline - ssl_min_h}" width="{width}" height="{ssl_min_h}" fill="#14b8a6" rx="8" opacity="0.35"/>',

            svg_text(x3 + width / 2, baseline + 30, "SSL-XIoMT", "label", "middle"),

            svg_text(x3 + width / 2, int(baseline - ssl_max_h - 10), "69.4-76.8 s", "value", "middle"),

            svg_text(60, 575, f"Scope in paper: {facts['scope']}", "note"),

        ]

    )

    write_svg("proof_gen_verification_points.svg", "\n".join(body))

def throughput_figure() -> None:

    facts = PAPER_FACTS["integrity_verification"]

    max_value = facts["ssl_xiomt_peak_verifications_per_second"]

    baseline = 470

    left = 180

    width = 220

    gap = 150

    def bar_height(value: float) -> float:

        return (value / max_value) * 280

    ssl_h = bar_height(facts["ssl_xiomt_peak_verifications_per_second"])

    s31_h = bar_height(facts["scheme_31_peak_verifications_per_second"])

    body = [

        svg_text(60, 60, "Integrity Verification Throughput", "title"),

        svg_text(60, 88, "Paper-reported peaks and crossover facts only", "subtitle"),

        f'<rect x="{left}" y="{baseline - ssl_h}" width="{width}" height="{ssl_h}" fill="#0f766e" rx="8"/>',

        f'<rect x="{left + width + gap}" y="{baseline - s31_h}" width="{width}" height="{s31_h}" fill="#9f1239" rx="8"/>',

        svg_text(left + width / 2, baseline + 30, "SSL-XIoMT", "label", "middle"),

        svg_text(left + width + gap + width / 2, baseline + 30, "Scheme [31]", "label", "middle"),

        svg_text(left + width / 2, int(baseline - ssl_h - 10), "918 / s", "value", "middle"),

        svg_text(left + width + gap + width / 2, int(baseline - s31_h - 10), "777 / s", "value", "middle"),

        svg_text(60, 540, f"SSL-XIoMT surpasses Scheme [31] after > {facts['ssl_xiomt_throughput_surpasses_after_concurrent_requests']} concurrent requests.", "note"),

        svg_text(60, 568, f"Peak SSL-XIoMT throughput is reported at {facts['ssl_xiomt_peak_user_range']}.", "note"),

        svg_text(60, 596, f"Latency advantage is reported once requests exceed {facts['ssl_xiomt_outperforms_latency_after_requests']}.", "note"),

    ]

    write_svg("integrity_throughput_peaks.svg", "\n".join(body))

def transmission_fact_figure() -> None:

    seconds = PAPER_FACTS["secure_cross_domain_transmission"]["all_compared_schemes_under_seconds"]

    body = [

        svg_text(60, 70, "Secure Cross-Domain Transmission", "title"),

        svg_text(60, 100, "The paper text does not expose Table 3 cell values in extractable form", "subtitle"),

        '<rect x="80" y="150" width="840" height="250" rx="18" fill="#f0f9ff" stroke="#7dd3fc" stroke-width="2"/>',

        svg_text(500, 250, f"All compared schemes completed the end-to-end process in under {seconds} seconds.", "title", "middle"),

        svg_text(500, 305, "This figure intentionally avoids invented per-step or per-scheme timings.", "note", "middle"),

        svg_text(500, 352, "Missing Table 3 cells require manual transcription or OCR from the PDF page.", "note", "middle"),

    ]

    write_svg("secure_transmission_fact.svg", "\n".join(body))

def main() -> None:

    proof_figure()

    throughput_figure()

    transmission_fact_figure()

if __name__ == "__main__":

    main()
