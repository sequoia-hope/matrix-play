#!/usr/bin/env python3
"""reserve_power.py VARIANT_DIR: lay parallel vias on the power paths before routing, locked.
VSYS at U5 OUT (pins 10, 11): up to 3 vias to the In5 plane, stubs 0.3 mm on B.Cu.
VBAT at U5 BAT (pins 2, 3) and at BT1: up to 3 vias, stubs 0.3 mm, joined to each other on B.Cu and on In4 and In6 by 0.3 mm links so the router's trunk shares them whichever of those it takes."""
import math, sys
from pathlib import Path
import pcbnew
D = Path(sys.argv[1]); PCB = D/"round-pendant.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM; um = pcbnew.ToMM; OX = OY = 100.0
lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}; B = lid["B.Cu"]; F = lid["F.Cu"]
fps = {f.GetReference(): f for f in b.GetFootprints()}
leds = []
for f in b.GetFootprints():
    if f.GetReference()[0] == "D":
        a = math.radians(-f.GetOrientationDegrees())
        for p in f.Pads():
            c = p.GetPosition(); leds.append((um(c.x)-OX, um(c.y)-OY, math.cos(a), math.sin(a), p.GetNetname()))
pads = [(um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY, p.GetNetname()) for f in b.GetFootprints() if f.GetReference()[0] != "D" for p in f.Pads() for q in [p.GetBoundingBox()]]
vias = [(um(t.GetPosition().x)-OX, um(t.GetPosition().y)-OY, t.GetNetname()) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
stubs = [(um(t.GetStart().x)-OX, um(t.GetStart().y)-OY, um(t.GetEnd().x)-OX, um(t.GetEnd().y)-OY, t.GetNetname(), t.GetLayerName(), um(t.GetWidth())) for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
def sd(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay; n = vx*vx+vy*vy; t = 0 if n == 0 else max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/n)); return math.hypot(px-ax-t*vx, py-ay-t*vy)
def boxd(x, y, a, e, g, h): return math.hypot(max(a-x, 0, x-g), max(e-y, 0, y-h))
def pd(x, y, L):
    du = abs(L[2]*(x-L[0])+L[3]*(y-L[1]))-.225; dv = abs(-L[3]*(x-L[0])+L[2]*(y-L[1]))-.225
    return math.hypot(max(du, 0), max(dv, 0))
R = .275
def site(x, y, net):
    for L in leds:
        if abs(L[0]-x) < 1.2 and abs(L[1]-y) < 1.2 and L[4] != net and pd(x, y, L) < R: return False
    if any(n != net and boxd(x, y, a, e, g, h) < R for a, e, g, h, n in pads): return False
    if any(math.hypot(x-a, y-e) < (.41 if n != net else .36) for a, e, n in vias): return False
    return not any(n != net and sd(x, y, a, e, g, h) < .15+.09+w/2 and (lay in ("F.Cu", "B.Cu")) for a, e, g, h, n, lay, w in stubs)
def bpath(x0, y0, x, y, net, w=.3):
    k = max(2, int(math.hypot(x-x0, y-y0)/.03))
    for i in range(k+1):
        px, py = x0+(x-x0)*i/k, y0+(y-y0)*i/k
        if any(n != net and boxd(px, py, a, e, g, h) < .09+w/2 for a, e, g, h, n in pads): return False
        if any(n != net and math.hypot(px-a, py-e) < max(.15+.09, .075+.2)+w/2 for a, e, n in vias): return False
    return True
def track(x0, y0, x, y, net, lay, w=.3):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(OX+x0), mm(OY+y0))); t.SetEnd(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); t.SetWidth(mm(w)); t.SetLayer(lay); t.SetNetCode(b.FindNet(net).GetNetCode()); t.SetLocked(True); b.Add(t)
    stubs.append((x0, y0, x, y, net, b.GetLayerName(lay), w))
def reserve(net, srcs, want, reach, link):
    placed = []; cands = []
    for x0, y0 in srcs:
        for i in range(-60, 61):
            for j in range(-60, 61):
                x, y = x0+i*.04, y0+j*.04; d = math.hypot(i*.04, j*.04)
                if .1 < d <= reach: cands.append((d, x, y, x0, y0))
    cands.sort()
    for d, x, y, x0, y0 in cands:
        if len(placed) >= want: break
        if any(math.hypot(x-p[0], y-p[1]) < .42 for p in placed) or not site(x, y, net) or not bpath(x0, y0, x, y, net): continue
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); v.SetWidth(mm(.3)); v.SetDrill(mm(.15)); v.SetLayerPair(F, B); v.SetNetCode(b.FindNet(net).GetNetCode()); v.SetLocked(True); b.Add(v)
        track(x0, y0, x, y, net, B); vias.append((x, y, net)); placed.append((x, y))
        print(f"  {net} via ({x:.2f}, {y:.2f}), stub {d:.2f} from ({x0:.2f}, {y0:.2f})")
    if link:
        for lay in ("In4.Cu", "In6.Cu"):
            for p, q in zip(placed, placed[1:]): track(p[0], p[1], q[0], q[1], net, lid[lay])
    print(net, "placed", len(placed), "of", want)
    return placed
pos = lambda r, n: next((um(p.GetPosition().x)-OX, um(p.GetPosition().y)-OY) for p in fps[r].Pads() if p.GetNumber() == n)
reserve("VSYS", [pos("U5", "11"), pos("U5", "10")], 3, 2.4, False)
reserve("VBAT", [pos("U5", "3"), pos("U5", "2")], 3, 2.4, True)
reserve("VBAT", [pos("BT1", "1")], 3, 2.4, True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b)
