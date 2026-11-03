#!/usr/bin/env python3
"""necks.py BOARD.kicad_pcb [OUT.json]: true copper neck of every track-to-pad joint on a finished board.

pad_joints.py calls an end inside the pad sound. At a rectangular pad's corner that isn't enough: the
track's cap straddles the corner and copper passes through a chord far under the track's width.
For each track end within w/2 of a same-net SMD pad, take the pad outline inside the track's capsule;
the neck is the straight distance between the two points where the outline enters and leaves it
(a full chord across a straight edge is the width or more; capped at the width).
Under 0.09 mm (JLC min track) is reported, split by whether the joint is load-bearing:
  sole       dropping this track-pad link leaves that copper no other route to the pad
  redundant  other same-net copper also reaches the pad (nearest thing to harmless)
"""
import collections, json, math, sys
import pcbnew
from shapely.geometry import LineString, Polygon, MultiLineString
FLOOR = 0.09
b = pcbnew.LoadBoard(sys.argv[1])
trk = collections.defaultdict(list); via = collections.defaultdict(list)
for t in b.GetTracks():
    (via if t.Type() == pcbnew.PCB_VIA_T else trk)[t.GetNetname()].append(t)
mm = lambda v: v / 1e6
def cap(t): return LineString([(mm(t.GetStart().x), mm(t.GetStart().y)), (mm(t.GetEnd().x), mm(t.GetEnd().y))]).buffer(mm(t.GetWidth()) / 2, 16)
def neck(t, poly):
    c = cap(t); w = mm(t.GetWidth())
    if not c.intersects(poly): return None
    if poly.contains(c): return w                    # wholly inside: its other end carries on, judged there
    x = poly.exterior.intersection(c)
    if x.is_empty: return None
    if x.geom_type == "MultiLineString":             # corner cases come back as pieces: chain them
        from shapely.ops import linemerge
        x = linemerge(x)
    if x.geom_type == "LineString":
        p, q = x.coords[0], x.coords[-1]
        return min(w, math.dist(p, q))
    return w
def others(net, t0, pad, lay):
    poly = pad.GetEffectivePolygon(lay); seen = {id(t0)}; todo = [t0]; ts = trk[net]; vs = via[net]
    def touch(a, c):
        return a.GetLayer() == c.GetLayer() and cap(a).intersects(cap(c))
    while todo:
        t = todo.pop()
        if isinstance(t, pcbnew.PCB_VIA):
            P = t.GetPosition(); r = t.GetWidth(pcbnew.F_Cu) / 2
            if t.IsOnLayer(lay) and poly.SquaredDistance(P) <= r * r: return True
            for u in ts:
                if id(u) not in seen and cap(u).distance(LineString([(mm(P.x), mm(P.y)), (mm(P.x) + 1e-6, mm(P.y))])) <= mm(r):
                    seen.add(id(u)); todo.append(u)
            continue
        if t is not t0 and t.GetLayer() == lay and any(math.sqrt(poly.SquaredDistance(e)) < t.GetWidth() / 2 for e in (t.GetStart(), t.GetEnd())): return True
        for u in ts:
            if id(u) not in seen and touch(t, u): seen.add(id(u)); todo.append(u)
        c = cap(t)
        for v in vs:
            P = v.GetPosition()
            if id(v) not in seen and c.distance(LineString([(mm(P.x), mm(P.y)), (mm(P.x) + 1e-6, mm(P.y))])) <= mm(v.GetWidth(pcbnew.F_Cu)) / 2:
                seen.add(id(v)); todo.append(v)
    return False
rows = []; n = 0
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not net or net.startswith("unconnected"): continue
        lay = pad.GetLayer(); sp = pad.GetEffectivePolygon(lay); o = sp.Outline(0)
        poly = Polygon([(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())])
        if not poly.is_valid or poly.is_empty: continue
        for t in trk[net]:
            if t.GetLayer() != lay: continue
            if min(math.sqrt(sp.SquaredDistance(e)) for e in (t.GetStart(), t.GetEnd())) >= t.GetWidth() / 2: continue
            k = neck(t, poly); n += 1
            if k is not None and k < FLOOR - 1e-4:
                rows.append(dict(pad=f"{fp.GetReference()}.{pad.GetNumber()}", net=net, neck=round(k, 3), w=mm(t.GetWidth()), load="redundant" if others(net, t, pad, lay) else "sole"))
c = collections.Counter(r["load"] for r in rows)
led = sum(1 for r in rows if r["pad"].startswith("D"))
hist = collections.Counter(round(r["neck"], 2) for r in rows)
print(f"necks: {n} track-pad joints, {len(rows)} under {FLOOR} mm ({c['sole']} sole, {c['redundant']} redundant; {led} on LED pads); min {min((r['neck'] for r in rows), default=None)}; by 0.01: {sorted(hist.items())}")
if len(sys.argv) > 2: json.dump(rows, open(sys.argv[2], "w"), indent=0)
