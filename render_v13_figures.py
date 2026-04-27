from __future__ import annotations

import math

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from reportlab.lib import colors

from reportlab.lib.pagesizes import landscape, letter

from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent

def font(size: int, bold: bool = False):

    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]

    for name in names:

        try:

            return ImageFont.truetype(name, size)

        except OSError:

            pass

    return ImageFont.load_default()

def draw_center(draw: ImageDraw.ImageDraw, xy, text, fill, fnt):

    bbox = draw.textbbox((0, 0), text, font=fnt)

    draw.text((xy[0] - (bbox[2] - bbox[0]) / 2, xy[1] - (bbox[3] - bbox[1]) / 2), text, fill=fill, font=fnt)

def save_pdf_from_png(png: Path, pdf: Path):

    img = Image.open(png).convert("RGB")

    c = canvas.Canvas(str(pdf), pagesize=landscape(letter))

    w, h = landscape(letter)

    c.drawImage(str(png), 0, 0, width=w, height=h, preserveAspectRatio=True, anchor="c")

    c.save()

def fig5():

    schemes = ["XAuth", "SSL-XIoMT", "Scheme [30]"]

    colors_map = {"XAuth": "#455a64", "SSL-XIoMT": "#78909c", "Scheme [30]": "#b0bec5"}

    axes = [

        ("Computation per flow", "ms", 869.06, {"XAuth": 2652.00, "SSL-XIoMT": 1317.73, "Scheme [30]": 54.49}),

        ("Communication per flow", "B", 12080, {"XAuth": 352, "SSL-XIoMT": 5500, "Scheme [30]": 1620}),

    ]

    img = Image.new("RGB", (1500, 900), "white")

    d = ImageDraw.Draw(img)

    title = font(34, True)

    body = font(22)

    small = font(18)

    d.text((70, 35), "SCAPE-ZK vs. baselines - reported per-flow cost axes", fill="#263238", font=title)

    d.text((70, 80), "Bars show baseline / SCAPE-ZK. Values above 1 favor SCAPE-ZK; values below 1 favor the baseline.", fill="#37474f", font=body)

    chart_left, chart_top, chart_right, chart_bottom = 120, 170, 1390, 700

    d.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#263238", width=2)

    d.line((chart_left, chart_top, chart_left, chart_bottom), fill="#263238", width=2)

    max_log, min_log = math.log10(4), math.log10(0.02)

    for tick in [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 4]:

        y = chart_bottom - (math.log10(tick) - min_log) / (max_log - min_log) * (chart_bottom - chart_top)

        d.line((chart_left - 8, y, chart_right, y), fill="#eceff1", width=1)

        d.text((45, y - 10), f"{tick:g}x", fill="#546e7a", font=small)

    y1 = chart_bottom - (math.log10(1) - min_log) / (max_log - min_log) * (chart_bottom - chart_top)

    d.line((chart_left, y1, chart_right, y1), fill="#00897b", width=4)

    d.text((chart_right - 210, y1 - 28), "SCAPE-ZK = 1.0", fill="#00897b", font=small)

    group_w = (chart_right - chart_left) / len(axes)

    bar_w = 70

    for gi, (label, unit, scape, vals) in enumerate(axes):

        gx = chart_left + group_w * gi + group_w / 2

        d.text((gx - 150, chart_top - 55), f"SCAPE-ZK: {scape:,.0f} {unit}", fill="#00897b", font=small)

        draw_center(d, (gx, chart_bottom + 45), label, "#263238", body)

        for si, scheme in enumerate(schemes):

            ratio = vals[scheme] / scape

            y = chart_bottom - (math.log10(max(ratio, 0.02)) - min_log) / (max_log - min_log) * (chart_bottom - chart_top)

            x = gx + (si - 1) * (bar_w + 18)

            d.rectangle((x - bar_w / 2, y, x + bar_w / 2, chart_bottom), fill=colors_map[scheme], outline="#263238")

            draw_center(d, (x, y - 28), f"{ratio:.2f}x", "#263238", small)

    lx = 1030

    for i, scheme in enumerate(schemes):

        y = 760 + i * 36

        d.rectangle((lx, y, lx + 24, y + 24), fill=colors_map[scheme], outline="#263238")

        d.text((lx + 36, y), scheme, fill="#263238", font=body)

    out = ROOT / "fig5_headline_normalized.png"

    img.save(out)

    save_pdf_from_png(out, ROOT / "fig5_headline_normalized.pdf")

def fig7():

    session_setup = 44.945 + 501.051 + 101.507

    request_total = 115.654 + 4.583 + 1.628 + 99.693

    ks = list(range(1, 101))

    vals = [(session_setup + k * request_total) / k for k in ks]

    img = Image.new("RGB", (1500, 900), "white")

    d = ImageDraw.Draw(img)

    title = font(34, True)

    body = font(22)

    small = font(18)

    d.text((70, 35), "Two-tier CPCP amortization", fill="#263238", font=title)

    d.text((70, 80), "SCAPE-ZK pays session setup once; request cost is amortized over k requests.", fill="#37474f", font=body)

    left, top, right, bottom = 120, 155, 1390, 720

    d.line((left, bottom, right, bottom), fill="#263238", width=2)

    d.line((left, top, left, bottom), fill="#263238", width=2)

    y_min, y_max = 50, 3000

    log_min, log_max = math.log10(y_min), math.log10(y_max)

    def xmap(k): return left + (k - 1) / 99 * (right - left)

    def ymap(v): return bottom - (math.log10(v) - log_min) / (log_max - log_min) * (bottom - top)

    for tick in [50, 100, 200, 500, 1000, 2000, 3000]:

        y = ymap(tick)

        d.line((left - 8, y, right, y), fill="#eceff1", width=1)

        d.text((45, y - 10), f"{tick}", fill="#546e7a", font=small)

    lines = [

        ("XAuth", 1329, "#455a64", -44),

        ("SSL-XIoMT", 1317.73, "#78909c", 8),

        ("Scheme [30]", 54.49, "#b0bec5", -24),

        ("SCAPE-ZK floor", request_total, "#00897b", -24),

    ]

    for name, val, col, yoff in lines:

        y = ymap(val)

        d.line((left, y, right, y), fill=col, width=3)

        d.rectangle((right - 300, y + yoff - 4, right - 18, y + yoff + 24), fill="white")

        d.text((right - 292, y + yoff), f"{name}: {val:.1f} ms", fill=col, font=small)

    pts = [(xmap(k), ymap(v)) for k, v in zip(ks, vals)]

    d.line(pts, fill="#00897b", width=5)

    d.text((left, bottom + 35), "k = 1", fill="#263238", font=small)

    d.text((right - 70, bottom + 35), "k = 100", fill="#263238", font=small)

    d.text((70, 760), f"Session setup = {session_setup:.1f} ms; request+PRE+IPFS floor = {request_total:.1f} ms", fill="#263238", font=body)

    out = ROOT / "fig7_cpcp_amortization.png"

    img.save(out)

    save_pdf_from_png(out, ROOT / "fig7_cpcp_amortization.pdf")

if __name__ == "__main__":

    fig5()

    fig7()

    print("rendered fig5_headline_normalized and fig7_cpcp_amortization")
