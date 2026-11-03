#!/usr/bin/env python3
"""sunflower.py -- variant b: LED sites and matrix map. 234 LEDs on the turned golden-angle lattice (design/study/usb-offboard), buttons mirrored about north.

Each cell (driver, SW, triplet) takes one site, each driver one half of the disc. Annealing swaps keep every (SW, triplet) unique. Cost: tree
length of each SW net plus three times that of each triplet, which carries R, G and B. Writes design/study/b/matrix_map.csv and buttons.json. Deterministic.
"""
import csv, json, math, random
from pathlib import Path
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/b"
R, EDGE, LAND = 19.0, .35, .625
RMAX = R - EDGE - LAND*math.sqrt(2)
GA = math.pi*(3-5**.5)
ROT = math.radians(-82.75)
BUTTONS = {"SW1": (338.75, 17.38), "SW2": (201.25, 17.32)}
PEG_R, PEG_SPAN, PEG_GAP = .35, .9, .22    # EVQP7C01P land pattern 0.7 mm holes; JLC hole to copper 0.2

def lattice(skip=1):
    c = RMAX/math.sqrt(skip+234); pts = []
    for n in range(skip, skip+234):
        r, t = c*math.sqrt(n+.5), n*GA+ROT
        pts.append([r*math.cos(t), r*math.sin(t), t+math.radians(45)])
    return pts

def land_dist(p, x, y):
    c, s = math.cos(p[2]), math.sin(p[2]); dx, dy = x-p[0], y-p[1]
    u, v = abs(c*dx+s*dy)-LAND, abs(-s*dx+c*dy)-LAND
    return math.hypot(max(u, 0), max(v, 0))

def nudge(pts):
    """Move an LED straight away from a peg by what the peg needs: no LED is dropped."""
    moved = []
    for deg, rc in BUTTONS.values():
        t = math.radians(deg)
        for d in (-1, 1):
            hx, hy = (rc+d*PEG_SPAN)*math.cos(t), (rc+d*PEG_SPAN)*math.sin(t)
            for i, p in enumerate(pts):
                for _ in range(40):
                    g = land_dist(p, hx, hy)-PEG_R
                    if g >= PEG_GAP:
                        break
                    n = math.hypot(p[0]-hx, p[1]-hy); p[0] += (p[0]-hx)/n*.01; p[1] += (p[1]-hy)/n*.01
                    moved.append(i)
    return sorted(set(moved))

def mst(pts):
    n = len(pts); seen = [False]*n; d = [1e9]*n; d[0] = 0; tot = 0
    for _ in range(n):
        u = min((i for i in range(n) if not seen[i]), key=lambda i: d[i]); seen[u] = True; tot += d[u]
        for v in range(n):
            if not seen[v]:
                w = math.hypot(pts[u][0]-pts[v][0], pts[u][1]-pts[v][1])
                if w < d[v]: d[v] = w
    return tot

def solve(half, seed, iters=200000):
    rnd = random.Random(seed)
    order = sorted(half, key=lambda s: (round(s[0]/2), s[1]))
    grid = {}
    for t in range(13):
        run = sorted(order[t*9:t*9+9], key=lambda s: s[1])
        for sw in range(9):
            grid[(t, sw)] = run[sw]
    c_sw = lambda sw: mst([grid[(t, sw)] for t in range(13)])
    c_t = lambda t: 3*mst([grid[(t, sw)] for sw in range(9)])
    csw = [c_sw(i) for i in range(9)]; ct = [c_t(i) for i in range(13)]
    first = sum(csw)+sum(ct)
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
    return grid, first, sum(csw), sum(ct)

CHIP = {1: (-11.4, 3.4), 2: (10.6, 3.4)}
CS_PINS = [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 1, 2, 3, 4, 5, 6]

def pin_xy(n, p):
    if p <= 15: fx, fy = -3.4, -2.8+.4*(p-1)
    elif p <= 30: fx, fy = -2.8+.4*(p-16), 3.4
    elif p <= 45: fx, fy = 3.4, 2.8-.4*(p-31)
    else: fx, fy = 2.8-.4*(p-46), -3.4
    cx, cy = CHIP[n]
    return (cx+fx, cy-fy) if n == 1 else (cx-fx, cy+fy)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = lattice()
    moved = nudge(pts)
    print("LEDs nudged for pegs:", len(moved))
    sites = sorted(tuple(p) for p in pts)
    rows = []
    for n, half, first in ((1, sites[:117], 1), (2, sites[117:], 118)):
        grid, a, sw, t = solve(half, 7*n)
        print(f"driver {n}: cost {a:.0f}, SW trees {sw:.0f} mm, triplet trees x3 {t:.0f}")
        assert len(set(grid.values())) == 117
        cost = []
        for tr in range(13):
            ps = [grid[(tr, s_)] for s_ in range(9)]
            mx, my = sum(p[0] for p in ps)/9, sum(p[1] for p in ps)/9
            cost.append([sum(math.hypot(q[0]-mx, q[1]-my) for q in (pin_xy(n, CS_PINS[3*k+i]) for i in range(3)))/3 for k in range(13)])
        r_, c_ = linear_sum_assignment(cost)
        print(f"driver {n}: mean pin-to-triplet distance {sum(cost[i][j] for i, j in zip(r_, c_))/13:.2f} mm")
        new = {int(i): int(j) for i, j in zip(r_, c_)}
        for (tr, s_), s in grid.items():
            rows.append((f"D{first+new[tr]*9+s_}", n, s_+1, new[tr]+1, round(s[0], 4), round(s[1], 4), round(math.degrees(s[2]), 3)))
    rows.sort(key=lambda r: int(r[0][1:]))
    with open(OUT/"matrix_map.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm", "angle_deg"]); w.writerows(rows)
    (OUT/"buttons.json").write_text(json.dumps(BUTTONS))

if __name__ == "__main__":
    main()
