#!/usr/bin/env python3
"""floorplan_svg.py -- Generate visual 4-panel SVG comparison of the parallelogram variant family."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sunflower"))
from config import CELL_CENTER, CELL_H, CELL_W, HALF_EDGE, HALF_W, SKEW, VARIANTS, build_led_cells  # noqa: E402


def poly_pts(dx: float, dy: float, scale: float) -> str:
    verts = [
        (-HALF_W, -HALF_EDGE + SKEW * (-HALF_W)),
        (HALF_W, -HALF_EDGE + SKEW * HALF_W),
        (HALF_W, HALF_EDGE + SKEW * HALF_W),
        (-HALF_W, HALF_EDGE + SKEW * (-HALF_W)),
    ]
    return " ".join(f"{dx + x * scale:.2f},{dy + y * scale:.2f}" for x, y in verts)


def main():
    out_dir = ROOT / "design/study/parallelogram"
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "floorplan.svg"

    scale = 6.0  # 1 mm = 6 px -> 25x70 mm = 150x420 px per panel
    pw = 205
    ph = 500
    names = ["p1-66", "p2-132", "p3-162", "p3-198", "p4-264"]
    W = pw * len(names) + 40
    H = ph + 60

    drv_colors = {1: "#38bdf8", 2: "#fbbf24", 3: "#34d399", 4: "#f472b6"}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="system-ui, -apple-system, sans-serif">',
        f'  <rect width="{W}" height="{H}" fill="#0f172a"/>',
        f'  <text x="{W/2:.1f}" y="28" fill="#f8fafc" font-size="16" font-weight="700" text-anchor="middle">'
        "Parallelogram 4-Layer Low-Cost Variant Family (25.0 × 70.0 mm, 17.75° Skew, 20×35 mm Prismatic LiPo)"
        "</text>",
    ]

    for idx, vname in enumerate(names):
        spec = VARIANTS[vname]
        cx = 20 + idx * pw + pw / 2
        cy = 50 + ph / 2
        cells = build_led_cells(spec)

        led_short = "XL-1615" if spec.led_type == "XL-1615RGBC" else "XL-1010"
        lines.append(f'  <g id="panel-{vname}">')
        lines.append(
            f'    <text x="{cx:.1f}" y="54" fill="#e2e8f0" font-size="13" font-weight="600" text-anchor="middle">'
            f"{vname} ({spec.n_leds}× {led_short})</text>"
        )
        lines.append(
            f'    <text x="{cx:.1f}" y="70" fill="#94a3b8" font-size="10.5" text-anchor="middle">'
            f"{spec.cols}×{spec.rows} · {spec.px:.2f}×{spec.py:.2f} mm · {len(spec.drivers)}× AW20198</text>"
        )

        # Board outline
        lines.append(
            f'    <polygon points="{poly_pts(cx, cy, scale)}" fill="#112e1f" stroke="#22c55e" stroke-width="1.6" stroke-linejoin="round"/>'
        )

        # 20x35 mm Prismatic LiPo pouch cell dashed box on B.Cu
        bx = cx + (CELL_CENTER[0] - CELL_W / 2) * scale
        by = cy + (CELL_CENTER[1] - CELL_H / 2) * scale
        lines.append(
            f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{CELL_W*scale:.1f}" height="{CELL_H*scale:.1f}" '
            'fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,3" rx="3"/>'
        )

        # RP2350A U3 on B.Cu (+0.02, +5.50, 7x7 mm)
        ux, uy = cx + (0.02 - 3.5) * scale, cy + (5.50 - 3.5) * scale
        lines.append(
            f'    <rect x="{ux:.1f}" y="{uy:.1f}" width="{7.0*scale:.1f}" height="{7.0*scale:.1f}" '
            'fill="#1e293b" fill-opacity="0.78" stroke="#94a3b8" stroke-width="1.0"/>'
        )
        lines.append(
            f'    <text x="{cx + 0.02*scale:.1f}" y="{cy + 5.50*scale + 3:.1f}" fill="#cbd5e1" font-size="8.5" text-anchor="middle">RP2350</text>'
        )

        # AW20198QNR QFN-40 5x5 mm drivers + 3.4x3.4 mm solid EP on B.Cu
        for drv in spec.drivers:
            dx0, dy0, _ = drv.bcu_pos
            if dy0 > 10.0 and dx0 < 0:
                dx0, dy0 = (-7.40 if spec.cols == 6 else -8.00), 19.25
            col = drv_colors[drv.idx]
            rx, ry = cx + (dx0 - 2.5) * scale, cy + (dy0 - 2.5) * scale
            ex, ey = cx + (dx0 - 1.7) * scale, cy + (dy0 - 1.7) * scale
            lines.append(
                f'    <rect x="{rx:.1f}" y="{ry:.1f}" width="{5.0*scale:.1f}" height="{5.0*scale:.1f}" '
                f'fill="#0f172a" fill-opacity="0.82" stroke="{col}" stroke-width="1.2"/>'
            )
            lines.append(
                f'    <rect x="{ex:.1f}" y="{ey:.1f}" width="{3.4*scale:.1f}" height="{3.4*scale:.1f}" '
                f'fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="0.7"/>'
            )
            lines.append(
                f'    <text x="{cx + dx0*scale:.1f}" y="{cy + dy0*scale + 3:.1f}" fill="{col}" font-size="7.5" font-weight="600" text-anchor="middle">{drv.uref}</text>'
            )

        # Q2 Top-bezel light sensor (0.0, -29.9)
        qx, qy = cx, cy - 29.90 * scale
        lines.append(f'    <circle cx="{qx:.1f}" cy="{qy:.1f}" r="3.5" fill="#fde047" stroke="#ca8a04" stroke-width="0.8"/>')

        # J1 USB pads & BT1 battery pads on South end-zone
        lines.append(
            f'    <text x="{cx:.1f}" y="{cy + 29.5*scale:.1f}" fill="#94a3b8" font-size="7.5" text-anchor="middle">J1 USB</text>'
        )
        lines.append(
            f'    <text x="{cx + 8.6*scale:.1f}" y="{cy + 30.2*scale:.1f}" fill="#fca5a5" font-size="7.5" text-anchor="middle">BT1</text>'
        )

        # F.Cu LEDs colored by driving AW20198QNR tile (true 1.6x1.5 mm XL-1615 vs 1.0x1.0 mm XL-1010 scale!)
        lw_px = (1.60 if spec.led_type == "XL-1615RGBC" else 1.00) * scale
        lh_px = (1.50 if spec.led_type == "XL-1615RGBC" else 1.00) * scale
        for c in cells:
            lx = cx + c["x_mm"] * scale
            ly = cy + c["y_mm"] * scale
            col = drv_colors[c["drv_idx"]]
            lines.append(
                f'    <rect x="{lx - lw_px/2:.2f}" y="{ly - lh_px/2:.2f}" width="{lw_px:.2f}" height="{lh_px:.2f}" fill="{col}" fill-opacity="0.88" rx="0.9"/>'
            )

        lines.append("  </g>")

    lines.append(
        f'  <text x="{W/2:.1f}" y="{H - 12}" fill="#94a3b8" font-size="10.5" text-anchor="middle">'
        "Colors show contiguous rectangular LED tiles per AW20198QNR (U1=cyan, U2=amber, U10=emerald, U11=pink) · Yellow dot = top-bezel Q2 light sensor · Dashed = 20×35 mm LiPo"
        "</text>"
    )
    lines.append("</svg>")
    svg_path.write_text("\n".join(lines) + "\n")
    print(f"wrote {svg_path}")


if __name__ == "__main__":
    main()
