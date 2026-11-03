#!/usr/bin/env python3
"""channel_vias.py BOARD: test the claim that CS vias land in channels between LEDs and each corks F.Cu.
For each routed (unlocked) via: is it inside an LED pad of its net? Else, in the LED field (within 1.2 mm of an LED pad)?
Corked: a 0.1 track can't pass on F.Cu on at least one side: the gap from the via centre to the nearest foreign LED pad
on both of two opposite sides leaves under 0.275+0.09+0.1=0.465 mm."""
import collections, math, re, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pads = []
for f in b.GetFootprints():
    if f.GetReference().startswith("D"):
        for p in f.Pads():
            pads.append((p.GetEffectivePolygon(pcbnew.F_Cu), p.GetNetname(), p.GetPosition()))
c = collections.Counter()
for v in b.GetTracks():
    if v.Type() != pcbnew.PCB_VIA_T: continue
    n = v.GetNetname(); q = v.GetPosition()
    k = "CS" if re.search(r"/CS\d_\d+$", n) else "SW" if re.search(r"/SW\d_\d+$", n) else "other"
    lk = "locked" if v.IsLocked() else "routed"
    near = [(math.sqrt(poly.SquaredDistance(q)) / 1e6, m, cc) for poly, m, cc in pads if abs(cc.x - q.x) < 2.5e6 and abs(cc.y - q.y) < 2.5e6]
    if not near: c[k, lk, "outside LED field"] += 1; continue
    dmin = min(near, key=lambda t: t[0])
    if dmin[0] == 0 and dmin[1] == n: c[k, lk, "in own pad"] += 1; continue
    if dmin[0] > 1.2: c[k, lk, "outside LED field"] += 1; continue
    # room for a track between via and pads: look at pads within reach, by direction
    tight = [(cc.x - q.x, cc.y - q.y) for d, m, cc in near if d < .465 and m != n]
    cork = any(ax * bx + ay * by < 0 for i, (ax, ay) in enumerate(tight) for bx, by in tight[i + 1:])
    c[k, lk, "channel, corks F.Cu" if cork else "channel, track can pass"] += 1
for k, v in sorted(c.items()): print(k, v)
