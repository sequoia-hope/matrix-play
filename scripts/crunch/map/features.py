#!/usr/bin/env python3
"""features.py MAP.csv [TURNS.json]: cheap measures of a map, candidates for predicting routed open.

    cs, sw        tree length at lands, mm (all CS, all SW)
    cs_x, sw_x    crossings between tree edges of different nets, same family, weighted as spiral_map.score counts them only roughly
    near          tree length of CS nets within 6 mm of a chip centre
    long          CS tree edges over 2.6 mm
    groups        F.Cu groups: CS nets' land pieces after joining lands closer than 1.7 mm (each piece needs its own via or pin route)
    groups_near   of those, pieces whose centre lies within 6 mm of a chip centre
    cut           peak nets through a 2 mm grid cell if each tree edge is rasterised (demand peak)
    over          sum of grid cell demand above 8 tracks per cell
    over_near     the same within 6 mm of a chip centre
    pin_x         crossings between each net's last edge to its pin, near the chips
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import mapkit

U3 = (-1.4, -6.6)
CHIPS = [mapkit.CHIP[1], mapkit.CHIP[2], U3]


def near_chip(p, r=6):
    return min(math.dist(p, c) for c in CHIPS) < r


def crosses(a, b, c, d):
    o = lambda p, q, r: (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    return o(a, b, c)*o(a, b, d) < 0 and o(c, d, a)*o(c, d, b) < 0


def features(rows):
    ns, pin = mapkit.nets(rows)
    f = dict(cs=0.0, sw=0.0, near=0.0, long=0, groups=0, groups_near=0)
    edges = {"cs": [], "sw": []}; pin_edges = []
    cells = {}
    for k, m in ns.items():
        pts = [mapkit.pad_xy(r, p) for r, p in m]
        ed = []
        pts2 = pts+[pin[k]]
        tot = mapkit.mst_len(pts2, ed)
        f[k[0]] += tot
        for u, v in ed:
            a, b = pts2[u], pts2[v]; L = math.dist(a, b)
            ispin = u == len(pts) or v == len(pts)
            if ispin:
                pin_edges.append((k, a, b))
            else:
                edges[k[0]].append((k, a, b))
            if k[0] == "cs":
                if L > 2.6 and not ispin:
                    f["long"] += 1
                mid = ((a[0]+b[0])/2, (a[1]+b[1])/2)
                if near_chip(mid):
                    f["near"] += L
            n = max(1, int(L/.5))
            for i in range(n+1):
                x, y = a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n
                cells.setdefault((int(x//2), int(y//2)), set()).add((k, u, v))
        if k[0] == "cs":
            # Pieces joined by short land-to-land hops: each piece must leave F.Cu at least once.
            par = list(range(len(pts)))
            def find(i):
                while par[i] != i:
                    par[i] = par[par[i]]; i = par[i]
                return i
            for i in range(len(pts)):
                for j in range(i):
                    if math.dist(pts[i], pts[j]) < 1.7:
                        par[find(i)] = find(j)
            comp = {}
            for i in range(len(pts)):
                comp.setdefault(find(i), []).append(pts[i])
            f["groups"] += len(comp)
            f["groups_near"] += sum(near_chip((sum(p[0] for p in c)/len(c), sum(p[1] for p in c)/len(c))) for c in comp.values())
    for fam in edges:
        e = edges[fam]; x = 0
        for i in range(len(e)):
            for j in range(i):
                if e[i][0] != e[j][0] and crosses(e[i][1], e[i][2], e[j][1], e[j][2]):
                    x += 1
        f[fam+"_x"] = x
    x = 0
    for i in range(len(pin_edges)):
        for j in range(i):
            if crosses(pin_edges[i][1], pin_edges[i][2], pin_edges[j][1], pin_edges[j][2]):
                x += 1
    f["pin_x"] = x
    dem = {c: len(s) for c, s in cells.items()}
    f["cut"] = max(dem.values())
    f["over"] = sum(max(0, v-8) for v in dem.values())
    f["over_near"] = sum(max(0, v-8) for c, v in dem.items() if near_chip((c[0]*2+1, c[1]*2+1)))
    # Distinct triplets that have a land over each chip's exposed pad, or over its pad ring: all of those nets must leave on F.Cu.
    f["ep_nets"] = f["pads_nets"] = 0
    half = {0: 2.975, 1: 2.975, 2: 1.975}
    for c, ch in enumerate(CHIPS):
        ep, pa = set(), set()
        for r in rows:
            for p in mapkit.CATH:
                x, y = mapkit.pad_xy(r, p); d = max(abs(x-ch[0]), abs(y-ch[1]))
                k = (r["driver"], r["triplet"], p)
                if d < half[c]:
                    ep.add(k)
                elif d < 3.9:
                    pa.add(k)
        f["ep_nets"] += len(ep); f["pads_nets"] += len(pa)
    return {k: round(v, 1) for k, v in f.items()}


if __name__ == "__main__":
    rows = mapkit.load(sys.argv[1])
    if len(sys.argv) > 2:
        t = json.load(open(sys.argv[2]))
        for r in rows:
            r["turn"] = t[r["ref"]]
    print(json.dumps(features(rows)))
