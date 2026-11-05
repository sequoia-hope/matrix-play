#!/usr/bin/env python3
"""map_d.py -- 5-sector balanced LED matrix map for Variant D (5x IS31FL3745-CLS4-TR WLCSP-36).

Assigns the 235 physical LED sites (234 sunflower sites + center LED) to D1..D235:
  Driver 1 (U1,  D1..D47):    (-11.85,   1.80), orient   0 deg on B.Cu
  Driver 2 (U2,  D48..D94):   ( -3.50,  12.00), orient 180 deg on B.Cu
  Driver 3 (U10, D95..D141):  (-10.85,  -8.95), orient   0 deg on B.Cu
  Driver 4 (U11, D142..D188): (  9.80,  -9.10), orient   0 deg on B.Cu
  Driver 5 (U12, D189..D235): (  9.90,   0.90), orient   0 deg on B.Cu

Writes design/study/d/matrix_map.csv with columns:
  ref,driver,sw,triplet,x_mm,y_mm,angle_deg
"""
import csv
import math
import random
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "design/study/d/matrix_map.csv"

# (driver_idx, uref, cx, cy, bcu_orient_deg, first_led)
BGA_SPECS = [
    (1, "U1", -11.85, 1.80, 0.0, 1),
    (2, "U2", -3.50, 12.00, 0.0, 48),
    (3, "U10", -10.85, -8.95, 0.0, 95),
    (4, "U11", 9.80, -9.10, 0.0, 142),
    (5, "U12", 9.90, 0.90, 0.0, 189),
]

# Top-view F.Cu ball positions (mm from package center):
# row A..F -> y = -1.25 .. +1.25; col 1..6 -> x = -1.25 .. +1.25
def fcu_ball_xy(ball: str) -> tuple[float, float]:
    r = "ABCDEF".index(ball[0])
    c = int(ball[1]) - 1
    return ((c - 2.5) * 0.5, (r - 2.5) * 0.5)


def bcu_ball_xy(cx: float, cy: float, bcu_orient_deg: float, ball: str) -> tuple[float, float]:
    """Board (x, y) of a WLCSP-36 ball after Flip(LEFT_RIGHT) + SetOrientationDegrees(bcu_orient_deg).
    Verified against pcbnew 9: at SetOrientationDegrees(0.0) on B.Cu, F.Cu pad (fx, fy) sits at (+fx, -fy).
    """
    fx, fy = fcu_ball_xy(ball)
    bx0, by0 = fx, -fy
    a = math.radians(bcu_orient_deg)
    ca, sa = math.cos(a), math.sin(a)
    return (cx + bx0 * ca + by0 * sa, cy - bx0 * sa + by0 * ca)


SW_BALLS = {1: "A2", 2: "A4", 3: "A1", 4: "A5", 5: "B1", 6: "A6", 7: "C1", 8: "B6"}
CS_BALLS = {
    1: "B2", 2: "B3", 3: "C3",
    4: "C2", 5: "D2", 6: "D1",
    7: "E2", 8: "E1", 9: "F1",
    10: "F6", 11: "E6", 12: "D5",
    13: "D6", 14: "C4", 15: "C6",
    16: "C5", 17: "B4", 18: "B5",
}


def load_physical_sites() -> list[tuple[float, float, float]]:
    """Load the exact 234 sunflower sites from design/study/b/matrix_map.csv + center site (0.05, -0.65, 80.0)."""
    sites = []
    with (ROOT / "design/study/b/matrix_map.csv").open() as f:
        for r in csv.DictReader(f):
            sites.append((float(r["x_mm"]), float(r["y_mm"]), float(r["angle_deg"])))
    assert len(sites) == 234, len(sites)
    # Center 235th site from place_c() (SetOrientationDegrees(-80) => angle_deg = 80.0)
    sites.append((0.05, -0.65, 80.0))
    return sites


def mst_len(pts: list[tuple[float, float]]) -> float:
    n = len(pts)
    if n <= 1:
        return 0.0
    seen = [False] * n
    d = [1e9] * n
    d[0] = 0.0
    tot = 0.0
    for _ in range(n):
        u = -1
        best = 1e10
        for i in range(n):
            if not seen[i] and d[i] < best:
                best = d[i]
                u = i
        seen[u] = True
        tot += best
        ux, uy = pts[u]
        for v in range(n):
            if not seen[v]:
                w = math.hypot(ux - pts[v][0], uy - pts[v][1])
                if w < d[v]:
                    d[v] = w
    return tot


def solve_sector(sector_sites: list[tuple[float, float, float]], spec: tuple, seed: int = 42) -> list[tuple[int, int, tuple[float, float, float]]]:
    """Assign 47 physical sites in a sector to the 47 (row=0..5, col=0..7 minus (5,7)) cells of `spec`."""
    _, _, cx, cy, orient, _ = spec
    cells = [(r, c) for r in range(6) for c in range(7 if r == 5 else 8)]
    assert len(cells) == 47 and len(sector_sites) == 47

    sw_xy = {sw - 1: bcu_ball_xy(cx, cy, orient, SW_BALLS[sw]) for sw in range(1, 9)}
    tr_xy = {}
    for k in range(1, 7):
        bs = [bcu_ball_xy(cx, cy, orient, CS_BALLS[3 * k - j]) for j in (0, 1, 2)]
        tr_xy[k - 1] = (sum(p[0] for p in bs) / 3.0, sum(p[1] for p in bs) / 3.0)

    # Initial polar sort around BGA center: slice into 6 angular bands matched to triplet ball angles,
    # and sort radially within each band matched to SW distance/order.
    site_polar = sorted(sector_sites, key=lambda s: math.atan2(s[1] - cy, s[0] - cx))
    tr_order = sorted(range(6), key=lambda r: math.atan2(tr_xy[r][1] - cy, tr_xy[r][0] - cx))
    # Ensure row 5 (the 7-LED row) gets 7 sites and rows 0..4 get 8 sites.
    assign = [None] * 47  # cell index -> site
    cell_idx = {rc: idx for idx, rc in enumerate(cells)}
    pos = 0
    for r in tr_order:
        cnt = 7 if r == 5 else 8
        band = site_polar[pos : pos + cnt]
        pos += cnt
        band.sort(key=lambda s: math.hypot(s[0] - cx, s[1] - cy))
        for c, s in enumerate(band):
            assign[cell_idx[(r, c)]] = s

    sw_groups = [[cell_idx[(r, c)] for r in range(6) if (r, c) in cell_idx] for c in range(8)]
    tr_groups = [[cell_idx[(r, c)] for c in range(7 if r == 5 else 8)] for r in range(6)]

    def total_cost(arr) -> float:
        c_sw = sum(mst_len([sw_xy[c]] + [(arr[i][0], arr[i][1]) for i in sw_groups[c]]) for c in range(8))
        c_tr = sum(mst_len([tr_xy[r]] + [(arr[i][0], arr[i][1]) for i in tr_groups[r]]) for r in range(6))
        return c_sw + 2.5 * c_tr

    cur = total_cost(assign)
    init_cost = cur
    rnd = random.Random(seed)
    n_iters = 30000
    for step in range(n_iters):
        t = 2.0 * ((0.01 / 2.0) ** (step / n_iters))
        i = rnd.randrange(47)
        j = rnd.randrange(47)
        if i == j:
            continue
        assign[i], assign[j] = assign[j], assign[i]
        nxt = total_cost(assign)
        if nxt <= cur or rnd.random() < math.exp((cur - nxt) / t):
            cur = nxt
        else:
            assign[i], assign[j] = assign[j], assign[i]

    print(f"  {spec[1]}: sector MST cost {init_cost:.1f} -> {cur:.1f} mm")
    return [(cells[idx][0], cells[idx][1], assign[idx]) for idx in range(47)]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sites = load_physical_sites()
    pts = np.array([(s[0], s[1]) for s in sites])
    centers = np.repeat(np.array([(sp[2], sp[3]) for sp in BGA_SPECS]), 47, axis=0)
    cost = ((pts[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    ri, ci = linear_sum_assignment(cost)

    by_sec = [[] for _ in range(5)]
    for s_idx, col_idx in zip(ri, ci):
        by_sec[col_idx // 47].append(sites[s_idx])

    rows_out = []
    for sec_i, spec in enumerate(BGA_SPECS):
        drv_idx, uref, _, _, _, first_led = spec
        solved = solve_sector(by_sec[sec_i], spec, seed=100 + sec_i)
        # Schematic order in schematic_d.py: row=0..5, col=0..(6 if row==5 else 7) -> D{first_led + idx}
        solved.sort(key=lambda item: (item[0], item[1]))
        for k_off, (r, c, (x, y, ang)) in enumerate(solved):
            ref = f"D{first_led + k_off}"
            rows_out.append((ref, uref, f"SW{drv_idx}_{c + 1}", r + 1, f"{x:.4f}", f"{y:.4f}", f"{ang:.2f}"))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm", "angle_deg"])
        w.writerows(rows_out)
    print(f"wrote {OUT} ({len(rows_out)} LEDs)")


if __name__ == "__main__":
    main()
