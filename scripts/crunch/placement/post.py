#!/usr/bin/env python3
"""post.py IN.kicad_pcb OUT.kicad_pcb: post-route work on a finished board, each step checked against foreign copper by geometry, then judged by KiCad DRC.
 1. 0.2/0.1 vias become 0.25/0.15 where they fit.  2. Extra vias for VSYS and VBAT at U5.  3. Corner necks: move a track's end inside the pad so it crosses the edge at full width.
 4. Widen the worst SW inner-layer segments where free. IN's folder must hold its .kicad_pro."""
import collections, json, math, sys
import pcbnew
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import linemerge
from shapely.strtree import STRtree
inp, out = sys.argv[1:3]
b = pcbnew.LoadBoard(inp); um = pcbnew.ToMM; fm = pcbnew.FromMM
CL = .09; HOLE = .2
LAY = [b.GetLayerName(l) for l in range(64) if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)]; ids = {b.GetLayerName(l): l for l in range(64)}
P = lambda v: (um(v.x), um(v.y))
def seg(a, c, w): return LineString([a, c]).buffer(w/2, 8) if a != c else Point(a).buffer(w/2, 8)
class Geo:
    def __init__(s):
        s.items = {L: [] for L in LAY}; s.holes = []; s.dead = set(); s.added = {L: [] for L in LAY}; s.addh = []
    def add(s, L, g, net, key): s.items[L].append((g, net, key))
    def build(s):
        s.tree = {L: STRtree([i[0] for i in s.items[L]]) for L in LAY}; s.htree = STRtree([h[0] for h in s.holes])
    def near(s, L, g, d):
        q = g.buffer(d)
        for k in s.tree[L].query(q):
            it = s.items[L][k]
            if it[2] not in s.dead: yield it
        for it in s.added[L]:
            if it[2] not in s.dead and it[0].intersects(q): yield it
    def clear(s, L, g, net, cl=CL):
        for gg, n, key in s.near(L, g, cl):
            if n != net and gg.distance(g) < cl-1e-5: return False
        return True
    def hole_ok(s, g, net, ignore=None):
        q = g.buffer(HOLE)
        for k in s.htree.query(q):
            h = s.holes[k]
            if h[1] != net and h[2] not in s.dead and h[0].distance(g) < HOLE-1e-5: return False
        for h in s.addh:
            if h[1] != net and h[2] not in s.dead and h[0].distance(g) < HOLE-1e-5: return False
        return True
    def put(s, L, g, net, key): s.added[L].append((g, net, key))
G = Geo()
padgeo = []
for f in b.GetFootprints():
    for p in f.Pads():
        for L in LAY:
            if p.IsOnLayer(ids[L]):
                sp = p.GetEffectivePolygon(ids[L]); o = sp.Outline(0); poly = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
                if poly.is_valid and not poly.is_empty:
                    G.add(L, poly, p.GetNetname(), ("pad", id(p)))
                    padgeo.append((f.GetReference(), p.GetNumber(), p, L, poly))
        if p.GetDrillSizeX() > 0:
            c = P(p.GetPosition()); G.holes.append((Point(c).buffer(um(p.GetDrillSizeX())/2), p.GetNetname(), ("padh", id(p))))
tracks = [t for t in b.GetTracks()]
for t in tracks:
    n = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        c = P(t.GetPosition()); g = Point(c).buffer(um(t.GetWidth(ids["F.Cu"]))/2, 12)
        for L in LAY: G.add(L, g, n, ("v", id(t)))
        G.holes.append((Point(c).buffer(um(t.GetDrill())/2, 12), n, ("vh", id(t))))
    else:
        G.add(t.GetLayerName(), seg(P(t.GetStart()), P(t.GetEnd()), um(t.GetWidth())), n, ("t", id(t)))
G.build()
def via_ok(c, net, w, d, ignore=()):
    g = Point(c).buffer(w/2, 12); h = Point(c).buffer(d/2, 12)
    for L in LAY:
        if not G.clear(L, g, net): return False
        if not G.clear(L, h, net, HOLE): return False
    return G.hole_ok(h, net)
# Step 1: via sizes.
rep = []; ok = no = 0
for v in tracks:
    if isinstance(v, pcbnew.PCB_VIA) and um(v.GetDrill()) < .149:
        c = P(v.GetPosition()); n = v.GetNetname()
        G.dead |= {("v", id(v)), ("vh", id(v))}
        if via_ok(c, n, .25, .15):
            v.SetWidth(fm(.25)); v.SetDrill(fm(.15)); ok += 1; key = ("v2", id(v))
            for L in LAY: G.put(L, Point(c).buffer(.125, 12), n, key)
            G.addh.append((Point(c).buffer(.075, 12), n, ("vh2", id(v))))
        else:
            G.dead -= {("v", id(v)), ("vh", id(v))}; no += 1; rep.append((n.split("/")[-1], round(c[0]-100, 2), round(c[1]-100, 2)))
print("0.2/0.1 vias: changed", ok, "can't", no, rep)
# Step 2: U5 vias.
sites = {}
via_all = collections.defaultdict(list)
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA): via_all[t.GetNetname()].append(P(t.GetPosition()))
def extra(net, near, w_tr, want, inner=False, vw=.3):
    """Sites near these B.Cu points. inner: site must also lie on the net's inner track, so the via carries current there."""
    got = 0; placed = []
    its = [t for t in tracks if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net and t.GetLayerName() not in ("B.Cu", "F.Cu")]
    cands = []
    for (x0, y0) in near:
        if inner:
            for t in its:
                a, c = P(t.GetStart()), P(t.GetEnd()); L_ = math.dist(a, c); k = max(1, int(L_/.04))
                for i in range(k+1):
                    q = (a[0]+(c[0]-a[0])*i/k, a[1]+(c[1]-a[1])*i/k); d = math.dist(q, (x0, y0))
                    if d < 3.0: cands.append((d, q, (x0, y0)))
        else:
            for i in range(-65, 66):
                for j in range(-65, 66):
                    q = (x0+i*.04, y0+j*.04); d = math.dist(q, (x0, y0))
                    if d < 2.6: cands.append((d, q, (x0, y0)))
    cands.sort(key=lambda r: r[0])
    for d, q, src in cands:
        if got >= want: break
        if any(math.dist(q, r) < .36 for r in placed) or any(math.dist(q, r) < .36 for r in via_all.get(net, [])): continue
        if not via_ok(q, net, vw, .15): continue
        sites[net] = sites.get(net, 0)+1
        s_ = seg(src, q, w_tr)
        if not G.clear("B.Cu", s_, net) or not G.hole_ok(s_, net): continue
        code = b.FindNet(net).GetNetCode(); v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(fm(q[0]), fm(q[1]))); v.SetWidth(fm(vw)); v.SetDrill(fm(.15)); v.SetLayerPair(ids["F.Cu"], ids["B.Cu"]); v.SetNetCode(code); b.Add(v)
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(fm(src[0]), fm(src[1]))); t.SetEnd(pcbnew.VECTOR2I(fm(q[0]), fm(q[1]))); t.SetWidth(fm(w_tr)); t.SetLayer(ids["B.Cu"]); t.SetNetCode(code); b.Add(t)
        key = ("nv", id(v))
        for L in LAY: G.put(L, Point(q).buffer(vw/2, 12), net, key)
        G.addh.append((Point(q).buffer(.075, 12), net, key)); G.put("B.Cu", s_, net, ("nt", id(t))); placed.append(q); got += 1
        print(f"  extra {net} via at ({q[0]-100:.2f}, {q[1]-100:.2f}), {d:.2f} mm stub from ({src[0]-100:.2f}, {src[1]-100:.2f})")
    return got
u5 = {p.GetNumber(): P(p.GetPosition()) for f in b.GetFootprints() if f.GetReference() == "U5" for p in f.Pads()}
print("VSYS extra at U5:", extra("VSYS", [u5["11"], u5["10"]], .2, 2, vw=.25))
print("VBAT extra at U5:", extra("VBAT", [u5["2"], u5["3"]], .3, 2, inner=True, vw=.25))
print("via sites free for these nets", sites)
# Step 3: corner necks.
def neck(a, c, w, poly):
    g = seg(a, c, w)
    if not g.intersects(poly): return None
    if poly.contains(g): return w
    x = poly.exterior.intersection(g)
    if x.is_empty: return None
    if x.geom_type == "MultiLineString": x = linemerge(x)
    if x.geom_type == "LineString":
        return min(w, math.dist(x.coords[0], x.coords[-1]))
    return w
stat = collections.Counter(); bys = collections.defaultdict(list); before = []
ends = collections.defaultdict(list)
for t in tracks:
    if not isinstance(t, pcbnew.PCB_VIA):
        ends[t.GetNetname()].append(t)
via_at = collections.defaultdict(list)
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA): via_at[t.GetNetname()].append(P(t.GetPosition()))
for ref, num, p, L, poly in padgeo:
    if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
    n = p.GetNetname()
    if not n: continue
    for t in ends[n]:
        if t.GetLayerName() != L: continue
        a, c = P(t.GetStart()), P(t.GetEnd()); w = um(t.GetWidth())
        da, dc = poly.distance(Point(a)), poly.distance(Point(c))
        if min(da, dc) >= w/2: continue
        k = neck(a, c, w, poly)
        if k is None or k >= .09-1e-4: continue
        stat["found"] += 1; before.append(k)
        if k < .075: stat["found_under_075"] += 1
        endp = a if da <= dc else c; other = c if da <= dc else a
        # something else ending here? Only move if it stays inside this pad, or nothing else is there.
        blocked = False
        for u in ends[n]:
            if u is t or u.GetLayerName() != L: continue
            for e in (P(u.GetStart()), P(u.GetEnd())):
                if math.dist(e, endp) < .01 and not poly.contains(Point(e)): blocked = True
        if any(math.dist(v, endp) < .01 for v in via_at[n]): blocked = True
        if blocked: stat["junction"] += 1; continue
        cx, cy = poly.centroid.x, poly.centroid.y; opts = []
        for i in range(-12, 13):
            for j in range(-12, 13):
                q = (cx+i*.02, cy+j*.02)
                if poly.buffer(-w/2+.005).contains(Point(q)): opts.append((math.dist(q, endp), q))
        opts.sort(); done = False; moved_best = None; G.dead.add(("t", id(t)))
        for d, q in opts:
            g = seg(other, q, w)
            kk = neck(other, q, w, poly)
            if kk is None or kk < .09-1e-4: continue
            if G.clear(L, g, n) and G.hole_ok(g, n):
                done = True; moved_best = (q, g, kk); break
        if done:
            q, g, kk = moved_best
            if da <= dc: t.SetStart(pcbnew.VECTOR2I(fm(q[0]), fm(q[1])))
            else: t.SetEnd(pcbnew.VECTOR2I(fm(q[0]), fm(q[1])))
            G.put(L, g, n, ("t2", id(t), stat["fixed"])); stat["fixed"] += 1
            if len(bys["sample"]) < 6: bys["sample"].append((f"{ref}.{num}", round(k, 3), round(kk, 3), round(math.dist(q, endp), 3)))
        else:
            G.dead.discard(("t", id(t))); stat["no_room"] += 1; bys["unfixed"].append((f"{ref}.{num}", round(k, 3), n.split("/")[-1]))
print("necks:", dict(stat), "sample (pad, before, after, moved mm)", bys["sample"])
print("  unfixed under 0.075:", [u for u in bys["unfixed"] if u[1] < .075][:30])
# Step 4: SW widen, inner layers, only where free.
SW = sys.argv[3].split(",") if len(sys.argv) > 3 else []
w_done = collections.Counter(); w_mm = collections.Counter()
for net in SW:
    for t in ends[net] if net in ends else []:
        L = t.GetLayerName()
        if L in ("F.Cu", "B.Cu") or um(t.GetLength()) < .2: continue
        a, c = P(t.GetStart()), P(t.GetEnd()); G.dead.add(("t", id(t))); nw = None
        for w in (.25, .2, .15):
            g = seg(a, c, w)
            if G.clear(L, g, net) and G.hole_ok(g, net): nw = w; break
        if nw:
            t.SetWidth(fm(nw)); G.put(L, g, net, ("t3", id(t))); w_mm[net.split("/")[-1]] += um(t.GetLength()); w_done[net.split("/")[-1]] += 1
        else: G.dead.discard(("t", id(t)))
print("SW widened segments", dict(w_done), "mm", {k: round(v, 1) for k, v in w_mm.items()})
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b)
import os; sys.stdout.flush(); os._exit(0)
