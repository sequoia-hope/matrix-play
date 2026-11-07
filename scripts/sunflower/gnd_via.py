#!/usr/bin/env python3
"""gnd_via.py IN OUT REF.PAD [REF.PAD ...]: tie each named GND pad to the In1.Cu GND plane with one through via and a short stub on the pad's layer.

Searches spots within --reach mm of the pad, nearest first, and keeps the first one that clears every
foreign pad, track, via and hole on all four layers by the board's clearance (0.10 copper, 0.20 hole to
copper, 0.20 hole to hole) plus --margin. A via hole inside an SMD pad is not allowed. Touches nothing
else. Judge with KiCad DRC afterwards, never with this script.
"""
import argparse
import math

import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("out")
ap.add_argument("pads", nargs="+")
ap.add_argument("--reach", type=float, default=1.2)
ap.add_argument("--step", type=float, default=0.025)
ap.add_argument("--via", type=float, default=0.30)
ap.add_argument("--drill", type=float, default=0.15)
ap.add_argument("--width", type=float, default=0.15)
ap.add_argument("--margin", type=float, default=0.01)
a = ap.parse_args()

b = pcbnew.LoadBoard(a.inp)
um, mm = pcbnew.ToMM, pcbnew.FromMM
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
CLR, HOLE_CU, HOLE_HOLE = 0.10 + a.margin, 0.20 + a.margin, 0.20 + a.margin
gnd = b.GetNetcodeFromNetname("GND")


def poly(shape):
    out = []
    for k in range(shape.OutlineCount()):
        o = shape.Outline(k)
        out.append(Polygon([(um(o.CPoint(j).x), um(o.CPoint(j).y)) for j in range(o.PointCount())]))
    return out


foreign = {L: [] for L in CU}   # copper of other nets, per layer
holes = []                      # every drilled hole (any net)
smd = []                        # SMD pads (no via hole inside)
for f in b.GetFootprints():
    for p in f.Pads():
        for L in CU:
            if p.IsOnLayer(L) and p.GetNetCode() != gnd:
                foreign[L] += poly(p.GetEffectivePolygon(L))
        if p.GetDrillSize().x > 0:
            c = p.GetPosition()
            holes.append(Point(um(c.x), um(c.y)).buffer(um(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2))
        elif p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            L = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
            smd += poly(p.GetEffectivePolygon(L))
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        c = t.GetPosition()
        pt = Point(um(c.x), um(c.y))
        holes.append(pt.buffer(um(t.GetDrill()) / 2))
        if t.GetNetCode() != gnd:
            for L in CU:
                foreign[L].append(pt.buffer(um(t.GetWidth(L)) / 2))
    elif t.GetNetCode() != gnd:
        s, e = t.GetStart(), t.GetEnd()
        foreign[t.GetLayer()].append(LineString([(um(s.x), um(s.y)), (um(e.x), um(e.y))]).buffer(um(t.GetWidth()) / 2))
# zones of other nets on outer layers (filled copper)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetCode() == gnd:
        continue
    for L in CU:
        if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L):
            foreign[L] += poly(z.GetFilledPolysList(L))

trees = {L: STRtree(foreign[L]) for L in CU}
hole_tree, smd_tree = STRtree(holes), STRtree(smd)


def clear(geom, L, d):
    return all(foreign[L][i].distance(geom) >= d for i in trees[L].query(geom.buffer(d)))


fps = {f.GetReference(): f for f in b.GetFootprints()}
added = []
for spec in a.pads:
    ref, num = spec.split(".")
    pad = next(p for p in fps[ref].Pads() if p.GetNumber() == num)
    assert pad.GetNetCode() == gnd, f"{spec} is {pad.GetNetname()}, not GND"
    L = pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
    c = pad.GetPosition()
    cx, cy = um(c.x), um(c.y)
    n = int(a.reach / a.step)
    cands = sorted(((i * a.step) ** 2 + (j * a.step) ** 2, cx + i * a.step, cy + j * a.step)
                   for i in range(-n, n + 1) for j in range(-n, n + 1) if (i * a.step) ** 2 + (j * a.step) ** 2 <= a.reach ** 2)
    found = None
    for _, x, y in cands:
        v = Point(x, y)
        ring, hole = v.buffer(a.via / 2), v.buffer(a.drill / 2)
        if any(holes[i].distance(hole) < HOLE_HOLE for i in hole_tree.query(hole.buffer(HOLE_HOLE))):
            continue
        if any(smd[i].distance(hole) < 0.10 for i in smd_tree.query(hole.buffer(0.10))):
            continue
        if not all(clear(ring, Lx, CLR) and clear(hole, Lx, HOLE_CU) for Lx in CU if Lx != pcbnew.In1_Cu):
            continue
        stub = LineString([(cx, cy), (x, y)]).buffer(a.width / 2)
        if not clear(stub, L, CLR):
            continue
        found = (x, y)
        break
    if not found:
        print(f"{spec}: no spot within {a.reach} mm")
        continue
    x, y = found
    via = pcbnew.PCB_VIA(b)
    via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    via.SetWidth(mm(a.via))
    via.SetDrill(mm(a.drill))
    via.SetNetCode(gnd)
    b.Add(via)
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(c)
    tr.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
    tr.SetWidth(mm(a.width))
    tr.SetLayer(L)
    tr.SetNetCode(gnd)
    b.Add(tr)
    # later pads must see this via and stub
    hp = Point(x, y)
    holes.append(hp.buffer(a.drill / 2))
    hole_tree = STRtree(holes)
    added.append(spec)
    print(f"{spec}: via at ({x:.3f}, {y:.3f}), stub {math.hypot(x - cx, y - cy):.3f} mm on {b.GetLayerName(L)}")
b.Save(a.out)
print("added", len(added))
