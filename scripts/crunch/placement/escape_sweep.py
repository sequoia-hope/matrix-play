#!/usr/bin/env python3
"""escape_sweep.py BOARD CHIP DX_RANGE DY_RANGE [TURNS]: offline score of a QFN's position against the LED field: how many pins can drop a through via nearby.
A via can't land within 0.215 mm of a foreign LED pad on F.Cu, nor of another pin on B.Cu, and vias keep 0.34 mm apart. Greedy along the perimeter, which is a floor on the true matching.
Prints the best and worst offsets. Also prints the share of the board where a via can land at all."""
import sys, math, json, re
import numpy as np, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
ref = sys.argv[2]; rx = float(sys.argv[3]); ry = float(sys.argv[4]); turns = [int(t) for t in (sys.argv[5] if len(sys.argv) > 5 else "0").split(",")]
fps = {f.GetReference(): f for f in b.GetFootprints()}
L = []
for f in b.GetFootprints():
    if f.GetReference().startswith("D"):
        a = math.radians(-f.GetOrientationDegrees())
        for p in f.Pads():
            c = p.GetPosition(); L.append((mm(c.x)-100, mm(c.y)-100, math.cos(a), math.sin(a)))
L = np.array(L); H = .225
def led_clear(x, y, need=.215):
    dx = x-L[:, 0]; dy = y-L[:, 1]; near = (abs(dx) < 1) & (abs(dy) < 1)
    if not near.any(): return True
    u = np.abs(L[near, 2]*dx[near]+L[near, 3]*dy[near])-H; v = np.abs(-L[near, 3]*dx[near]+L[near, 2]*dy[near])-H
    return (np.hypot(np.maximum(u, 0), np.maximum(v, 0)) >= need).all()
# share of the disc open to a foreign via
g = np.arange(-18.5, 18.5, .1); ok = tot = 0
for x in g:
    for y in g:
        if x*x+y*y < 18.5**2:
            tot += 1; ok += led_clear(x, y)
print(f"share of disc where a foreign through via clears the LED pads: {ok/tot:.2f}")
U = fps[ref]; c0 = U.GetPosition(); cx0, cy0 = mm(c0.x)-100, mm(c0.y)-100
pins = []
for p in U.Pads():
    if p.GetNumber() in ("61", "") : continue
    c = p.GetPosition(); pins.append((int(p.GetNumber()), mm(c.x)-100-cx0, mm(c.y)-100-cy0, p.GetNetname()))
pins.sort()
others = []
for f in b.GetFootprints():
    r = f.GetReference()
    if r == ref or r.startswith("D"): continue
    for p in f.Pads():
        q = p.GetBoundingBox(); others.append((mm(q.GetLeft())-100, mm(q.GetTop())-100, mm(q.GetRight())-100, mm(q.GetBottom())-100))
others = np.array(others)
def score(dx, dy, t):
    th = math.radians(t); C, S = round(math.cos(th)), round(math.sin(th))
    pl = [(n, cx0+dx+C*px+S*py, cy0+dy-S*px+C*py, net) for n, px, py, net in pins]
    arr = np.array([(q[1], q[2]) for q in pl]); picked = []; got = 0; lost = []
    cx, cy = cx0+dx, cy0+dy
    for n, x, y, net in pl:
        if net == "GND" or "unconnected" in net: continue
        ox, oy = (x-cx), (y-cy); s = max(abs(ox), abs(oy)); ux, uy = (ox/s, 0) if abs(ox) >= abs(oy) else (0, oy/s)
        best = None
        for d in np.arange(.55, 1.5, .05):
            for w in np.arange(-.6, .61, .05):
                vx, vy = x+ux*d-uy*w, y+uy*d+ux*w
                if math.hypot(d, w) > 1.4 or vx*vx+vy*vy > 18.2**2: continue
                dd = np.hypot(np.maximum(np.abs(arr[:, 0]-vx)-.4, 0), np.maximum(np.abs(arr[:, 1]-vy)-.15, 0))
                if not led_clear(vx, vy): continue
                if any(math.hypot(vx-a, vy-c) < .34 for a, c in picked): continue
                ob = others
                if (np.hypot(np.maximum(np.maximum(ob[:, 0]-vx, vx-ob[:, 2]), 0), np.maximum(np.maximum(ob[:, 1]-vy, vy-ob[:, 3]), 0)) < .215).any(): continue
                k = math.hypot(d, w)
                if best is None or k < best[0]: best = (k, vx, vy)
        if best: picked.append(best[1:]); got += 1
        else: lost.append(n)
    return got, lost
res = []
for t in turns:
    for dx in np.arange(-rx, rx+.01, .2):
        for dy in np.arange(-ry, ry+.01, .2):
            g_, l = score(dx, dy, t); res.append((g_, round(dx, 1), round(dy, 1), t, l))
res.sort(key=lambda r: (-r[0], abs(r[1])+abs(r[2])))
print(ref, "here:", score(0, 0, 0)[0], "of", sum(1 for q in pins if q[3] != "GND" and "unconnected" not in q[3]))
for r in res[:6]: print("best", r[:4], "lost", r[4])
for r in res[-2:]: print("worst", r[:4])
