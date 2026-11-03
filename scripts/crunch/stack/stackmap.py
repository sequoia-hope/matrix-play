#!/usr/bin/env python3
"""stackmap.py OUT.csv U1x,U1y,U1rot U2x,U2y,U2rot [--mode chip] [--turns] : the fan map of variant c (spiral_map build chip lsa) rebuilt for drivers on one half of the back.

Rot 0 means pins laid out as U1 is on the main board; 180 as U2 is there. Only pin positions and CHIP change; the shared scripts are monkeypatched, not edited.
"""
import argparse, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"crunch/map"))
import sunflower, spiral_map, mapkit
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("u1"); ap.add_argument("u2"); ap.add_argument("--mode", default="chip"); ap.add_argument("--k", type=float, default=0); ap.add_argument("--turns", action="store_true"); a = ap.parse_args()
C = {}
for n, s in ((1, a.u1), (2, a.u2)):
    x, y, r = [float(v) for v in s.split(",")]; C[n] = (x, y, r); sunflower.CHIP[n] = (x, y)
def pin_xy(n, p):
    if p <= 15: fx, fy = -3.4, -2.8+.4*(p-1)
    elif p <= 30: fx, fy = -2.8+.4*(p-16), 3.4
    elif p <= 45: fx, fy = 3.4, 2.8-.4*(p-31)
    else: fx, fy = 2.8-.4*(p-46), -3.4
    cx, cy, r = C[n]
    return (cx+fx, cy-fy) if r == 0 else (cx-fx, cy+fy) if r == 180 else (cx+fy, cy+fx) if r == 90 else (cx-fy, cy-fx)
sunflower.pin_xy = spiral_map.pin_xy = mapkit.pin_xy = pin_xy
spiral_map.build(a.mode, a.k, "lsa", a.out)
if a.turns:
    rows = mapkit.load(a.out)
    for r in rows: r["turn"] = 0
    print("CS tree at lands", mapkit.optimise_turns(rows)); mapkit.save(rows, a.out)
