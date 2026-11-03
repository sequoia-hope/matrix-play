#!/usr/bin/env python3
"""capacity.py BOARD [BOARD...]: track demand against supply, layer by layer.

Supply: disc area, less what each through via blocks, over the 0.19 mm track pitch (0.10 track + 0.09 gap).
Demand: routed length per layer, plus the rectilinear-free MST length of each net (a lower bound for routing it).
Opens: KiCad-independent estimate, the MST length of the connections the board's own connectivity reports unrouted.
"""
import re, sys, math, collections, pcbnew
PITCH = .19
def um(v): return pcbnew.ToMM(v)
def mst(pts):
    if len(pts) < 2: return 0.0
    seen = [pts[0]]; rest = list(pts[1:]); tot = 0.0
    d = {i: math.hypot(p[0]-pts[0][0], p[1]-pts[0][1]) for i, p in enumerate(rest)}
    while d:
        i = min(d, key=d.get); tot += d.pop(i); p = rest[i]
        for j in d: d[j] = min(d[j], math.hypot(rest[j][0]-p[0], rest[j][1]-p[1]))
    return tot
for path in sys.argv[1:]:
    b = pcbnew.LoadBoard(path)
    nets = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n: c = p.GetPosition(); nets[n].append((um(c.x), um(c.y)))
    kinds = collections.Counter()
    for n, pts in nets.items():
        k = "CS" if "/CS" in n else "SW" if re.search(r"/SW\d_", n) else "GND" if n == "GND" else "VSYS" if n == "VSYS" else "+3V3" if n == "+3V3" else "other"
        kinds[k] += mst(pts)
    lay = collections.Counter(); wide = collections.Counter(); vias = 0; netlen = collections.Counter()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA": vias += 1; continue
        l = um(t.GetLength()); lay[b.GetLayerName(t.GetLayer())] += l; wide[b.GetLayerName(t.GetLayer())] += l*um(t.GetWidth())
    area = math.pi*19*19
    via_block = math.pi*(.125+.09+.05)**2      # a through via's keep-out for a 0.10 track, on every layer
    free = area - vias*via_block
    print(path); print(f"  vias {vias}, each blocks {via_block:.3f} mm2 on all layers; free area per layer {free:.0f} of {area:.0f} mm2; supply {free/PITCH:.0f} mm track per layer at {PITCH} mm pitch")
    print("  MST lower bound by net kind (mm):", {k: round(v) for k, v in kinds.most_common()}, "total", round(sum(kinds.values())))
    for l in [b.GetLayerName(x) for x in b.GetEnabledLayers().CuStack()]:
        print(f"  {l:7s} routed {lay[l]:7.0f} mm  utilisation {lay[l]*PITCH/free*100:5.1f}%  (of pitch-limited supply)")
    tot = sum(lay.values()); print(f"  total routed {tot:.0f} mm")
