#!/usr/bin/env python3
"""lens_check.py BOARD.kicad_pcb ROUTER.log: judge each 'narrow pad joint' line against the finished board.

For each line: find the same-net track end nearest the reported point on that layer and the pad named,
measure the lens (chord of the round cap across the pad edge), then ask whether that lens is load-bearing:
drop the track-to-pad link and see whether the track still reaches the pad through other copper of the net.
Prints a class per line and totals:
  gone        no such track end on the finished board (cleaning dropped or moved it)
  sound       end reaches at least w/4 from the pad edge, full width joint on the finished board
  wide        lens at or over 0.09 mm (fab minimum)
  redundant   lens under 0.09 mm but copper also joins the pad another way: no break if it fails
  sole        lens under 0.09 mm and the only path from that copper to the pad: a real defect
pad_joints.py is per pad: 'sole' lines on a pad with another sound joint pass it, because a pad passes when any one joint is sound.
"""
import collections, json, math, re, sys
import pcbnew
pcb, log = sys.argv[1:3]
b = pcbnew.LoadBoard(pcb); MM = 1e6
P = re.compile(r"narrow pad joint: (.+?) on (\S+) at \(([\d.-]+), ([\d.-]+)\) mm, ([\d.]+) mm wide where its track is ([\d.]+) mm .*ends outside (\S+)-(\S+)$")
fps = {f.GetReference(): f for f in b.GetFootprints()}
tr = collections.defaultdict(list); vi = collections.defaultdict(list)
for t in b.GetTracks():
    (vi if t.Type() == pcbnew.PCB_VIA_T else tr)[t.GetNetname()].append(t)
pads = collections.defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads(): pads[p.GetNetname()].append(p)
zn = {z.GetNetname() for z in b.Zones() if not z.GetIsRuleArea()}

def segdist(a, b_, q):
    ax, ay, bx, by = a.x, a.y, b_.x, b_.y; dx, dy = bx-ax, by-ay; l = dx*dx+dy*dy
    u = 0 if l == 0 else max(0, min(1, ((q.x-ax)*dx+(q.y-ay)*dy)/l))
    return math.hypot(ax+u*dx-q.x, ay+u*dy-q.y)

def linked(a, c):  # two tracks overlap
    if a.GetLayer() != c.GetLayer(): return False
    r = max(a.GetWidth(), c.GetWidth())/2
    return min(segdist(a.GetStart(), a.GetEnd(), c.GetStart()), segdist(a.GetStart(), a.GetEnd(), c.GetEnd()),
               segdist(c.GetStart(), c.GetEnd(), a.GetStart()), segdist(c.GetStart(), c.GetEnd(), a.GetEnd())) <= r

def reach_other(net, track, pad):
    """does `track` reach `pad` without the track-pad link itself?"""
    items = tr[net]; seen = {id(track)}; todo = [track]; vs = vi[net]; seenv = set()
    idx = {id(t): t for t in items}
    lay = pad.GetLayer(); poly = pad.GetEffectivePolygon(lay)
    while todo:
        t = todo.pop()
        if isinstance(t, pcbnew.PCB_VIA):
            for u in items:
                if id(u) not in seen and min(segdist(u.GetStart(), u.GetEnd(), t.GetPosition()),1e18) <= t.GetWidth(pcbnew.F_Cu)/2:
                    seen.add(id(u)); todo.append(u)
            if t.IsOnLayer(lay) and poly.SquaredDistance(t.GetPosition()) <= (t.GetWidth(lay)/2)**2: return True
            continue
        if t is not track and t.GetLayer() == lay:
            for e in (t.GetStart(), t.GetEnd()):
                if math.sqrt(poly.SquaredDistance(e)) < t.GetWidth()/2: return True
        for u in items:
            if id(u) not in seen and linked(t, u):
                seen.add(id(u)); todo.append(u)
        for v in vs:
            if id(v) not in seen and segdist(t.GetStart(), t.GetEnd(), v.GetPosition()) <= v.GetWidth(pcbnew.F_Cu)/2:
                seen.add(id(v)); todo.append(v)
    return False

cnt = collections.Counter(); rows = []
for ln in open(log):
    if "narrow pad joint" not in ln: continue
    m = P.search(ln.strip())
    if not m: cnt["unparsed"] += 1; continue
    net, lay, x, y, w0, full, ref, num = m.groups()
    q = pcbnew.VECTOR2I(int(float(x)*MM), int(float(y)*MM)); li = b.GetLayerID(lay)
    pad = next((p for p in fps[ref].Pads() if p.GetNumber() == num), None) if ref in fps else None
    if pad is None: cnt["gone"] += 1; continue
    poly = pad.GetEffectivePolygon(li)
    best = None
    for t in tr[net]:
        if t.GetLayer() != li: continue
        for e in (t.GetStart(), t.GetEnd()):
            d = math.sqrt(poly.SquaredDistance(e))
            if d < t.GetWidth()/2 and (best is None or d < best[0]) and math.hypot(e.x-q.x, e.y-q.y) < 0.4*MM:
                best = (d, t)
    if best is None: c = "gone"; lens = None
    else:
        d, t = best; r = t.GetWidth()/2; lens = 2*math.sqrt(r*r-d*d)/MM
        if d <= r/2: c = "sound"
        elif lens >= 0.09: c = "wide"
        elif net in zn: c = "plane-net"
        else: c = "redundant" if reach_other(net, t, pad) else "sole"
    cnt[c] += 1; rows.append(dict(net=net, pad=f"{ref}.{num}", log_mm=float(w0), final_mm=lens and round(lens, 3), cls=c, at=[float(x), float(y)]))
print(json.dumps(dict(totals=cnt, sole=[r for r in rows if r["cls"] == "sole"][:60]), indent=0))
if len(sys.argv) > 3: json.dump(rows, open(sys.argv[3], "w"), indent=0)
