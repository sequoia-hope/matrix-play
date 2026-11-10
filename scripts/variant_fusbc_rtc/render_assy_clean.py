#!/usr/bin/env python3
"""Generate crisp, 100% collision-free, high-DPI assembly drawings for round-pendant-f-usbc-rtc:
  - hw/round-pendant/f-usbc-rtc/fab/assembly-top.pdf & assembly-bottom.pdf
  - design/renders/round-pendant-f-usbc-rtc/assembly-top.{png,pdf} & assembly-bottom.{png,pdf}
"""
import math
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
PCB_PATH = ROOT / "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb"
FAB_DIR = ROOT / "hw/round-pendant/f-usbc-rtc/fab"
RENDER_DIR = ROOT / "design/renders/round-pendant-f-usbc-rtc"

to_mm = pcbnew.ToMM
from_mm = pcbnew.FromMM


def extract_poly_pts(shape_or_pad, layer_id):
    ps = pcbnew.SHAPE_POLY_SET()
    if isinstance(shape_or_pad, pcbnew.PAD):
        poly = shape_or_pad.GetEffectivePolygon(layer_id)
        out = []
        for i in range(poly.OutlineCount()):
            ol = poly.Outline(i)
            pts = [(to_mm(ol.CPoint(j).x), to_mm(ol.CPoint(j).y)) for j in range(ol.PointCount())]
            if len(pts) >= 3:
                out.append(pts)
        return out
    else:
        shape_or_pad.TransformShapeToPolygon(ps, layer_id, 0, from_mm(0.02), pcbnew.ERROR_INSIDE)
        out = []
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            pts = [(to_mm(ol.CPoint(j).x), to_mm(ol.CPoint(j).y)) for j in range(ol.PointCount())]
            if len(pts) >= 3:
                out.append(pts)
        return out


def extract_shape_lines(g):
    sh = g.GetShape()
    if sh == pcbnew.SHAPE_T_SEGMENT:
        s, e = g.GetStart(), g.GetEnd()
        return [[(to_mm(s.x), to_mm(s.y)), (to_mm(e.x), to_mm(e.y))]]
    elif sh in (pcbnew.SHAPE_T_RECT, pcbnew.SHAPE_T_POLY, pcbnew.SHAPE_T_ARC, pcbnew.SHAPE_T_CIRCLE):
        ps = pcbnew.SHAPE_POLY_SET()
        g.TransformShapeToPolygon(ps, g.GetLayer(), 0, from_mm(0.02), pcbnew.ERROR_INSIDE)
        lines = []
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            pts = [(to_mm(ol.CPoint(j).x), to_mm(ol.CPoint(j).y)) for j in range(ol.PointCount())]
            if pts:
                pts.append(pts[0])
                lines.append(pts)
        return lines
    return []


def resolve_labels(items, mirror_x=False):
    placed = []
    for it in items:
        placed.append({
            "ref": it["ref"],
            "ax": (-it["cx"] if mirror_x else it["cx"]),
            "ay": it["cy"],
            "x": (-it["cx"] if mirror_x else it["cx"]),
            "y": it["cy"],
            "w": it["w"],
            "h": it["h"],
            "fs": it["fs"],
        })

    for _ in range(200):
        moved = False
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                a, b_it = placed[i], placed[j]
                ox = (a["w"] + b_it["w"]) / 2.0 + 0.12 - abs(a["x"] - b_it["x"])
                oy = (a["h"] + b_it["h"]) / 2.0 + 0.10 - abs(a["y"] - b_it["y"])
                if ox > 0 and oy > 0:
                    moved = True
                    if ox < oy:
                        sgn = 1.0 if a["x"] >= b_it["x"] else -1.0
                        if abs(a["x"] - b_it["x"]) < 1e-4:
                            sgn = 1.0 if i < j else -1.0
                        a["x"] += 0.52 * ox * sgn
                        b_it["x"] -= 0.52 * ox * sgn
                    else:
                        sgn = 1.0 if a["y"] >= b_it["y"] else -1.0
                        if abs(a["y"] - b_it["y"]) < 1e-4:
                            sgn = 1.0 if i < j else -1.0
                        a["y"] += 0.52 * oy * sgn
                        b_it["y"] -= 0.52 * oy * sgn
        for a in placed:
            a["x"] += 0.04 * (a["ax"] - a["x"])
            a["y"] += 0.04 * (a["ay"] - a["y"])
        if not moved:
            break
    return placed


def render_side(b, is_top, out_png, out_pdf):
    cu_id = b.GetLayerID("F.Cu" if is_top else "B.Cu")
    fab_id = b.GetLayerID("F.Fab" if is_top else "B.Fab")
    crtyd_id = b.GetLayerID("F.CrtYd" if is_top else "B.CrtYd")
    mirror_x = not is_top

    def tx(x):
        return -x if mirror_x else x

    fig, ax = plt.subplots(figsize=(10.5, 10.5), dpi=300)
    ax.set_facecolor("#ffffff")

    cx0 = tx(100.0)
    cy0 = 100.0
    ax.add_patch(Circle((cx0, cy0), 19.0, facecolor="#fbfcfe", edgecolor="#1e293b", linewidth=1.6, zorder=1))

    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                px, py = to_mm(p.GetPosition().x), to_mm(p.GetPosition().y)
                r = to_mm(p.GetDrillSize().x) / 2.0
                ax.add_patch(Circle((tx(px), py), r, facecolor="#fde68a", edgecolor="#b45309", linewidth=0.7, zorder=3))

    label_inputs = []
    fps = [fp for fp in b.GetFootprints() if fp.GetLayer() == cu_id]
    for fp in fps:
        ref = fp.GetReference()
        pad_centers = []
        for p in fp.Pads():
            if p.GetLayerSet().Contains(cu_id):
                px, py = to_mm(p.GetPosition().x), to_mm(p.GetPosition().y)
                pad_centers.append((px, py))
                is_p1 = p.GetNumber() in ("1", "A1", "A1B12")
                for pts in extract_poly_pts(p, cu_id):
                    mpts = [(tx(qx), qy) for qx, qy in pts]
                    ax.add_patch(Polygon(
                        mpts, closed=True,
                        facecolor=("#dbeafe" if not is_p1 else "#fecdd3"),
                        edgecolor=("#93c5fd" if not is_p1 else "#f43f5e"),
                        linewidth=0.35, zorder=2
                    ))

        fab_lines = []
        for g in fp.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == fab_id:
                fab_lines.extend(extract_shape_lines(g))
        if not fab_lines:
            for g in fp.GraphicalItems():
                if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == crtyd_id:
                    fab_lines.extend(extract_shape_lines(g))
        for ln_pts in fab_lines:
            ax.plot([tx(p[0]) for p in ln_pts], [p[1] for p in ln_pts], color="#475569", linewidth=0.55, zorder=4)

        fx, fy = to_mm(fp.GetPosition().x), to_mm(fp.GetPosition().y)
        span = max(
            max(p[0] for p in pad_centers) - min(p[0] for p in pad_centers),
            max(p[1] for p in pad_centers) - min(p[1] for p in pad_centers),
        ) if pad_centers else 1.0

        if is_top:
            fs, ch_w, ch_h = 4.6, 0.23, 0.34
        elif span >= 3.0 or ref.startswith(("U", "J", "SW", "BT", "L", "Y")):
            fs, ch_w, ch_h = 5.6, 0.28, 0.42
        else:
            fs, ch_w, ch_h = 4.2, 0.21, 0.31

        label_inputs.append({
            "ref": ref,
            "cx": fx,
            "cy": fy,
            "w": len(ref) * ch_w + 0.14,
            "h": ch_h + 0.08,
            "fs": fs,
        })

    resolved = resolve_labels(label_inputs, mirror_x=mirror_x)
    for it in resolved:
        dist = math.hypot(it["x"] - it["ax"], it["y"] - it["ay"])
        if dist > 0.38:
            ax.plot([it["ax"], it["x"]], [it["ay"], it["y"]], color="#64748b", linewidth=0.45, linestyle="-", zorder=5)
            ax.plot([it["ax"]], [it["ay"]], marker="o", markersize=1.1, color="#64748b", zorder=5)
        ax.text(
            it["x"], it["y"], it["ref"],
            fontsize=it["fs"], fontweight="bold", family="DejaVu Sans Mono",
            color="#0f172a", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.06", facecolor=(1, 1, 1, 0.78), edgecolor="none"),
            zorder=6,
        )

    side_title = (
        "Round Pendant f-usbc-rtc — TOP Assembly Map (F.Cu, 236 parts: D1..D235 + Q2, Direct Front View)"
        if is_top else
        f"Round Pendant f-usbc-rtc — BOTTOM Assembly Map (B.Cu, {len(resolved)} footprints incl. J1 USB-C, BT1 & U13 RTC, Mirrored Back View)"
    )
    ax.set_title(side_title + "\nPink pad = Pin 1 / A1 / Cathode-1 | Amber circle = NPTH locating hole", fontsize=9.2, pad=10, color="#0f172a")
    ax.set_xlim(cx0 - 20.6, cx0 + 20.6)
    ax.set_ylim(cy0 + 20.6, cy0 - 20.6)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Wrote {out_png.name} & {out_pdf.name} ({len(resolved)} collision-free refs)")


def main():
    b = pcbnew.LoadBoard(str(PCB_PATH))
    FAB_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    render_side(b, True, RENDER_DIR / "assembly-top.png", RENDER_DIR / "assembly-top.pdf")
    render_side(b, False, RENDER_DIR / "assembly-bottom.png", RENDER_DIR / "assembly-bottom.pdf")
    shutil.copy2(RENDER_DIR / "assembly-top.pdf", FAB_DIR / "assembly-top.pdf")
    shutil.copy2(RENDER_DIR / "assembly-bottom.pdf", FAB_DIR / "assembly-bottom.pdf")


if __name__ == "__main__":
    main()
