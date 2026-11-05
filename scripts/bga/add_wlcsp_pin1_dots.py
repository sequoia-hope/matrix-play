#!/usr/bin/env python3
"""add_wlcsp_pin1_dots.py BOARD.kicad_pcb [OUT.kicad_pcb]

Adds a 0.26 mm filled B.SilkS pin-1 dot beside ball A1 on each WLCSP-36 driver
(U1, U2, U10, U11, U12), placed outside all B.Mask openings (>=0.165 mm) and
component bodies so `back_silk.py` preserves them and routes text around them.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import pcbnew
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


def poly_from_ps(ps: "pcbnew.SHAPE_POLY_SET") -> Polygon:
    polys = []
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k)
        pts = [(pcbnew.ToMM(o.CPoint(i).x), pcbnew.ToMM(o.CPoint(i).y)) for i in range(o.PointCount())]
        if len(pts) >= 3:
            p = Polygon(pts)
            polys.append(p if p.is_valid else p.buffer(0))
    return unary_union(polys) if polys else Polygon()


def main():
    pcb_in = Path(sys.argv[1])
    pcb_out = Path(sys.argv[2]) if len(sys.argv) > 2 else pcb_in
    pro_path = pcb_out.with_suffix(".kicad_pro")
    pro_bytes = pro_path.read_bytes() if pro_path.exists() else None

    b = pcbnew.LoadBoard(str(pcb_in))
    um = pcbnew.ToMM
    mm = pcbnew.FromMM

    mask_polys = []
    hole_polys = []
    body_polys = []
    via_rings = []

    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Mask) or p.IsOnLayer(pcbnew.B_Cu):
                ps = p.GetEffectivePolygon(pcbnew.B_Mask if p.IsOnLayer(pcbnew.B_Mask) else pcbnew.B_Cu)
                gp = poly_from_ps(ps)
                if not gp.is_empty:
                    mask_polys.append(gp)
            if p.GetDrillSizeX() > 0:
                c = p.GetPosition()
                hole_polys.append(Point(um(c.x), um(c.y)).buffer(um(p.GetDrillSizeX()) / 2.0 + 0.20, 16))
        if fp.IsFlipped():
            fab_pts = []
            for g in fp.GraphicalItems():
                if g.GetLayer() == pcbnew.B_Fab and g.GetClass() != "PCB_TEXT":
                    bb = g.GetBoundingBox()
                    fab_pts.extend([
                        (um(bb.GetLeft()), um(bb.GetTop())),
                        (um(bb.GetRight()), um(bb.GetBottom())),
                    ])
            if fab_pts:
                xs = [x for x, _ in fab_pts]
                ys = [y for _, y in fab_pts]
                body_polys.append(Polygon([(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]).buffer(0.02))

    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            c = t.GetPosition()
            r = um(t.GetWidth(pcbnew.B_Cu)) / 2.0
            if not t.IsTented(pcbnew.B_Mask):
                mask_polys.append(Point(um(c.x), um(c.y)).buffer(r, 16))
            else:
                via_rings.append(Point(um(c.x), um(c.y)).buffer(r + 0.02, 16))

    mask_u = unary_union(mask_polys) if mask_polys else Polygon()
    hole_u = unary_union(hole_polys) if hole_polys else Polygon()
    body_u = unary_union(body_polys) if body_polys else Polygon()

    fps = {f.GetReference(): f for f in b.GetFootprints()}
    keep_alive = []
    dot_r = 0.13
    for ref in ("U1", "U2", "U10", "U11", "U12"):
        fp = fps[ref]
        # Remove any prior B.SilkS circles on this WLCSP footprint so script is idempotent
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() == pcbnew.B_SilkS and g.GetClass() != "PCB_FIELD":
                keep_alive.append(g)
                fp.RemoveNative(g)

        pads = {p.GetNumber(): p for p in fp.Pads()}
        p_a1 = pads["A1"]
        a1x, a1y = um(p_a1.GetPosition().x), um(p_a1.GetPosition().y)
        fpx, fpy = um(fp.GetPosition().x), um(fp.GetPosition().y)
        other_pts = [(um(p.GetPosition().x), um(p.GetPosition().y)) for k, p in pads.items() if k != "A1"]

        out_ang = math.atan2(a1y - fpy, a1x - fpx)
        best = None
        for r_dist in np.linspace(0.32, 1.15, 42):
            for d_ang in np.linspace(-math.pi * 0.75, math.pi * 0.75, 61):
                ang = out_ang + float(d_ang)
                dx = round(a1x + float(r_dist) * math.cos(ang), 3)
                dy = round(a1y + float(r_dist) * math.sin(ang), 3)
                if math.hypot(dx - 100.0, dy - 100.0) > 18.60:
                    continue
                d1 = math.hypot(dx - a1x, dy - a1y)
                min_other = min(math.hypot(dx - ox, dy - oy) for ox, oy in other_pts)
                if d1 + 0.12 >= min_other:
                    continue
                dp = Point(dx, dy).buffer(dot_r, 24)
                if dp.distance(mask_u) < 0.165:
                    continue
                if dp.intersects(hole_u) or dp.intersects(body_u):
                    continue
                nv = sum(1 for vr in via_rings if vr.intersects(dp))
                score = nv * 6.0 + d1 + 0.4 * abs(float(d_ang))
                if best is None or score < best[0]:
                    best = (score, dx, dy, nv, round(d1, 3))

        if best is None:
            raise RuntimeError(f"Could not place pin-1 dot for {ref}")
        _, dx, dy, nv, d1 = best
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetLayer(pcbnew.B_SilkS)
        s.SetFilled(True)
        s.SetWidth(mm(0.13))
        s.SetCenter(pcbnew.VECTOR2I(mm(dx), mm(dy)))
        s.SetEnd(pcbnew.VECTOR2I(mm(dx + 0.065), mm(dy)))
        fp.Add(s)
        print(f"  {ref}: B.SilkS A1 dot at ({dx:.3f}, {dy:.3f}), d_A1={d1:.3f} mm, tented_vias={nv}")

    pcbnew.SaveBoard(str(pcb_out), b)
    if pro_bytes is not None:
        pro_path.write_bytes(pro_bytes)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
