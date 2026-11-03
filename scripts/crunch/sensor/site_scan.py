#!/usr/bin/env python3
"""site_scan.py BOARD SPACE.npz [--land LxW --pitch P --body LxW]: scan the disc for the sensor's real LAND pattern (survey used body only).
A site passes if both lands clear F.Cu copper by 0.09, the body clears LED bodies by 0.05 and the lands the rim by 0.25.
For each passing placement, report legal through-via area (space.py map) inside/near each land, and the In5 net under each land."""
import argparse, math, sys
import numpy as np, pcbnew
from shapely.geometry import Point, LineString, Polygon, box
from shapely.affinity import rotate, translate
from shapely.strtree import STRtree
ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("space"); ap.add_argument("--land", default="0.8x0.8"); ap.add_argument("--pitch", type=float, default=1.5); ap.add_argument("--body", default="1.7x0.8"); a = ap.parse_args()
lw, lh = map(float, a.land.split("x")); bl, bh = map(float, a.body.split("x"))
b = pcbnew.LoadBoard(a.board); C = 100.; mm = lambda v: v/1e6
sp = np.load(a.space); via = sp["via"]; H = .025
obs = []; leds = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        obs.append(Point(mm(t.GetPosition().x)-C, mm(t.GetPosition().y)-C).buffer(mm(t.GetWidth(pcbnew.F_Cu))/2, 8))
    elif t.GetLayer() == pcbnew.F_Cu:
        obs.append(LineString([(mm(t.GetStart().x)-C, mm(t.GetStart().y)-C), (mm(t.GetEnd().x)-C, mm(t.GetEnd().y)-C)]).buffer(mm(t.GetWidth())/2, 4))
for f in b.GetFootprints():
    r = f.GetReference()
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.F_Cu):
            o = p.GetEffectivePolygon(pcbnew.F_Cu).Outline(0)
            obs.append(Polygon([(mm(o.CPoint(i).x)-C, mm(o.CPoint(i).y)-C) for i in range(o.PointCount())]))
        elif p.GetDrillSize().x > 0:
            obs.append(Point(mm(p.GetPosition().x)-C, mm(p.GetPosition().y)-C).buffer(mm(p.GetDrillSize().x)/2+.1, 12))
    if r.startswith("D"):
        x, y = mm(f.GetPosition().x)-C, mm(f.GetPosition().y)-C
        leds.append(rotate(box(x-.5, y-.5, x+.5, y+.5), -f.GetOrientationDegrees(), origin=(x, y)))
T = STRtree(obs); TL = STRtree(leds)
zn = {}
for z in b.Zones():
    if not z.GetIsRuleArea() and z.IsOnLayer(b.GetLayerID("In5.Cu")): zn[z.GetNetname()] = z
def in5(x, y):
    q = pcbnew.VECTOR2I(int((x+C)*1e6), int((y+C)*1e6)); out = []
    for n, z in zn.items():
        if z.GetFilledPolysList(b.GetLayerID("In5.Cu")).Contains(q): out.append(n)
    return out
def via_near(x, y, r):
    ci, cj = int((y+20)/H), int((x+20)/H); k = int(r/H)
    s = via[ci-k:ci+k+1, cj-k:cj+k+1]
    yy, xx = np.nonzero(s)
    if not len(yy): return None
    d = np.hypot(yy-k, xx-k)*H; i = d.argmin()
    return round(float(d[i]), 3), round(float(s.sum()*H*H), 3)
res = []
for rr in np.arange(10, 18.8, .1):
    n = int(2*math.pi*rr/.1)
    for k in range(n):
        th = 2*math.pi*k/n; x, y = rr*math.cos(th), rr*math.sin(th)
        for ang in range(0, 180, 15):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            p1 = (x-a.pitch/2*ca, y-a.pitch/2*sa); p2 = (x+a.pitch/2*ca, y+a.pitch/2*sa)
            L1 = rotate(box(p1[0]-lw/2, p1[1]-lh/2, p1[0]+lw/2, p1[1]+lh/2), ang, origin=p1); L2 = rotate(box(p2[0]-lw/2, p2[1]-lh/2, p2[0]+lw/2, p2[1]+lh/2), ang, origin=p2)
            bd = rotate(box(x-bl/2, y-bh/2, x+bl/2, y+bh/2), ang, origin=(x, y))
            if max(math.hypot(*c) for g in (L1, L2, bd) for c in g.exterior.coords) > 18.75: continue
            m = 9
            bad = False
            for g in (L1, L2):
                for i in T.query(g.buffer(.6)):
                    d = g.distance(obs[i]); m = min(m, d)
                    if d < .09: bad = True; break
                if bad: break
            if bad: continue
            ml = min((bd.distance(leds[i]) for i in TL.query(bd.buffer(.3))), default=.3)
            if ml < .05: continue
            v1 = via_near(*p1, .6); v2 = via_near(*p2, .6)
            res.append(dict(x=round(x, 2), y=round(y, 2), ang=ang, m=round(m, 2), led=round(ml, 2), v1=v1, v2=v2, n1=in5(*p1), n2=in5(*p2)))
print(len(res), "placements pass the land check")
picks = []
res.sort(key=lambda r: (-(bool(r["v1"]) + bool(r["v2"])), -r["m"]))
for r in res:
    if all(math.dist((r["x"], r["y"]), (q["x"], q["y"])) > 1.5 for q in picks): picks.append(r)
for r in picks[:24]: print(r)
