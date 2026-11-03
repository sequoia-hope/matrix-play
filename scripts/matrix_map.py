#!/usr/bin/env python3
"""matrix_map.py -- which LED site each (driver, SW, triplet) cell takes. Each cell once; each driver takes one half of the disc.

Starts from a column snake (9 consecutive LEDs make a triplet; within a triplet SW goes by y), then anneals swaps
that keep every (SW, triplet) pair unique: swap two cells of one triplet, or two of one SW. Cost: tree length of
each SW net plus tree length of each triplet, with x distance in a triplet costing more, since triplets run in columns.
Writes design/study/matrix_map.csv. Deterministic.
"""
import csv, json, math, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
st = json.loads((ROOT / "design/study/sites.json").read_text())
sites = [tuple(s) for s in st["sites"]]

def mst(pts, wx=1.0):
    n = len(pts); seen = [False]*n; d = [1e9]*n; d[0] = 0; tot = 0
    for _ in range(n):
        u = min((i for i in range(n) if not seen[i]), key=lambda i: d[i]); seen[u] = True; tot += d[u]
        for v in range(n):
            if not seen[v]:
                w = abs(pts[u][0]-pts[v][0])*wx + abs(pts[u][1]-pts[v][1])
                if w < d[v]: d[v] = w
    return tot

def solve(half, seed, iters=150000):
    rnd = random.Random(seed)
    cols = sorted({s[0] for s in half})
    snake = []
    for k, x in enumerate(cols):
        snake += sorted([s for s in half if s[0] == x], key=lambda s: s[1], reverse=bool(k % 2))
    grid = {}
    for t in range(13):
        run = sorted(snake[t*9:t*9+9], key=lambda s: s[1])
        for sw in range(9):
            grid[(t, sw)] = run[sw]
    def cost_sw(sw): return mst([grid[(t, sw)] for t in range(13)])
    def cost_t(t): return mst([grid[(t, sw)] for sw in range(9)], wx=3.0)
    csw = [cost_sw(i) for i in range(9)]; ct = [cost_t(i) for i in range(13)]
    cur = sum(csw)+sum(ct); first = cur; T = 4.0
    for i in range(iters):
        T = 4.0*(1-i/iters)+.01
        if rnd.random() < .5:
            t = rnd.randrange(13); a, b = rnd.sample(range(9), 2); p, q = (t, a), (t, b)
            grid[p], grid[q] = grid[q], grid[p]
            n = (cost_t(t), cost_sw(a), cost_sw(b)); d = n[0]+n[1]+n[2]-ct[t]-csw[a]-csw[b]
            if d <= 0 or rnd.random() < math.exp(-d/T):
                ct[t], csw[a], csw[b] = n; cur += d
            else:
                grid[p], grid[q] = grid[q], grid[p]
        else:
            sw = rnd.randrange(9); a, b = rnd.sample(range(13), 2); p, q = (a, sw), (b, sw)
            grid[p], grid[q] = grid[q], grid[p]
            n = (cost_sw(sw), cost_t(a), cost_t(b)); d = n[0]+n[1]+n[2]-csw[sw]-ct[a]-ct[b]
            if d <= 0 or rnd.random() < math.exp(-d/T):
                csw[sw], ct[a], ct[b] = n; cur += d
            else:
                grid[p], grid[q] = grid[q], grid[p]
    return grid, first, cur, sum(csw), sum(ct)

ordered = sorted(sites, key=lambda s: (s[0], s[1]))
west, east = ordered[:117], ordered[117:]
CHIP = {1: (-11.4, 3.4), 2: (10.6, 3.4)}
rows = []
for n, half, first in ((1, west, 1), (2, east, 118)):
    grid, a, b, sw, t = solve(half, 7 * n)
    print(f"driver {n}: {len({x[0] for x in half})} columns, x {min(x[0] for x in half)}..{max(x[0] for x in half)}; cost {a:.0f} -> {b:.0f}, SW trees {sw:.0f} mm, triplet trees (x weighted) {t:.0f}")
    assert len(set(grid.values())) == 117
    # Number triplets so CS pins sit nearest their LEDs: assignment on pin-to-LED distance.
    from scipy.optimize import linear_sum_assignment
    cx0, cy0 = CHIP[n]
    CS_PINS = [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 1, 2, 3, 4, 5, 6]
    def pin_xy(p):
        if p <= 15: fx, fy = -3.4, -2.8 + .4*(p-1)
        elif p <= 30: fx, fy = -2.8 + .4*(p-16), 3.4
        elif p <= 45: fx, fy = 3.4, 2.8 - .4*(p-31)
        else: fx, fy = 2.8 - .4*(p-46), -3.4
        return (cx0 + fx, cy0 - fy) if n == 1 else (cx0 - fx, cy0 + fy)
    cost = []
    for tr in range(13):
        pts = [grid[(tr, s_)] for s_ in range(9)]
        mx, my = sum(p[0] for p in pts)/9, sum(p[1] for p in pts)/9
        row = []
        for k in range(13):
            ps = [pin_xy(CS_PINS[3*k+i]) for i in range(3)]
            row.append(sum(math.hypot(a-mx, c-my) for a, c in ps)/3)
        cost.append(row)
    r_, c_ = linear_sum_assignment(cost)
    print(f"driver {n}: mean pin-to-triplet distance {sum(cost[i][j] for i, j in zip(r_, c_))/13:.2f} mm")
    order = [None]*13
    for i, j in zip(r_, c_):
        order[j] = int(i)
    newt = {old: new for new, old in enumerate(order)}
    for (tr, sw_), s in grid.items():
        t2 = newt[tr]
        rows.append((f"D{first+t2*9+sw_}", n, sw_+1, t2+1, s[0], s[1]))
rows.sort(key=lambda r: int(r[0][1:]))
with open(ROOT / "design/study/matrix_map.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm"]); w.writerows(rows)
