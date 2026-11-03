#!/usr/bin/env python3
"""sensor_sites.py BOARD -- where a small front-side part could go without moving anything. For body sizes in mm, scan the disc at each position and rotation; report sites clear of front
copper, holes, LED bodies and the board edge, largest margin first, and how far a free through-via site is. A survey: it changes nothing."""
import math, sys
import pcbnew
from shapely.geometry import Point, LineString, Polygon, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
from shapely.strtree import STRtree
b = pcbnew.LoadBoard(sys.argv[1]); C = 100.
mm = lambda v: v/1e6
obs = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        obs.append(Point(mm(t.GetPosition().x)-C, mm(t.GetPosition().y)-C).buffer(mm(t.GetWidth(pcbnew.F_Cu))/2, 8))
    elif t.GetLayer() == pcbnew.F_Cu:
        obs.append(LineString([(mm(t.GetStart().x)-C, mm(t.GetStart().y)-C), (mm(t.GetEnd().x)-C, mm(t.GetEnd().y)-C)]).buffer(mm(t.GetWidth())/2, 4))
for f in b.GetFootprints():
    r = f.GetReference()
    if r.startswith("D"):
        x, y = mm(f.GetPosition().x)-C, mm(f.GetPosition().y)-C
        obs.append(rotate(box(x-.5, y-.5, x+.5, y+.5), -f.GetOrientationDegrees(), origin=(x, y)))
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.F_Cu):
            o = p.GetEffectivePolygon(pcbnew.F_Cu).Outline(0)
            obs.append(Polygon([(mm(o.CPoint(i).x)-C, mm(o.CPoint(i).y)-C) for i in range(o.PointCount())]))
        elif p.GetDrillSize().x > 0:
            obs.append(Point(mm(p.GetPosition().x)-C, mm(p.GetPosition().y)-C).buffer(mm(p.GetDrillSize().x)/2, 12))
print("obstacles", len(obs))
tree = STRtree(obs)
R = 19.0; CL = .1; EDGE = .25
for L, W, name in ((2.3, .8, "ALS-PT19 land, earring footprint"), (1.7, .8, "1.7x0.8"), (1.6, .8, "0603 size"), (1.0, .5, "0402 size"), (2.0, 1.25, "2.0x1.25")):
    best = []
    for rr in [r/10 for r in range(20, 188, 2)]:
        n = max(8, int(2*math.pi*rr/.25))
        for k in range(n):
            a = 2*math.pi*k/n; x, y = rr*math.cos(a), rr*math.sin(a)
            for ang in (0, 30, 60, 90, 120, 150, math.degrees(a)):
                bx = rotate(box(x-L/2, y-W/2, x+L/2, y+W/2), ang, origin=(x, y))
                if max(math.hypot(*c) for c in bx.exterior.coords) > R-EDGE:
                    continue
                near = tree.query(bx.buffer(.6))
                d = min((bx.distance(obs[i]) for i in near), default=.6)
                if d >= CL:
                    best.append((round(d, 2), round(x, 1), round(y, 1), round(rr, 1), round(ang) % 180))
    best.sort(reverse=True)
    picks = []
    for s in best:
        if all(math.dist(s[1:3], p[1:3]) > 2 for p in picks):
            picks.append(s)
    print(name, "clear positions", len(best), "distinct sites", len(picks))
    for s in picks[:10]:
        print("   margin", s[0], "at", s[1:3], "radius", s[3], "angle", s[4])
