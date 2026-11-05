#!/usr/bin/env python3
"""necks2.py IN.kicad_pcb OUT.kicad_pcb: fix track-to-pad corner necks under 0.09 mm without rerouting. Re-runnable on any finished board; IN's folder needs its .kicad_pro.
For each joint, lowest first, on the pad's true layer (pad.GetLayer() says F.Cu for flipped pads):
  A move the track's end inside the pad so it crosses the edge at full width (anything sharing that end moves too);
  B dogleg: keep the far end, go to a point just outside the pad, then straight in;
  C delete the track if KiCad's open count doesn't rise: its joint was doing nothing.
Each move is kept only if it clears foreign copper and holes by geometry. Prints what it did and what it couldn't. Judge with KiCad DRC."""
import collections, math, sys, os
import pcbnew
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import linemerge
from shapely.strtree import STRtree
inp, out = sys.argv[1:3]
b = pcbnew.LoadBoard(inp); um = pcbnew.ToMM; fm = pcbnew.FromMM
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
count = lambda: b.GetConnectivity().GetUnconnectedCount(False); base = count()
LAY = [b.GetLayerName(l) for l in range(64) if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)]; ids = {b.GetLayerName(l): l for l in range(64)}
P = lambda v: (um(v.x), um(v.y)); HOLE = .2
def cl(n):
    if any(k in n for k in ("XIN", "XOUT", "C24-Pad1", "USB_D")): return .15
    if "VREG_LX" in n: return .12
    if "QSPI" in n: return .1
    return .09
def seg(a, c, w): return LineString([a, c]).buffer(w/2, 8) if a != c else Point(a).buffer(w/2, 8)
items = {L: [] for L in LAY}; holes = []; pads = []; tracks = list(b.GetTracks())
for f in b.GetFootprints():
    for p in f.Pads():
        for L in LAY:
            if p.IsOnLayer(ids[L]):
                o = p.GetEffectivePolygon(ids[L]).Outline(0); g = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
                if g.is_valid and not g.is_empty:
                    items[L].append((g, p.GetNetname(), ("p", id(p)))); pads.append((f.GetReference(), p.GetNumber(), p, L, g))
        if p.GetDrillSizeX() > 0: holes.append((Point(P(p.GetPosition())).buffer(um(p.GetDrillSizeX())/2), p.GetNetname(), ("ph", id(p))))
for t in tracks:
    n = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        c = P(t.GetPosition()); g = Point(c).buffer(um(t.GetWidth(ids["F.Cu"]))/2, 12)
        for L in LAY: items[L].append((g, n, ("v", id(t))))
        holes.append((Point(c).buffer(um(t.GetDrill())/2, 12), n, ("vh", id(t))))
    else: items[t.GetLayerName()].append((seg(P(t.GetStart()), P(t.GetEnd()), um(t.GetWidth())), n, ("t", id(t))))
tree = {L: STRtree([i[0] for i in items[L]]) for L in LAY}; htree = STRtree([h[0] for h in holes]); dead = set(); added = {L: [] for L in LAY}
def clear(L, g, n):
    q = g.buffer(.2)
    for k in tree[L].query(q):
        gg, m, key = items[L][k]
        if m != n and key not in dead and gg.distance(g) < max(cl(n), cl(m))-1e-5: return False
    for gg, m, key in added[L]:
        if m != n and key not in dead and gg.distance(g) < max(cl(n), cl(m))-1e-5: return False
    for k in htree.query(g.buffer(HOLE)):
        h, m, key = holes[k]
        if m != n and key not in dead and h.distance(g) < HOLE-1e-5: return False
    return True
def neck(a, c, w, poly):
    g = seg(a, c, w)
    if not g.intersects(poly): return None
    if poly.contains(g): return w
    x = poly.exterior.intersection(g)
    if x.is_empty: return None
    if x.geom_type == "MultiLineString": x = linemerge(x)
    if x.geom_type == "LineString": return min(w, math.dist(x.coords[0], x.coords[-1]))
    return w
by = collections.defaultdict(list)
for t in tracks:
    if not isinstance(t, pcbnew.PCB_VIA): by[t.GetNetname()].append(t)
viaat = collections.defaultdict(list)
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA): viaat[t.GetNetname()].append(P(t.GetPosition()))
found = []
for ref, num, p, L, poly in pads:
    if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.GetNetname(): continue
    n = p.GetNetname()
    for t in by[n]:
        if t.GetLayerName() != L: continue
        a, c = P(t.GetStart()), P(t.GetEnd()); w = um(t.GetWidth()); da, dc = poly.distance(Point(a)), poly.distance(Point(c))
        if min(da, dc) >= w/2: continue
        k = neck(a, c, w, poly)
        if k is not None and k < .09-1e-4: found.append((k, ref, num, p, L, poly, t))
found.sort(key=lambda r: r[0]); stat = collections.Counter(); log = []; removed = []; gone = set()
V = lambda q: pcbnew.VECTOR2I(fm(q[0]), fm(q[1]))
for k, ref, num, p, L, poly, t in found:
    if id(t) in gone: continue
    n = p.GetNetname(); a, c = P(t.GetStart()), P(t.GetEnd()); w = um(t.GetWidth())
    if not (neck(a, c, w, poly) or 1) or (neck(a, c, w, poly) or 1) >= .09-1e-4: stat["already"] += 1; continue
    da, dc = poly.distance(Point(a)), poly.distance(Point(c)); e, o_ = (a, c) if da <= dc else (c, a); isstart = da <= dc
    partners = []
    for u in by[n]:
        if u is t or u.GetLayerName() != L or id(u) in gone: continue
        ua, uc = P(u.GetStart()), P(u.GetEnd())
        if math.dist(ua, e) < .01: partners.append((u, True, uc))
        elif math.dist(uc, e) < .01: partners.append((u, False, ua))
    hasvia = any(math.dist(v, e) < .01 for v in viaat[n])
    cx, cy = poly.centroid.x, poly.centroid.y; opts = []; inner = poly.buffer(-w/2+.005)
    if not inner.is_empty:
        for i in range(-30, 31):
            for j in range(-30, 31):
                q = (cx+i*.01, cy+j*.01)
                if inner.contains(Point(q)): opts.append((math.dist(q, e), q))
    if not opts:
        for i in range(-40, 41):
            for j in range(-40, 41):
                q = (cx+i*.01, cy+j*.01)
                if poly.buffer(-.04).contains(Point(q)): opts.append((math.dist(q, e), q))
    opts.sort(); dead.add(("t", id(t)))
    for u, _, _ in partners: dead.add(("t", id(u)))
    done = None
    if hasvia:
        vobj = next(v for v in tracks if isinstance(v, pcbnew.PCB_VIA) and v.GetNetname() == n and math.dist(P(v.GetPosition()), e) < .01)
        if not vobj.IsLocked():
            others = []
            for u in by[n]:
                if id(u) in gone: continue
                ua, uc = P(u.GetStart()), P(u.GetEnd())
                if math.dist(ua, e) < .01: others.append((u, True, uc))
                elif math.dist(uc, e) < .01: others.append((u, False, ua))
            for u, _, _ in others: dead.add(("t", id(u)))
            dead.add(("v", id(vobj))); dead.add(("vh", id(vobj))); vw = um(vobj.GetWidth(ids["F.Cu"])); vd = um(vobj.GetDrill())
            for d, q in opts:
                if d > .35: break
                ok = all(clear(LL, Point(q).buffer(vw/2, 12), n) and clear(LL, Point(q).buffer(vd/2, 12), n) for LL in LAY)
                if ok:
                    for hh in (Point(q).buffer(vd/2, 12),):
                        for LL in LAY:
                            for gg, m, key in items[LL]:
                                if m != n and key not in dead and gg.distance(hh) < HOLE-1e-5: ok = False; break
                            if not ok: break
                if not ok: continue
                kk = [neck(far, q, um(u.GetWidth()), poly) for u, _, far in others if u.GetLayerName() == L]
                if any(x is not None and x < .09-1e-4 for x in kk): continue
                if not all(clear(u.GetLayerName(), seg(far, q, um(u.GetWidth())), n) for u, _, far in others): continue
                done = ("V", q); break
            if done:
                q = done[1]; vobj.SetPosition(V(q))
                for u, st, far in others:
                    (u.SetStart if st else u.SetEnd)(V(q)); added[u.GetLayerName()].append((seg(far, q, um(u.GetWidth())), n, ("v2", id(u))))
                for LL in LAY: added[LL].append((Point(q).buffer(vw/2, 12), n, ("v2", id(vobj))))
                stat["V move via"] += 1; log.append((ref+"."+num, round(k, 3), "V", round(math.dist(q, e), 3))); continue
            dead.discard(("v", id(vobj))); dead.discard(("vh", id(vobj)))
            for u, _, _ in others: dead.discard(("t", id(u)))
            dead.add(("t", id(t)))
            for u, _, _ in partners: dead.add(("t", id(u)))
    if not hasvia:
        for d, q in opts:                                  # A
            kk = neck(o_, q, w, poly)
            if kk is None or kk < .09-1e-4 or not clear(L, seg(o_, q, w), n): continue
            pk = [neck(far, q, um(u.GetWidth()), poly) for u, _, far in partners]
            if any(x is not None and x < .09-1e-4 for x in pk): continue
            if all(clear(L, seg(far, q, um(u.GetWidth())), n) for u, _, far in partners): done = ("A", q); break
    if done:
        q = done[1]
        (t.SetStart if isstart else t.SetEnd)(V(q)); added[L].append((seg(o_, q, w), n, ("a", id(t))))
        for u, st, far in partners:
            (u.SetStart if st else u.SetEnd)(V(q)); added[L].append((seg(far, q, um(u.GetWidth())), n, ("a", id(u))))
        stat["A move end"] += 1; log.append((ref+"."+num, round(k, 3), "A", round(math.dist(q, e), 3))); continue
    if not hasvia or True:                                 # B: keep everything else at e if it's elsewhere; a new vertex outside the pad, then in
        for d, q in opts[:400]:
            for ang in range(0, 360, 15):
                aa = (q[0]+.25*math.cos(math.radians(ang)), q[1]+.25*math.sin(math.radians(ang)))
                if poly.distance(Point(aa)) < w/2+.002: continue
                kk = neck(aa, q, w, poly)
                if kk is None or kk < .09-1e-4: continue
                if hasvia or partners:
                    # from the existing end: e stays, t stays but is pulled clear only if it can be; else skip
                    continue
                if clear(L, seg(o_, aa, w), n) and clear(L, seg(aa, q, w), n): done = ("B", aa, q); break
            if done: break
    if done:
        _, aa, q = done
        (t.SetStart if isstart else t.SetEnd)(V(aa)); added[L].append((seg(o_, aa, w), n, ("b", id(t))))
        nt = pcbnew.PCB_TRACK(b); nt.SetStart(V(aa)); nt.SetEnd(V(q)); nt.SetWidth(fm(w)); nt.SetLayer(ids[L]); nt.SetNetCode(p.GetNetCode()); b.Add(nt); added[L].append((seg(aa, q, w), n, ("bn", id(nt)))); removed.append(nt)
        stat["B dogleg"] += 1; log.append((ref+"."+num, round(k, 3), "B", 0)); continue
    # C: is this track needed at all?
    dead.discard(("t", id(t)))
    for u, _, _ in partners: dead.discard(("t", id(u)))
    removed.append(t); b.Remove(t); b.BuildConnectivity()
    if count() <= base:
        gone.add(id(t)); dead.add(("t", id(t))); stat["C delete"] += 1; log.append((ref+"."+num, round(k, 3), "C", 0))
    else:
        b.Add(t); b.BuildConnectivity(); stat["left"] += 1; log.append((ref+"."+num, round(k, 3), "LEFT", n.split("/")[-1], "via at end" if hasvia else f"{len(partners)} sharing"))
print("found", len(found), dict(stat), "open", base, "->", count())
print([x for x in log if x[2] != "A"]); print("A sample", [x for x in log if x[2] == "A"][:5])
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b); sys.stdout.flush(); os._exit(0)
