#!/usr/bin/env python3
"""fix_open.py IN OUT NET REF.PAD [--grid 0.02] [--win 5] [--width .1]: finish one open connection on a routed board with a small multi-layer maze: from the named pad's copper island to any other copper of its net.
Keeps every clearance the board's rules ask for: 0.09 track, hole 0.2 to copper, and the named keep-out areas for foreign nets. Touches nothing else. Prints the path. Judge with KiCad DRC afterwards, never with this script."""
import argparse, heapq, math, sys
import numpy as np, pcbnew, shapely
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("net"); ap.add_argument("pad")
ap.add_argument("--grid", type=float, default=.02); ap.add_argument("--win", type=float, default=5); ap.add_argument("--width", type=float, default=.1); ap.add_argument("--clear", type=float, default=.09); ap.add_argument("--to", default="", help="second path: join REF.PAD to this REF.PAD though they're already joined"); ap.add_argument("--only", default="", help="route on this layer only"); ap.add_argument("--allow", default="", help="rule area this net is exempt from"); ap.add_argument("--plane", default="", help="also finish at a through via anywhere on this net's zone on this layer")
a = ap.parse_args()
b = pcbnew.LoadBoard(a.inp); um = pcbnew.ToMM; mm = pcbnew.FromMM
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
LAY = ["F.Cu", "In1.Cu", "In3.Cu", "In4.Cu", "In6.Cu", "B.Cu"]; ids = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
nets = [n for n in (b.GetNetInfo().NetsByName().keys()) ]
netname = next(str(n) for n in nets if str(n).endswith(a.net))
ref, num = a.pad.split(".")
fps = {f.GetReference(): f for f in b.GetFootprints()}
P = [p for p in fps[ref].Pads() if p.GetNumber() == num and p.GetNetname() == netname][0]
sx, sy = um(P.GetPosition().x)-100, um(P.GetPosition().y)-100
def padpoly(p):
    s = p.GetEffectivePolygon(p.GetLayerSet().Seq()[0]) if False else None
    q = p.GetBoundingBox(); w, h = um(p.GetSize().x)/2, um(p.GetSize().y)/2; c = p.GetPosition(); x, y = um(c.x)-100, um(c.y)-100
    t = math.radians(-p.GetOrientationDegrees()); C, S = math.cos(t), math.sin(t)
    return Polygon([(x+C*u-S*v, y+S*u+C*v) for u, v in ((-w, -h), (w, -h), (w, h), (-w, h))])
own = {L: [] for L in LAY}; foreign = {L: [] for L in LAY}; own_items = []
W = box(sx-a.win, sy-a.win, sx+a.win, sy+a.win)
for f in b.GetFootprints():
    for p in f.Pads():
        g = padpoly(p)
        if not g.intersects(W): continue
        for L in LAY:
            if p.IsOnLayer(ids[L]):
                (own if p.GetNetname() == netname else foreign)[L].append(g)
        if p.GetNetname() == netname: own_items.append(("pad", g, [L for L in LAY if p.IsOnLayer(ids[L])], f"{f.GetReference()}.{p.GetNumber()}"))
holes = []
for t in b.GetTracks():
    n = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        c = t.GetPosition(); pt = Point(um(c.x)-100, um(c.y)-100)
        if not pt.buffer(.3).intersects(W): continue
        g = pt.buffer(um(t.GetWidth(ids["F.Cu"]))/2)
        for L in LAY: (own if n == netname else foreign)[L].append(g)
        if n == netname: own_items.append(("via", g, LAY, "via"))
        else: holes.append(pt.buffer(um(t.GetDrill())/2))
    else:
        L = t.GetLayerName()
        if L not in LAY: continue
        g = LineString([(um(t.GetStart().x)-100, um(t.GetStart().y)-100), (um(t.GetEnd().x)-100, um(t.GetEnd().y)-100)]).buffer(um(t.GetWidth())/2)
        if not g.intersects(W): continue
        (own if n == netname else foreign)[L].append(g)
        if n == netname: own_items.append(("trk", g, [L], "track"))
nokeep = {L: [] for L in LAY}; novia = []
for z in b.Zones():
    if z.GetIsRuleArea():
        nm = z.GetZoneName(); o = z.Outline().Outline(0); g = Polygon([(um(o.CPoint(i).x)-100, um(o.CPoint(i).y)-100) for i in range(o.PointCount())])
        L = b.GetLayerName(z.GetFirstLayer())
        if nm in ("U1 ring", "U2 ring", "U3 ring", "reg corner", "L1 window", "LX no copper In6") and nm != a.allow and L in LAY: nokeep[L].append(g)
        if nm in ("reg corner", "L1 window"): novia.append(g)
        continue
    for L in LAY:
        if z.IsOnLayer(ids[L]) and z.GetNetname() != netname:
            ps = z.GetFilledPolysList(ids[L])
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k); g = Polygon([(um(o.CPoint(i).x)-100, um(o.CPoint(i).y)-100) for i in range(o.PointCount())]).buffer(0)
                if g.intersects(W): foreign[L].append(g)
# Islands of own copper by touching geometry; source is the pad's.
items = own_items; par = list(range(len(items)))
def fd(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i in range(len(items)):
    for j in range(i):
        if set(items[i][2]) & set(items[j][2]) and items[i][1].distance(items[j][1]) < 1e-4: par[fd(i)] = fd(j)
start = next(i for i, it in enumerate(items) if it[3] == a.pad)
src = fd(start); tgt = [it for i, it in enumerate(items) if fd(i) != src]; srcs = [it for i, it in enumerate(items) if fd(i) == src]
if a.to:
    tgt = [it for it in items if it[3] == a.to]; srcs = [it for it in items if it[3] == a.pad]
print("own items", len(items), "source island", len(srcs), "targets", len(tgt), [t[3] for t in tgt if t[0] == "pad"][:8])
if not tgt: sys.exit("nothing to join in this window; widen --win")
n = int(2*a.win/a.grid)+1; xs = np.linspace(sx-a.win, sx+a.win, n); ys = np.linspace(sy-a.win, sy+a.win, n); X, Y = np.meshgrid(xs, ys, indexing="ij")
TR = a.clear+a.width/2+.002; VR = .275+.002
block = {}; viaBad = np.zeros_like(X, bool)
for L in LAY:
    gg = unary_union(foreign[L]) if foreign[L] else None
    m = shapely.contains_xy(gg.buffer(TR), X, Y) if gg is not None else np.zeros_like(X, bool)
    if nokeep[L]: m |= shapely.contains_xy(unary_union(nokeep[L]).buffer(TR), X, Y)
    if holes: m |= shapely.contains_xy(unary_union(holes).buffer(.2+a.width/2+.003), X, Y)
    block[L] = m
    if gg is not None: viaBad |= shapely.contains_xy(gg.buffer(VR), X, Y)
if holes: viaBad |= shapely.contains_xy(unary_union(holes).buffer(.075+.2+.05+.002+.1), X, Y)
if novia: viaBad |= shapely.contains_xy(unary_union(novia).buffer(.14), X, Y)
if a.only:
    for L in LAY:
        if L != a.only: block[L] = np.ones_like(X, bool)
    viaBad = np.ones_like(X, bool)
# Own-net copper of other islands may be touched; a via must clear the source's other-net neighbours as above.
goal = {L: shapely.contains_xy(unary_union([t[1] for t in tgt if L in t[2]]), X, Y) if [t for t in tgt if L in t[2]] else np.zeros_like(X, bool) for L in LAY}
srcm = {L: shapely.contains_xy(unary_union([t[1] for t in srcs if L in t[2]]), X, Y) if [t for t in srcs if L in t[2]] else np.zeros_like(X, bool) for L in LAY}
planegoal = np.zeros_like(X, bool)
if a.plane:
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == netname and z.IsOnLayer(ids[a.plane]):
            ps = z.GetFilledPolysList(ids[a.plane])
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k); planegoal |= shapely.contains_xy(Polygon([(um(o.CPoint(i).x)-100, um(o.CPoint(i).y)-100) for i in range(o.PointCount())]).buffer(0).buffer(-.13), X, Y)
    planegoal &= ~viaBad; print("plane via sites", int(planegoal.sum()))
idx = {L: i for i, L in enumerate(LAY)}; pq = []; dist = {}; prev = {}
for L in LAY:
    for i, j in zip(*np.nonzero(srcm[L] & ~block[L])):
        s = (int(i), int(j), idx[L]); dist[s] = 0; heapq.heappush(pq, (0, s))
print("start states", len(pq))
VC = 1.5; steps = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]; end = None; seen = 0
tx, ty = None, None
while pq:
    d, u = heapq.heappop(pq)
    if d > dist.get(u, 1e9): continue
    i, j, l = u; L = LAY[l]; seen += 1
    if goal[L][i, j]: end = u; break
    if planegoal[i, j]: end = u; endvia = True; break
    for di, dj in steps:
        v = (i+di, j+dj, l)
        if not (0 <= v[0] < n and 0 <= v[1] < n) or block[L][v[0], v[1]]: continue
        nd = d+a.grid*math.hypot(di, dj)
        if nd < dist.get(v, 1e9): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
    if not viaBad[i, j]:
        for m_ in range(len(LAY)):
            if m_ != l and not block[LAY[m_]][i, j]:
                v = (i, j, m_); nd = d+VC
                if nd < dist.get(v, 1e9): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
if end is None:
    sl = idx[LAY[-1]]; x0 = int((sx-xs[0])/a.grid); y0 = int((sy-ys[0])/a.grid)
    for j in range(max(0, y0-30), min(n, y0+30), 3):
        print("".join("#" if block["B.Cu"][i, j] else ("v" if not viaBad[i, j] else ".") for i in range(max(0, x0-45), min(n, x0+45), 2)))
    sys.exit(f"no path in window; searched {seen} states")
path = [end]
print("ends with plane via" if "endvia" in globals() else "ends on copper")
while path[-1] in prev: path.append(prev[path[-1]])
path.reverse(); print("path length cost", round(dist[end], 2), "points", len(path))
# Emit: straight runs merged, vias at layer changes.
code = b.FindNet(netname).GetNetCode(); added = []
def P2(u): return pcbnew.VECTOR2I(mm(float(100+xs[u[0]])), mm(float(100+ys[u[1]])))
run = path[0]; dirn = None; pts = [path[0]]
for u in path[1:]:
    pts.append(u)
segs = []; cur = [pts[0]]
for u in pts[1:]:
    if u[2] != cur[-1][2]:
        segs.append(cur); segs.append(("via", u)); cur = [u]
    else: cur.append(u)
segs.append(cur)
for s in segs:
    if isinstance(s, tuple):
        v = pcbnew.PCB_VIA(b); v.SetPosition(P2(s[1])); v.SetWidth(mm(.25)); v.SetDrill(mm(.15)); v.SetLayerPair(ids["F.Cu"], ids["B.Cu"]); v.SetNetCode(code); b.Add(v); added.append(("via", round(xs[s[1][0]], 2), round(ys[s[1][1]], 2))); continue
    if len(s) < 2: continue
    k = 0
    while k < len(s)-1:
        e = k+1; d0 = (s[e][0]-s[k][0], s[e][1]-s[k][1])
        while e+1 < len(s) and (s[e+1][0]-s[e][0], s[e+1][1]-s[e][1]) == d0: e += 1
        t = pcbnew.PCB_TRACK(b); t.SetStart(P2(s[k])); t.SetEnd(P2(s[e])); t.SetWidth(mm(a.width)); t.SetLayer(ids[LAY[s[k][2]]]); t.SetNetCode(code); b.Add(t)
        added.append((LAY[s[k][2]], round(xs[s[k][0]], 2), round(ys[s[k][1]], 2), round(xs[s[e][0]], 2), round(ys[s[e][1]], 2))); k = e
if "endvia" in globals():
    v = pcbnew.PCB_VIA(b); v.SetPosition(P2(end)); v.SetWidth(mm(.25)); v.SetDrill(mm(.15)); v.SetLayerPair(ids["F.Cu"], ids["B.Cu"]); v.SetNetCode(code); b.Add(v); added.append(("plane via", round(xs[end[0]], 2), round(ys[end[1]], 2)))
print(added)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(a.out, b)
import os; sys.stdout.flush(); os._exit(0)
