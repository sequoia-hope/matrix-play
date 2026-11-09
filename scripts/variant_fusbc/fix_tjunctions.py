#!/usr/bin/env python3
"""fix_tjunctions.py — Split remaining same-net degree-1 T-junction grazes onto trunk centerlines."""
from __future__ import annotations

import collections
import math
import sys
from pathlib import Path
from shapely.geometry import LineString, Point
import pcbnew

KEEP_ALIVE: list = []


def main() -> int:
    inp, out = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(inp)
    um = pcbnew.ToMM
    fm = pcbnew.FromMM
    V = lambda q: pcbnew.VECTOR2I(fm(q[0]), fm(q[1]))
    snap = lambda x, y: (round(x, 4), round(y, 4))

    lay_ids = {
        b.GetLayerName(l): l
        for l in range(64)
        if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)
    }

    pads_by_nl = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if not n:
                continue
            for ln, lid in lay_ids.items():
                if p.IsOnLayer(lid):
                    o = p.GetEffectivePolygon(lid).Outline(0)
                    from shapely.geometry import Polygon
                    poly = Polygon([(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())])
                    if poly.is_valid and not poly.is_empty:
                        pads_by_nl[(n, ln)].append(poly)

    vias_by_n = collections.defaultdict(list)
    tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            vias_by_n[t.GetNetname()].append((um(t.GetPosition().x), um(t.GetPosition().y)))

    zones_by_nl = collections.defaultdict(list)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for ln, lid in lay_ids.items():
                if z.IsOnLayer(lid):
                    zones_by_nl[(z.GetNetname(), ln)].append((z, lid))

    deg = collections.Counter()
    by_nl = collections.defaultdict(list)
    for t in tracks:
        n, ln = t.GetNetname(), t.GetLayerName()
        s = snap(um(t.GetStart().x), um(t.GetStart().y))
        e = snap(um(t.GetEnd().x), um(t.GetEnd().y))
        deg[(n, ln, s)] += 1
        deg[(n, ln, e)] += 1
        by_nl[(n, ln)].append(t)

    fixed = 0
    for (n, ln), segs in list(by_nl.items()):
        for t in list(segs):
            s = snap(um(t.GetStart().x), um(t.GetStart().y))
            e = snap(um(t.GetEnd().x), um(t.GetEnd().y))
            w = um(t.GetWidth())
            for end_is_e, pt in ((False, s), (True, e)):
                if deg[(n, ln, pt)] != 1:
                    continue
                P_pt = Point(pt)
                if any(poly.buffer(0.003).contains(P_pt) for poly in pads_by_nl[(n, ln)]):
                    continue
                if any(math.dist(pt, vp) <= 0.003 for vp in vias_by_n[n]):
                    continue
                vec = pcbnew.VECTOR2I(fm(pt[0]), fm(pt[1]))
                if any(z.GetFilledPolysList(lid).Contains(vec) for z, lid in zones_by_nl[(n, ln)]):
                    continue

                # Find nearest trunk segment on same (n, ln)
                best = None
                for t2 in segs:
                    if t2 is t:
                        continue
                    s2 = snap(um(t2.GetStart().x), um(t2.GetStart().y))
                    e2 = snap(um(t2.GetEnd().x), um(t2.GetEnd().y))
                    if pt in (s2, e2) or s2 == e2:
                        continue
                    ls = LineString([s2, e2])
                    d = ls.distance(P_pt)
                    w2 = um(t2.GetWidth())
                    if d <= (w + w2) / 2.0 + 0.02:
                        if best is None or d < best[0]:
                            proj = ls.interpolate(ls.project(P_pt))
                            q = snap(proj.x, proj.y)
                            best = (d, t2, s2, e2, w2, q)

                if best is not None:
                    _, t2, s2, e2, w2, q = best
                    # Extend t endpoint to q
                    if end_is_e:
                        t.SetEnd(V(q))
                    else:
                        t.SetStart(V(q))
                    # Split t2 at q if q is interior
                    if math.dist(q, s2) > 0.002 and math.dist(q, e2) > 0.002:
                        t2.SetStart(V(s2))
                        t2.SetEnd(V(q))
                        nt = pcbnew.PCB_TRACK(b)
                        nt.SetStart(V(q))
                        nt.SetEnd(V(e2))
                        nt.SetWidth(t2.GetWidth())
                        nt.SetLayer(t2.GetLayer())
                        nt.SetNetCode(t2.GetNetCode())
                        nt.SetLocked(t2.IsLocked())
                        b.Add(nt)
                        KEEP_ALIVE.append(nt)
                        segs.append(nt)
                    deg[(n, ln, pt)] -= 1
                    deg[(n, ln, q)] += 3
                    fixed += 1
                    print(f"  Split T-junction on {n} ({ln}): {pt} -> {q}")

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pro_path = Path(out).with_suffix(".kicad_pro")
    dru_path = Path(out).with_suffix(".kicad_dru")
    pro_bak = pro_path.read_bytes() if pro_path.exists() else None
    dru_bak = dru_path.read_bytes() if dru_path.exists() else None
    pcbnew.SaveBoard(out, b)
    if pro_bak is not None:
        pro_path.write_bytes(pro_bak)
    if dru_bak is not None:
        dru_path.write_bytes(dru_bak)
    print(f"Saved {out} (fixed={fixed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
