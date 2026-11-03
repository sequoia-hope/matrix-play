#!/usr/bin/env python3
"""netdiff.py BASE.kicad_pcb OUT.kicad_pcb [JSON]: per-net comparison of routed copper. A net counts as moved if the area of its copper
(per layer, capsules and via discs) differs by more than AREA mm2. Prints moved nets, via changes, and LIGHT's length, layers and neighbours' count."""
import collections, json, sys
import pcbnew
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
AREA = .01
def load(p):
    b = pcbnew.LoadBoard(p); d = collections.defaultdict(lambda: collections.defaultdict(list)); via = collections.defaultdict(set); ln = collections.Counter()
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.Type() == pcbnew.PCB_VIA_T:
            via[n].add((t.GetPosition().x//1000, t.GetPosition().y//1000))
        else:
            d[n][t.GetLayerName()].append(LineString([(t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6+1e-7, t.GetEnd().y/1e6)]).buffer(t.GetWidth()/2e6, 8)); ln[n] += t.GetLength()/1e6
    return b, d, via, ln
_, a, va, la = load(sys.argv[1]); _, c, vc, lc = load(sys.argv[2])
moved = {}
for n in set(a) | set(c):
    tot = 0
    for l in set(a[n]) | set(c[n]):
        A = unary_union(a[n][l]) if a[n][l] else None; B = unary_union(c[n][l]) if c[n][l] else None
        if A is None or B is None: tot += (A or B).area
        else: tot += A.symmetric_difference(B).area
    if tot > AREA or va[n] != vc[n]:
        moved[n] = dict(area=round(tot, 3), len=(round(la[n], 2), round(lc[n], 2)), vias=(len(va[n]), len(vc[n])))
print(len(moved), "nets moved of", len(set(a) | set(c)))
for n, m in sorted(moved.items(), key=lambda t: -t[1]["area"]): print(" ", n.split("/")[-1], m)
print("vias total", sum(map(len, va.values())), "->", sum(map(len, vc.values())))
if len(sys.argv) > 3: json.dump(moved, open(sys.argv[3], "w"))
