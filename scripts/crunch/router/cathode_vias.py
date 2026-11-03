#!/usr/bin/env python3
"""cathode_vias.py IN.kicad_pcb OUT.kicad_pcb [--stub MM] [--keep-f N]: give LED cathode pads a locked via before routing,
as anodes_b already does for anodes: in the pad where the back allows, else on a short F.Cu stub to the nearest legal
spot. Reason: the router drops its own CS vias in the channels between LEDs, each one corking that channel on F.Cu.
With every pad escaped the matrix routes on In1/In3/B between regular via fields and F.Cu is nearly free.
Run with a .kicad_pro beside OUT. Prints counts. Legal: 0.275 mm via centre to foreign copper on B.Cu and F.Cu (hole clearance),
0.40 mm to foreign via centres, 0.35 to same-net, outside rule areas that ban vias, B.Cu zones of other nets avoided."""
import argparse, collections, math, re
import pcbnew
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--stub", type=float, default=0.75)
ap.add_argument("--no-stub", action="store_true")
a = ap.parse_args()
b = pcbnew.LoadBoard(a.inp); mm = pcbnew.FromMM; V = pcbnew.VECTOR2I
F, B_ = pcbnew.F_Cu, pcbnew.B_Cu
KEEP, FV, SV = .275, .40, .35
TOP = []; BOT = []
for f in b.GetFootprints():
    for p in f.Pads():
        for lay, lst in ((F, TOP), (B_, BOT)):
            if p.IsOnLayer(lay) and p.GetNetname() is not None:
                lst.append((p.GetEffectivePolygon(lay), p.GetNetname(), p.GetPosition()))
zones = [(z, z.GetNetname()) for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(B_)]
novia = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
vias = [(t.GetPosition(), t.GetNetname()) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
tracks = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T]
def dist(p, q): return math.hypot(p.x - q.x, p.y - q.y) / 1e6
def legal(q, net, skip_pad=None):
    if math.hypot(q.x / 1e6 - 100, q.y / 1e6 - 100) > 18.6: return False
    for lst in (TOP, BOT):
        for poly, n, c in lst:
            if n == net: continue
            if abs(c.x - q.x) > 3e6 or abs(c.y - q.y) > 3e6: continue
            if poly.SquaredDistance(q) < (KEEP * 1e6) ** 2: return False
    for c, n in vias:
        if dist(c, q) < (SV if n == net else FV): return False
    for z, n in zones:
        if n != net and z.Outline().SquaredDistance(q) < (KEEP * 1e6) ** 2: return False
        if n != net and z.Outline().Contains(q): return False
    for z in novia:
        if z.Outline().Contains(q): return False
    for t in tracks:
        if t.GetNetname() != net and t.GetLayer() in (F, B_) or t.GetNetname() != net:
            A, E = t.GetStart(), t.GetEnd(); dx, dy = E.x - A.x, E.y - A.y; l = dx * dx + dy * dy or 1
            u = max(0, min(1, ((q.x - A.x) * dx + (q.y - A.y) * dy) / l))
            if math.hypot(A.x + u * dx - q.x, A.y + u * dy - q.y) / 1e6 < KEEP + t.GetWidth() / 2e6: return False
    return True
def stub_ok(p0, q, net):
    n = 8
    for i in range(n + 1):
        s = V(int(p0.x + (q.x - p0.x) * i / n), int(p0.y + (q.y - p0.y) * i / n))
        for poly, m, c in TOP:
            if m == net or abs(c.x - s.x) > 2e6 or abs(c.y - s.y) > 2e6: continue
            if poly.SquaredDistance(s) < (.14 * 1e6) ** 2: return False
        for c, m in vias:
            if m != net and dist(c, s) < .325: return False
    return True
MATRIX = re.compile(r"/CS\d_\d+$")
pads = []
for f in b.GetFootprints():
    if not f.GetReference().startswith("D"): continue
    for p in f.Pads():
        if MATRIX.search(p.GetNetname()): pads.append(p)
def add_via(q, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(q); v.SetWidth(mm(.25)); v.SetDrill(mm(.15)); v.SetLayerPair(F, B_); v.SetNetCode(net.GetNetCode()); v.SetLocked(True); b.Add(v)
    vias.append((q, net.GetNetname()))
cnt = collections.Counter(); rest = []
for p in pads:
    c = p.GetPosition()
    if legal(c, p.GetNetname()): add_via(c, p.GetNet()); cnt["in-pad"] += 1
    else: rest.append(p)
for p in rest:
    c = p.GetPosition(); best = None
    if not a.no_stub:
        for r in (.34, .4, .46, .52, .6, .68, a.stub):
            for k in range(24):
                th = k * math.pi / 12; q = V(int(c.x + r * 1e6 * math.cos(th)), int(c.y + r * 1e6 * math.sin(th)))
                if legal(q, p.GetNetname()) and stub_ok(c, q, p.GetNetname()): best = q; break
            if best: break
    if best is None: cnt["none"] += 1; continue
    t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(best); t.SetWidth(mm(.1)); t.SetLayer(F); t.SetNetCode(p.GetNetCode()); t.SetLocked(True); b.Add(t)
    tracks.append(t); add_via(best, p.GetNet()); cnt["stub"] += 1
pcbnew.SaveBoard(a.out, b)
print(dict(cnt), "of", len(pads), "cathode pads")
