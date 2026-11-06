#!/usr/bin/env python3
"""render_picoem_strip.py -- Render a publication-grade visual contact sheet of the
actual 132-LED frames streamed over DMA -> PIO0 -> I2C into U1/U2 AW20198QNR during our picoem run."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RUN_JSON = HERE / "results/picoem_run.json"
OUT_PNG = HERE / "report/img/picoem_frames.png"


def board_outline_xy():
    """Exact 25 x 70 mm 17.75-deg skewed parallelogram outline in KiCad (x, y) mm."""
    # Corners: (-12.5, -35.0+dy), (+12.5, -35.0-dy) -- wait: LEDs follow y = y0 + 0.3108 * x!
    # Top edge follows y = -33.2 + 0.3108 * x, bottom edge follows y = +33.2 + 0.3108 * x!
    s = 1.15 / 3.70  # tan(17.27 deg) = 0.31081
    xs = [-12.5, 12.5, 12.5, -12.5, -12.5]
    ys = [-33.4 + s * (-12.5), -33.4 + s * 12.5, 33.4 + s * 12.5, 33.4 + s * (-12.5), -33.4 + s * (-12.5)]
    return xs, ys


def main():
    data = json.loads(RUN_JSON.read_text())
    geom = data["led_geometry"]
    frames = data["frames"]

    plt.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#090d13",
        "axes.edgecolor": "#30363d",
        "axes.labelcolor": "#e6edf3",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "text.color": "#e6edf3",
        "font.size": 9,
    })

    # Pick 8 representative frames (2 per mode: [0, 2, 4, 7, 8, 11, 12, 15])
    pick_indices = [0, 2, 4, 7, 8, 11, 12, 15]
    fig, axes = plt.subplots(1, 8, figsize=(16.5, 5.4), dpi=150)

    bx, by = board_outline_xy()
    xs = np.array([g["x_mm"] for g in geom])
    ys = np.array([g["y_mm"] for g in geom])

    for ax, idx in zip(axes, pick_indices):
        fr = frames[idx]
        rgb = np.array(fr["leds_rgb"], dtype=np.float32) / 255.0
        # Slight perceptual lift for unlit dark background visibility while preserving color saturation
        disp_rgb = np.clip(0.06 + 0.94 * (rgb ** 0.82), 0.0, 1.0)

        poly = patches.Polygon(
            list(zip(bx, by)),
            closed=True,
            facecolor="#111822",
            edgecolor="#3b4654",
            linewidth=1.4,
            zorder=1,
        )
        ax.add_patch(poly)

        # Soft LED glow halo + crisp 1.6x1.5 mm emitter core
        ax.scatter(xs, ys, s=68, c=disp_rgb, alpha=0.28, edgecolors="none", zorder=2)
        ax.scatter(xs, ys, s=22, c=disp_rgb, alpha=1.0, edgecolors="#05070a", linewidths=0.25, marker="s", zorder=3)

        ax.set_xlim(-15.0, 15.0)
        ax.set_ylim(38.5, -38.5)  # KiCad South (+Y) downward, North (-Y) upward!
        ax.set_aspect("equal")
        ax.set_xticks([-10, 0, 10])
        if idx != pick_indices[0]:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("Board Y (mm, North = -Y)")

        mode_short = ["M0 Shear", "M1 Gravity", "M2 Rhombus", "M3 Gauge"][fr["mode"]]
        ax.set_title(
            f"F{fr['frame_index']:02d}: {mode_short}\n{fr['vbat_mv']/1000:.2f}V | GCC={fr['gcc_u1']}\n{fr['sim_time_ms']:.1f} ms",
            fontsize=8.2,
            pad=5,
        )

    fig.suptitle(
        f"picoem Dual-Core RP2350A Co-Simulation — Actual 132-LED AW20198QNR Frames Streamed via DMA Ch0 -> PIO0 SM0 (1.04 MHz I2C)",
        fontsize=11,
        y=0.98,
        color="#f0f6fc",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)
    print(f"[render] Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
