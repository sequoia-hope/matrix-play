#!/usr/bin/env python3
"""jst_site.py -- find one B.Cu site for the JST GH battery connector that fits every routed sunflower board.

Hard limits: its courtyard clears every other back-side courtyard; its body stays 0.2 mm inside the disc and its pads
0.35 mm; its mouth (the mounting-tab side, where the plug goes in) points within 35 deg of straight out to the rim.
Score: routed copper the new pads would hit (tracks and vias of other nets within 0.15 mm), summed over the boards,
so the local re-route is as small as possible. Prints the best sites.
"""
import math
import sys
from pathlib import Path

import pcbnew
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sunflower"))
from config import BAT_FP, BAT_LIB_SRC, OX, OY, R_BOARD, VARIANTS  # noqa: E402

um = pcbnew.ToMM
# Parts whose courtyards may be ignored (they would be moved), e.g. SKIP_CRT=TP3 for a what-if search
SKIP_CRT = set(filter(None, __import__("os").environ.get("SKIP_CRT", "").split(",")))
lib, name = BAT_FP.split(":")
LIBDIR = BAT_LIB_SRC


def poly_of(shape_poly_set):
    o = shape_poly_set.Outline(0)
    return Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])


def local_geometry(rot):
    """GH footprint flipped to B.Cu at (0, 0) and turned to `rot`: pads, courtyard, body and mouth direction."""
    b = pcbnew.NewBoard("/tmp/_gh.kicad_pcb")
    fp = pcbnew.FootprintLoad(LIBDIR, name)
    b.Add(fp)
    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    pads = [poly_of(p.GetEffectivePolygon(pcbnew.B_Cu)) for p in fp.Pads()]
    sig = [p for p in fp.Pads() if p.GetNumber() in ("1", "2")]
    mp = [p for p in fp.Pads() if p.GetNumber() == "MP"]
    cs = sum(um(p.GetPosition().x) for p in sig) / 2, sum(um(p.GetPosition().y) for p in sig) / 2
    cm = sum(um(p.GetPosition().x) for p in mp) / 2, sum(um(p.GetPosition().y) for p in mp) / 2
    mouth = math.atan2(cm[1] - cs[1], cm[0] - cs[0])
    crt = poly_of(fp.GetCourtyard(pcbnew.B_CrtYd))
    # Body: the fab outline's box (-2.92..2.92 across, -1.65..2.5 deep) turned with the part
    fab = [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.B_Fab and isinstance(g, pcbnew.PCB_SHAPE)
           and g.GetShape() == pcbnew.SHAPE_T_SEGMENT]
    body = unary_union([Point(um(v.x), um(v.y)) for g in fab for v in (g.GetStart(), g.GetEnd())]).convex_hull
    return pads, crt, body, mouth


def board_obstacles(pcb):
    b = pcbnew.LoadBoard(str(pcb))
    crts, copper = [], []
    for f in b.GetFootprints():
        if f.GetReference() == "BT1" or f.GetLayer() != pcbnew.B_Cu:
            continue
        cy = f.GetCourtyard(pcbnew.B_CrtYd)
        if cy.OutlineCount() and f.GetReference() not in SKIP_CRT:
            crts.append(affinity.translate(poly_of(cy), -OX, -OY))
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.B_Cu):
                copper.append(affinity.translate(poly_of(p.GetEffectivePolygon(pcbnew.B_Cu)), -OX, -OY))
    for t in b.GetTracks():
        if t.GetNetname() in ("VBAT", "/Power/BAT_N"):
            continue  # these get re-routed to the new pads anyway
        if isinstance(t, pcbnew.PCB_VIA):
            copper.append(Point(um(t.GetPosition().x) - OX, um(t.GetPosition().y) - OY).buffer(um(t.GetWidth(pcbnew.F_Cu)) / 2))
        elif t.GetLayer() == pcbnew.B_Cu:
            copper.append(LineString([(um(t.GetStart().x) - OX, um(t.GetStart().y) - OY),
                                      (um(t.GetEnd().x) - OX, um(t.GetEnd().y) - OY)]).buffer(um(t.GetWidth()) / 2))
    return unary_union(crts), STRtree(copper), copper


def main():
    boards = [VARIANTS[k].hw_dir / "sunflower.kicad_pcb" for k in VARIANTS]
    obs = [board_obstacles(p) for p in boards]
    disc_body = Point(0, 0).buffer(R_BOARD - 0.20, 256)
    disc_pads = Point(0, 0).buffer(R_BOARD - 0.35, 256)
    res = []
    for rot in range(0, 360, 5):
        pads, crt, body, mouth = local_geometry(rot)
        for xi in range(-180, 181, 2):
            for yi in range(-180, 181, 2):
                x, y = xi / 10, yi / 10
                r = math.hypot(x, y)
                if r < 9 or r > 18:
                    continue
                d = (math.degrees(mouth - math.atan2(y, x)) + 180) % 360 - 180
                if abs(d) > float(__import__("os").environ.get("MOUTH_TOL", 35)):
                    continue
                bd = affinity.translate(body, x, y)
                if not disc_body.contains(bd):
                    continue
                pd = [affinity.translate(p, x, y) for p in pads]
                if not all(disc_pads.contains(p) for p in pd):
                    continue
                cr = affinity.translate(crt, x, y)
                if any(cr.intersects(c) and cr.intersection(c).area > 1e-4 for c, _, _ in obs):
                    continue
                hits = 0
                for _, tree, geoms in obs:
                    for p in pd:
                        q = p.buffer(0.15)
                        hits += sum(1 for i in tree.query(q) if geoms[i].intersects(q))
                res.append((hits, abs(d), x, y, rot))
    res.sort()
    for h, d, x, y, rot in [r for r in res if r[1] >= float(__import__("os").environ.get("MOUTH_MIN", 0))][:15]:
        print(f"hits={h:3d} mouth_off={d:4.1f} deg  x={x:6.2f} y={y:6.2f} rot={rot}")
    print(f"{len(res)} legal sites")


if __name__ == "__main__":
    main()
