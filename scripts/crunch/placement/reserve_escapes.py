#!/usr/bin/env python3
"""reserve_escapes.py VARIANT_DIR X0 Y0 X1 Y1: for LED cathode pads in this box that can't take a via in the pad (a foreign back-side pad, or the regulator keep-outs above them), lay a locked F.Cu stub to the nearest legal via site, before routing. Same stub width as the anode stubs."""
import math, sys
from pathlib import Path
import pcbnew
D = Path(sys.argv[1]); PCB = D/"round-pendant.kicad_pcb"; X0, Y0, X1, Y1 = map(float, sys.argv[2:6])
b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM; um = pcbnew.ToMM; OX = OY = 100.0
lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}; B = lid["B.Cu"]; F = lid["F.Cu"]
leds = []; targets = []
for f in b.GetFootprints():
    if f.GetReference()[0] != "D": continue
    a = math.radians(-f.GetOrientationDegrees())
    for p in f.Pads():
        c = p.GetPosition(); x, y = um(c.x)-OX, um(c.y)-OY
        leds.append((x, y, math.cos(a), math.sin(a), p.GetNetname(), f.GetReference(), p.GetNumber()))
        if X0 < x < X1 and Y0 < y < Y1 and (p.GetNumber() != "3" or f.GetReference() == "D235"): targets.append((x, y, p, f.GetReference()))
pads = [(um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY, p.GetNetname()) for f in b.GetFootprints() if f.GetReference()[0] != "D" for p in f.Pads() for q in [p.GetBoundingBox()]]
vias = [(um(t.GetPosition().x)-OX, um(t.GetPosition().y)-OY, t.GetNetname()) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
stubs = [(um(t.GetStart().x)-OX, um(t.GetStart().y)-OY, um(t.GetEnd().x)-OX, um(t.GetEnd().y)-OY, t.GetNetname()) for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
# Rule boxes: foreign vias not allowed. Zones on B.Cu of other nets also stop a via.
keep = []
for z in b.Zones():
    if z.GetZoneName() in ("reg corner", "L1 window") or z.GetZoneName().startswith(("vendor", "DVDD", "FB")):
        q = z.GetBoundingBox(); keep.append((um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY))
def sd(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay; n = vx*vx+vy*vy; t = 0 if n == 0 else max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/n)); return math.hypot(px-ax-t*vx, py-ay-t*vy)
def boxd(x, y, a, e, g, h): return math.hypot(max(a-x, 0, x-g), max(e-y, 0, y-h))
def pd(x, y, L): 
    du = abs(L[2]*(x-L[0])+L[3]*(y-L[1]))-.225; dv = abs(-L[3]*(x-L[0])+L[2]*(y-L[1]))-.225
    return math.hypot(max(du, 0), max(dv, 0))
R = .275
def site(x, y, net, own=None):
    if x*x+y*y > 18.4**2: return False
    if any(boxd(x, y, *k) < R for k in keep): return False
    if any(n != net and boxd(x, y, a, e, g, h) < R for a, e, g, h, n in pads): return False
    if any(math.hypot(x-a, y-e) < (.41 if n != net else .36) for a, e, n in vias): return False
    if any(n != net and sd(x, y, a, e, g, h) < .125+.09+.06 for a, e, g, h, n in stubs): return False
    for L in leds:
        if L[4] != net and abs(L[0]-x) < 1.2 and abs(L[1]-y) < 1.2 and pd(x, y, L) < R: return False
    return True
def path(x0, y0, x, y, net):
    n = max(2, int(math.hypot(x-x0, y-y0)/.03))
    for i in range(n+1):
        px, py = x0+(x-x0)*i/n, y0+(y-y0)*i/n
        for L in leds:
            if L[4] != net and abs(L[0]-px) < 1 and abs(L[1]-py) < 1 and pd(px, py, L) < .06+.09: return False
        if any(k != net and math.hypot(px-a, py-e) < .125+.09+.06 for a, e, k in vias): return False
    return all(n2 == net or min(sd(a, e, x0, y0, x, y), sd(g, h, x0, y0, x, y)) >= .12+.09 for a, e, g, h, n2 in stubs)
rings = [(r, 2*math.pi*k/48) for r in (.3, .35, .4, .45, .5, .55, .6, .65, .7, .75, .8, .9, 1.0, 1.1, 1.2, 1.35, 1.5, 1.7, 1.9) for k in range(48)]
done = inpad = fail = 0; failed = []
for x0, y0, p, ref in sorted(targets, key=lambda t: t[0]+t[1]):
    net = p.GetNetname()
    if any(a == x0 and e == y0 for a, e, _ in vias): continue
    if any(n == net and (abs(a-x0) < .01 and abs(e-y0) < .01 or abs(g-x0) < .01 and abs(h-y0) < .01) for a, e, g, h, n in stubs): continue
    if site(x0, y0, net): inpad += 1; continue
    best = next(((r, x0+r*math.cos(t), y0+r*math.sin(t)) for r, t in rings if site(x0+r*math.cos(t), y0+r*math.sin(t), net) and path(x0, y0, x0+r*math.cos(t), y0+r*math.sin(t), net)), None)
    if not best: fail += 1; failed.append(f"{ref}.{p.GetNumber()}"); continue
    r, x, y = best
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); v.SetWidth(mm(.25)); v.SetDrill(mm(.15)); v.SetLayerPair(F, B); v.SetNetCode(p.GetNetCode()); v.SetLocked(True); b.Add(v)
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(OX+x0), mm(OY+y0))); t.SetEnd(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); t.SetWidth(mm(.12)); t.SetLayer(F); t.SetNetCode(p.GetNetCode()); t.SetLocked(True); b.Add(t)
    vias.append((x, y, net)); stubs.append((x0, y0, x, y, net)); done += 1
    print(f"{ref}.{p.GetNumber()} {net.split('/')[-1]} stub {r:.2f} to ({x:.2f}, {y:.2f})")
print("stubs", done, "in-pad possible", inpad, "failed", fail, failed)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b)
