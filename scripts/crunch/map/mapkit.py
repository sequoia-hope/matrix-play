#!/usr/bin/env python3
"""mapkit.py -- geometry of a matrix map: LED sites, lands by turn, nets, chip pins, trees, and per-LED turn choice.

A map CSV has ref, driver, sw, triplet, x_mm, y_mm, angle_deg and optionally turn. Turn k means KiCad orientation -angle_deg + 90k, as anodes_b does.
Footprint lands: 1 (-.4,-.4) 2 (.4,-.4) 3 (-.4,.4) 4 (.4,.4); 3 is the anode, 4/2/1 are CS 3t-2, 3t-1, 3t.
"""
import csv, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sunflower import CS_PINS, pin_xy, CHIP

LOCAL = {1: (-.4, -.4), 2: (.4, -.4), 3: (-.4, .4), 4: (.4, .4)}


def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r["driver"] = int(r["driver"]); r["sw"] = int(r["sw"]); r["triplet"] = int(r["triplet"])
        r["x"] = float(r["x_mm"]); r["y"] = float(r["y_mm"]); r["a"] = float(r["angle_deg"]); r["turn"] = int(r.get("turn") or 0)
    return rows


def save(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ref", "driver", "sw", "triplet", "x_mm", "y_mm", "angle_deg", "turn"])
        for r in sorted(rows, key=lambda r: int(r["ref"][1:])):
            w.writerow([r["ref"], r["driver"], r["sw"], r["triplet"], r["x_mm"], r["y_mm"], r["angle_deg"], r["turn"]])


def pad_xy(r, pad, turn=None):
    k = r["turn"] if turn is None else turn
    a = math.radians(r["a"]-90*k); c, s = math.cos(a), math.sin(a); lx, ly = LOCAL[pad]
    return (r["x"]+lx*c-ly*s, r["y"]+lx*s+ly*c)


def cs_pin(driver, triplet, i):
    """i 0, 1, 2 for pads 4, 2, 1."""
    return pin_xy(driver, CS_PINS[3*(triplet-1)+i])


def sw_pin(driver, sw):
    return pin_xy(driver, 15+sw)


def mst_len(pts, edges=None):
    n = len(pts); seen = [False]*n; d = [1e9]*n; par = [-1]*n; d[0] = 0; tot = 0
    for _ in range(n):
        u = min((i for i in range(n) if not seen[i]), key=lambda i: d[i]); seen[u] = True; tot += d[u]
        if edges is not None and par[u] >= 0:
            edges.append((par[u], u))
        ux, uy = pts[u]
        for v in range(n):
            if not seen[v]:
                w = math.hypot(ux-pts[v][0], uy-pts[v][1])
                if w < d[v]:
                    d[v] = w; par[v] = u
    return tot


CATH = (4, 2, 1)


def nets(rows):
    """{net key: list of (row, pad)}, plus the chip pin position per net."""
    out = {}; pin = {}
    for r in rows:
        for i, p in enumerate(CATH):
            k = ("cs", r["driver"], r["triplet"], i); out.setdefault(k, []).append((r, p)); pin[k] = cs_pin(r["driver"], r["triplet"], i)
        k = ("sw", r["driver"], r["sw"]); out.setdefault(k, []).append((r, 3)); pin[k] = sw_pin(r["driver"], r["sw"])
    return out, pin


def net_len(members, pin):
    return mst_len([pad_xy(r, p) for r, p in members]+[pin])


import os
PROBE = Path(__file__).resolve().parents[3]/"design/study/crunch/map"/os.environ.get("VIA_PROBE", "via_probe.json")


def via_cost(r, t, probe, stub=3.0, fan=15.0, blocked=30.0):
    """Price of an anode via for this site and turn, in mm of track: a stub takes room, a via in a chip's fan-out ring takes more."""
    key = min(probe, key=lambda s: math.dist(tuple(map(float, s.split(","))), (r["x"], r["y"]))) if "_k" not in r else r["_k"]
    r["_k"] = key
    a, b = probe[key][t]
    if a is not None:
        return stub*a
    if b is not None:
        return fan+stub*b
    return blocked


def optimise_turns(rows, sw_weight=1.0, sweeps=6, probe=None):
    """Coordinate descent on turn: tree length of every net at land positions, plus anode via fit. Returns (start, end) CS-only length."""
    ns, pin = nets(rows)
    of = {}
    for k, m in ns.items():
        for r, _ in m:
            of.setdefault(r["ref"], []).append(k)
    wt = lambda k: sw_weight if k[0] == "sw" else 1.0
    tot = lambda: sum(net_len(m, pin[k]) for k, m in ns.items() if k[0] == "cs")
    start = tot()
    for _ in range(sweeps):
        changed = 0
        for r in rows:
            best = None
            old = r["turn"]
            for t in range(4):
                r["turn"] = t
                c = sum(wt(k)*net_len(ns[k], pin[k]) for k in of[r["ref"]]) + (via_cost(r, t, probe) if probe else 0)
                if best is None or c < best[0]-1e-9:
                    best = (c, t)
            r["turn"] = best[1]; changed += best[1] != old
        if not changed:
            break
    return start, tot()


if __name__ == "__main__":
    rows = load(sys.argv[2])
    if sys.argv[1] == "turns":
        for r in rows:
            r["turn"] = 0
        import json
        print("CS tree at lands", optimise_turns(rows, probe=json.loads(PROBE.read_text()))); save(rows, sys.argv[3])
