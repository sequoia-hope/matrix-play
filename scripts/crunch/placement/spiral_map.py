#!/usr/bin/env python3
"""spiral_map.py -- variant b matrix map along the sunflower's own spirals: SW nets follow one wind, triplets the other.

Golden-angle points n and n+d sit on a clockwise spiral for d in 8, 21 and an anticlockwise one for d in 5, 13, 34. Whichever is nearest gives each site's
local direction for that wind. Annealing is sunflower.solve's, but an edge across the wind costs up to (1+alpha) times its length.

    spiral_map.py score CSV                    crossings and alignment of an existing map
    spiral_map.py solve ALPHA SWAP SEED OUT    annealed map; SWAP 1 puts SW on the clockwise wind instead
    spiral_map.py build MODE K PINS OUT        constructed map: MODE spiral (log spirals, wind K), xy or chip (polar round the driver); PINS lsa or order

Sites, the driver split and refs' cell formula are sunflower.py's. Deterministic.
"""
import csv, math, random, sys
from pathlib import Path
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, str(Path(__file__).parent))
from sunflower import lattice, nudge, CS_PINS, pin_xy, CHIP

CW, CCW = (8, 21), (5, 13, 34)
SW_PINS = [15+i for i in range(1, 10)]


def sites():
    """(x, y, angle) keyed by lattice index, with wind tangents for each."""
    pts = lattice(); nudge(pts)
    def tangent(i, ds):
        best = None
        for d in ds:
            for j in (i-d, i+d):
                if 0 <= j < len(pts):
                    v = (pts[j][0]-pts[i][0], pts[j][1]-pts[i][1]); n = math.hypot(*v)
                    if best is None or n < best[0]:
                        best = (n, v[0]/n, v[1]/n)
        return best[1:]
    return [dict(i=i, x=p[0], y=p[1], a=p[2], cw=tangent(i, CW), ccw=tangent(i, CCW)) for i, p in enumerate(pts)]


def across(a, b, wind):
    """0 along the wind at both ends, 1 straight across it."""
    d = math.hypot(a["x"]-b["x"], a["y"]-b["y"]) or 1e-9
    ux, uy = (b["x"]-a["x"])/d, (b["y"]-a["y"])/d
    return 1-(abs(ux*a[wind][0]+uy*a[wind][1])+abs(ux*b[wind][0]+uy*b[wind][1]))/2


def mst(pts, wind, alpha):
    n = len(pts); seen = [False]*n; d = [1e9]*n; d[0] = 0; tot = 0
    for _ in range(n):
        u = min((i for i in range(n) if not seen[i]), key=lambda i: d[i]); seen[u] = True; tot += d[u]
        for v in range(n):
            if not seen[v]:
                w = math.hypot(pts[u]["x"]-pts[v]["x"], pts[u]["y"]-pts[v]["y"])*(1+alpha*across(pts[u], pts[v], wind))
                if w < d[v]: d[v] = w
    return tot


def solve_half(half, wsw, wt, alpha, seed, iters):
    rnd = random.Random(seed)
    order = sorted(half, key=lambda s: (round(s["x"]/2), s["y"]))
    grid = {}
    for t in range(13):
        run = sorted(order[t*9:t*9+9], key=lambda s: s["y"])
        for sw in range(9):
            grid[(t, sw)] = run[sw]
    c_sw = lambda sw: mst([grid[(t, sw)] for t in range(13)], wsw, alpha)
    c_t = lambda t: 3*mst([grid[(t, sw)] for sw in range(9)], wt, alpha)
    csw = [c_sw(i) for i in range(9)]; ct = [c_t(i) for i in range(13)]
    for i in range(iters):
        T = 4.0*(1-i/iters)+.01
        if rnd.random() < .5:
            t = rnd.randrange(13); a, b = rnd.sample(range(9), 2); p, q = (t, a), (t, b)
            grid[p], grid[q] = grid[q], grid[p]
            n = (c_t(t), c_sw(a), c_sw(b)); d = sum(n)-ct[t]-csw[a]-csw[b]
            if d <= 0 or rnd.random() < math.exp(-d/T):
                ct[t], csw[a], csw[b] = n
            else:
                grid[p], grid[q] = grid[q], grid[p]
        else:
            sw = rnd.randrange(9); a, b = rnd.sample(range(13), 2); p, q = (a, sw), (b, sw)
            grid[p], grid[q] = grid[q], grid[p]
            n = (c_sw(sw), c_t(a), c_t(b)); d = sum(n)-csw[sw]-ct[a]-ct[b]
            if d <= 0 or rnd.random() < math.exp(-d/T):
                csw[sw], ct[a], ct[b] = n
            else:
                grid[p], grid[q] = grid[q], grid[p]
    return grid


def assign(n, groups, pin_groups):
    """Nets to chip pins, least total distance from each net's centroid."""
    cost = []
    for ps in groups:
        mx, my = sum(p["x"] for p in ps)/len(ps), sum(p["y"] for p in ps)/len(ps)
        cost.append([sum(math.hypot(q[0]-mx, q[1]-my) for q in (pin_xy(n, pn) for pn in pg))/len(pg) for pg in pin_groups])
    r_, c_ = linear_sum_assignment(cost)
    return {int(i): int(j) for i, j in zip(r_, c_)}


def solve(alpha, swap, seed, out, iters=200000):
    all_ = sorted(sites(), key=lambda s: (s["x"], s["y"], s["a"]))
    wsw, wt = ("cw", "ccw") if swap else ("ccw", "cw")
    rows = []
    for n, half, first in ((1, all_[:117], 1), (2, all_[117:], 118)):
        grid = solve_half(half, wsw, wt, alpha, seed*n, iters)
        trip = assign(n, [[grid[(t, s)] for s in range(9)] for t in range(13)], [CS_PINS[3*k:3*k+3] for k in range(13)])
        sw = assign(n, [[grid[(t, s)] for t in range(13)] for s in range(9)], [[p] for p in SW_PINS])
        for (t, s), p in grid.items():
            rows.append((f"D{first+trip[t]*9+sw[s]}", n, sw[s]+1, trip[t]+1, round(p["x"], 4), round(p["y"], 4), round(math.degrees(p["a"]), 3)))
    rows.sort(key=lambda r: int(r[0][1:]))
    assert len({r[0] for r in rows}) == 234
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm", "angle_deg"]); w.writerows(rows)


def coords(p, n, mode, k):
    """(strip coordinate, rank coordinate) of a site for driver n. Same-family nets can't tangle when these are sorted in turn."""
    if mode == "xy":
        return p["x"], p["y"]
    if mode == "chip":
        cx, cy = CHIP[n]
        t = math.atan2(p["y"]-cy, p["x"]-cx)
        return (t if n == 2 else (t+2*math.pi) % (2*math.pi)), math.hypot(p["x"]-cx, p["y"]-cy)
    t = math.atan2(p["y"], p["x"]); t = (t+2*math.pi) % (2*math.pi) if n == 1 else t
    lr = math.log(max(math.hypot(p["x"], p["y"]), .5))
    return t+k*lr, t-k*lr


def build(mode, k, trip_mode, out):
    """Strips of 9 by the first coordinate are triplets; rank along the second is SW. Pins: least distance, or in perimeter order."""
    all_ = sorted(sites(), key=lambda s: (s["x"], s["y"], s["a"]))
    rows = []
    for n, half, first in ((1, all_[:117], 1), (2, all_[117:], 118)):
        by = sorted(half, key=lambda s: coords(s, n, mode, k)[0])
        grid = {}
        for t in range(13):
            for r, p in enumerate(sorted(by[t*9:t*9+9], key=lambda s: coords(s, n, mode, k)[1])):
                grid[(t, r)] = p
        trips = [[grid[(t, s)] for s in range(9)] for t in range(13)]; sws = [[grid[(t, s)] for t in range(13)] for s in range(9)]
        pg = [CS_PINS[3*j:3*j+3] for j in range(13)]; ps = [[q] for q in SW_PINS]
        def cost(gs, pins, m):
            return sum(math.dist((sum(p["x"] for p in g)/len(g), sum(p["y"] for p in g)/len(g)), pin_xy(n, pins[m[i]][len(pins[m[i]])//2])) for i, g in enumerate(gs))
        def pick(gs, pins):
            if trip_mode == "lsa":
                return assign(n, gs, pins)
            return min(({i: i for i in range(len(gs))}, {i: len(gs)-1-i for i in range(len(gs))}), key=lambda m: cost(gs, pins, m))
        tm = pick(trips, pg); sm = pick(sws, ps)
        for (t, s), p in grid.items():
            rows.append((f"D{first+tm[t]*9+sm[s]}", n, sm[s]+1, tm[t]+1, round(p["x"], 4), round(p["y"], 4), round(math.degrees(p["a"]), 3)))
    rows.sort(key=lambda r: int(r[0][1:]))
    assert len({r[0] for r in rows}) == 234
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm", "angle_deg"]); w.writerows(rows)


def crosses(a, b, c, d):
    o = lambda p, q, r: (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    return o(a, b, c)*o(a, b, d) < 0 and o(c, d, a)*o(c, d, b) < 0


def tree(pts):
    """Euclidean MST edges of (x, y) points."""
    n = len(pts); seen = {0}; out = []
    while len(seen) < n:
        d, u, v = min((math.dist(pts[i], pts[j]), i, j) for i in seen for j in range(n) if j not in seen)
        seen.add(v); out.append((pts[u], pts[v]))
    return out


def score(path):
    rows = list(csv.DictReader(open(path)))
    table = {(round(s["x"], 3), round(s["y"], 3)): s for s in sites()}
    res = {}
    for kind, key, pins, mult in (("sw", "sw", lambda k: [SW_PINS[k-1]], 1), ("cs", "triplet", lambda k: CS_PINS[3*k-3:3*k], 3)):
        edges = []; length = 0
        for drv in ("1", "2"):
            for k in sorted({int(r[key]) for r in rows}):
                ps = [(float(r["x_mm"]), float(r["y_mm"])) for r in rows if r["driver"] == drv and int(r[key]) == k]
                t = tree(ps)
                pin = pin_xy(int(drv), pins(k)[len(pins(k))//2])
                near = min(ps, key=lambda p: math.dist(p, pin))
                t.append((near, pin))
                length += sum(math.dist(*e) for e in t)
                edges += [(drv, k, e) for e in t]
        x = sum(crosses(*edges[i][2], *edges[j][2]) for i in range(len(edges)) for j in range(i+1, len(edges)) if edges[i][:2] != edges[j][:2])
        res[kind] = dict(crossings=x*mult*(mult if kind == "cs" else 1), length=round(length*mult))
        # Cut load: nets through each radial ring and each spoke sector, peak.
    print(path, res, "total weighted crossings", sum(v["crossings"] for v in res.values()), "copper", sum(v["length"] for v in res.values()))


if __name__ == "__main__":
    if sys.argv[1] == "score":
        for p in sys.argv[2:]:
            score(p)
    elif sys.argv[1] == "build":
        build(sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5])
    else:
        solve(float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
