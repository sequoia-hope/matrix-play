#!/usr/bin/env python3
"""chainmap.py -- maps whose triplets are chains of touching neighbours, so R, G and B can run LED to LED on F.Cu with few through vias.

    chainmap.py OUT.csv --sw 0.5 --step 2.2 --pen 6 --seed 1 [--split x|chip] [--iters 400000] [--zone 1.0]

Anneals (driver, SW, triplet) cells over the sunflower sites. Cost per triplet: 3 x tree of its 9 sites, where any tree edge over STEP mm pays PEN per mm more.
Cost per SW net: SW x tree of its 13 sites. --zw E,P,F charges a triplet per chip whose EP, pad ring or fan-out ring it touches, so those zones' LEDs bunch into few triplets.
Then pins by least distance and per-LED turns (mapkit.optimise_turns). Deterministic for a seed.
"""
import argparse, json, math, random, sys
from pathlib import Path
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, str(Path(__file__).parent))
import mapkit
from spiral_sites import sites
from sunflower import CHIP, CS_PINS, pin_xy

U3 = (-1.4, -6.6)
CHIPS = [CHIP[1], CHIP[2], U3]


def tree(pts, step, pen, zone):
    n = len(pts); seen = [False]*n; d = [1e9]*n; d[0] = 0; tot = 0.0
    for _ in range(n):
        u = -1; best = 1e18
        for i in range(n):
            if not seen[i] and d[i] < best:
                best = d[i]; u = i
        seen[u] = True; tot += d[u]
        ux, uy, _ = pts[u]
        for v in range(n):
            if not seen[v]:
                vx, vy, _ = pts[v]
                w = math.hypot(ux-vx, uy-vy)
                if w > step:
                    w += pen*(w-step)
                if w < d[v]:
                    d[v] = w
    return tot


def solve_half(half, a, seed):
    rnd = random.Random(seed)
    order = sorted(half, key=lambda s: (round(s[0]/2), s[1]))
    grid = {}
    for t in range(13):
        run = sorted(order[t*9:t*9+9], key=lambda s: s[1])
        for sw in range(9):
            grid[(t, sw)] = run[sw]
    def c_t(t):
        ps = [grid[(t, s)] for s in range(9)]
        return 3*tree(ps, a.step, a.pen, 0)+sum(a.zw[z] for z in range(len(a.zw)) for c in range(3) if any(p[2] >> (3*z+c) & 1 for p in ps))
    c_s = lambda s: a.sw*tree([grid[(t, s)] for t in range(13)], 99, 0, 0)
    ct = [c_t(t) for t in range(13)]; cs = [c_s(s) for s in range(9)]
    for i in range(a.iters):
        T = 4.0*(1-i/a.iters)**2+.005
        p = (rnd.randrange(13), rnd.randrange(9)); q = (rnd.randrange(13), rnd.randrange(9))
        if p == q:
            continue
        ts = {p[0], q[0]}; ss = {p[1], q[1]}
        grid[p], grid[q] = grid[q], grid[p]
        nt = {t: c_t(t) for t in ts}; ns = {s: c_s(s) for s in ss} if a.sw else {s: 0.0 for s in ss}
        d = sum(nt.values())-sum(ct[t] for t in ts)+sum(ns.values())-sum(cs[s] for s in ss)
        if d <= 0 or rnd.random() < math.exp(-d/T):
            for t, v in nt.items():
                ct[t] = v
            for s, v in ns.items():
                cs[s] = v
        else:
            grid[p], grid[q] = grid[q], grid[p]
    return grid


def assign(n, groups, pin_groups):
    cost = []
    for ps in groups:
        mx, my = sum(p[0] for p in ps)/len(ps), sum(p[1] for p in ps)/len(ps)
        cost.append([sum(math.hypot(q[0]-mx, q[1]-my) for q in (pin_xy(n, pn) for pn in pg))/len(pg) for pg in pin_groups])
    r_, c_ = linear_sum_assignment(cost)
    return {int(i): int(j) for i, j in zip(r_, c_)}


EP_HALF = (2.975, 2.975, 1.975)


def zones(x, y):
    """Bitmask: bit 3z+c set if this LED sits in zone z of chip c, by its centre with the land reach. z 0: over the exposed pad, 1: over the pad ring, 2: fan-out ring."""
    m = 0
    for c, ch in enumerate(CHIPS):
        d = max(abs(x-ch[0]), abs(y-ch[1]))
        if d < EP_HALF[c]+.2:
            m |= 1 << (3*0+c)
        elif d < 3.9+.2:
            m |= 1 << (3*1+c)
        elif d < 5.3+.2:
            m |= 1 << (3*2+c)
    return m


def split(all_, how):
    if how == "x":
        s = sorted(all_, key=lambda p: (p["x"], p["y"], p["a"]))
        return s[:117], s[117:]
    if how == "u3":
        # U3's EP and pad ring LEDs all on driver 1; driver 2 takes the same number back from the lowest x elsewhere.
        hot = lambda p: zones(p["x"], p["y"]) & ((1 << 2) | (1 << 5))
        s = sorted(all_, key=lambda p: (0 if hot(p) else 1, p["x"], p["y"], p["a"]))
        return s[:117], s[117:]
    # Equal shares by the difference of distance to the two chips: same size, boundary a curve.
    s = sorted(all_, key=lambda p: math.dist((p["x"], p["y"]), CHIP[1])-math.dist((p["x"], p["y"]), CHIP[2]))
    return s[:117], s[117:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--sw", type=float, default=.5); ap.add_argument("--step", type=float, default=2.2); ap.add_argument("--pen", type=float, default=6)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--iters", type=int, default=400000); ap.add_argument("--split", default="x")
    ap.add_argument("--zw", default="0,0,0", help="price per triplet per chip for touching zones EP, pad ring, fan-out")
    a = ap.parse_args(); a.zw = [float(v) for v in a.zw.split(",")]
    all_ = sites()
    h1, h2 = split(all_, a.split)
    rows = []
    for n, half, first in ((1, h1, 1), (2, h2, 118)):
        pts = []
        for p in half:
            pts.append((p["x"], p["y"], zones(p["x"], p["y"]), p["a"]))
        g3 = {}
        grid = solve_half([q[:3] for q in pts], a, a.seed*n)
        ang = {q[:3]: q[3] for q in pts}
        tm = assign(n, [[grid[(t, s)] for s in range(9)] for t in range(13)], [CS_PINS[3*k:3*k+3] for k in range(13)])
        sm = assign(n, [[grid[(t, s)] for t in range(13)] for s in range(9)], [[15+i] for i in range(1, 10)])
        for (t, s), p in grid.items():
            rows.append(dict(ref=f"D{first+tm[t]*9+sm[s]}", driver=n, sw=sm[s]+1, triplet=tm[t]+1, x=p[0], y=p[1], a=math.degrees(ang[p]),
                             x_mm=round(p[0], 4), y_mm=round(p[1], 4), angle_deg=round(math.degrees(ang[p]), 3), turn=0))
    probe = json.loads(mapkit.PROBE.read_text())
    print("CS tree at lands", mapkit.optimise_turns(rows, probe=probe))
    mapkit.save(rows, a.out)


if __name__ == "__main__":
    main()
