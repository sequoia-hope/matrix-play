#!/usr/bin/env python3
"""u3fix2.py VARIANT_DIR: second half of u3fix.py, in a fresh process because a zone fill only keeps pad-joined pieces once the board has been reloaded. Adds a 3V3 plane via to each band piece with none."""
import math, sys
from pathlib import Path
import pcbnew
D = Path(sys.argv[1]); PCB = D/"round-pendant.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM; um = pcbnew.ToMM; OX = OY = 100.0
lid = {b.GetLayerName(l): l for l in range(0, 64) if b.GetLayerName(l).endswith(".Cu")}; B = lid["B.Cu"]
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
leds = []
for f in b.GetFootprints():
    if f.GetReference()[0] == "D":
        a = math.radians(-f.GetOrientationDegrees())
        for p in f.Pads():
            c = p.GetPosition(); leds.append((um(c.x)-OX, um(c.y)-OY, math.cos(a), math.sin(a)))
pads = [(um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY, p.GetNetname()) for f in b.GetFootprints() if f.GetReference()[0] != "D" for p in f.Pads() for q in [p.GetBoundingBox()]]
vias = [(um(t.GetPosition().x)-OX, um(t.GetPosition().y)-OY) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
stubs = [(um(t.GetStart().x)-OX, um(t.GetStart().y)-OY, um(t.GetEnd().x)-OX, um(t.GetEnd().y)-OY) for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
def sd(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay; n = vx*vx+vy*vy; t = 0 if n == 0 else max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/n)); return math.hypot(px-ax-t*vx, py-ay-t*vy)
def free(x, y, net, R=.275, sep=.41):
    for lx_, ly, c, s in leds:
        if abs(lx_-x) < 1.2 and abs(ly-y) < 1.2:
            du = abs(c*(x-lx_)+s*(y-ly))-.225; dv = abs(-s*(x-lx_)+c*(y-ly))-.225
            if math.hypot(max(du, 0), max(dv, 0)) < R: return False
    for a, e, g, h, n in pads:
        if n != net and math.hypot(max(a-x, 0, x-g), max(e-y, 0, y-h)) < R: return False
    if any(math.hypot(x-a, y-e) < sep for a, e in vias): return False
    if any(sd(x, y, *t) < R+.06 for t in stubs): return False
    return True
keepclear = [(um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY) for z in b.Zones() if z.GetZoneName().startswith("DVDD") for q in [z.GetBoundingBox()]]
_free = free
def free(x, y, net, R=.275, sep=.41):
    return _free(x, y, net, R, sep) and all(math.hypot(max(a-x, 0, x-g), max(e-y, 0, y-h)) >= .32 for a, e, g, h in keepclear)
def via(x, y, net, w=.25, d=.15):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); v.SetWidth(mm(w)); v.SetDrill(mm(d)); v.SetLayerPair(lid["F.Cu"], B); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
# Band pieces with no plane via get one, 0.2/0.1 like U3's other band vias.
v3 = b.FindNet("+3V3").GetNetCode(); added = 0
for z in b.Zones():
    if z.GetZoneName() == "RP2350 band":
        ps = z.GetFilledPolysList(B)
        for i in range(ps.OutlineCount()):
            ol = pcbnew.SHAPE_POLY_SET(); ol.NewOutline(); o = ps.Outline(i)
            for k in range(o.PointCount()): ol.Append(o.CPoint(k))
            q = ol.BBox(); area_ = ol.Area()/1e12
            if area_ < .05: continue
            has = any(ol.Contains(pcbnew.VECTOR2I(mm(OX+a), mm(OY+e))) and False for a, e in vias)
            has = any(t.GetNetCode() == v3 and ol.Contains(t.GetPosition()) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
            print("band piece", i, round(area_, 2), "via" if has else "none")
            if has: continue
            done = False; X0, Y0, X1, Y1 = um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY
            xs = [X0+k*.05 for k in range(int((X1-X0)/.05)+1)]; ys = [Y0+k*.05 for k in range(int((Y1-Y0)/.05)+1)]
            for x in xs:
                for y in ys:
                    if not done and ol.Contains(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))) and free(x, y, "+3V3", R=.25, sep=.37):
                        # inner rim stays in the band: both ends must stay on the piece
                        via(x, y, v3, .2, .1); vias.append((x, y)); done = True; added += 1
            print("  via placed" if done else "  NO SITE")
print("band vias", added)
filler.Fill(b.Zones())
pcbnew.SaveBoard(str(PCB), b)
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetFirstLayer() == B: print(z.GetZoneName(), "pieces", z.GetFilledPolysList(B).OutlineCount(), "area", round(z.GetFilledPolysList(B).Area()/1e12, 2))
