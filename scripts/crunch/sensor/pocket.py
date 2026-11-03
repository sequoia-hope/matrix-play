#!/usr/bin/env python3
"""pocket.py BOARD PINNET: candidate via spots near the ADC pins. Pads and existing vias count as fixed, tracks as movable.
For each spot prints the tracks (net, layer) a via there would need moved, fewest first."""
import collections, math, re, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); C = 100.
win = [float(v) for v in sys.argv[2:6]] if len(sys.argv) > 5 else [1.0, -6.6, 5.0, -3.6]
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        cx, cy = p.GetPosition().x/1e6-C, p.GetPosition().y/1e6-C
        if win[0]-2 < cx < win[2]+2 and win[1]-2 < cy < win[3]+2:
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(l): pads.append((p.GetEffectivePolygon(l), f.GetReference()+"."+p.GetNumber(), l))
vias = []; trk = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        vias.append((t.GetPosition().x/1e6-C, t.GetPosition().y/1e6-C, t.GetNetname()))
    else:
        trk.append((t.GetStart().x/1e6-C, t.GetStart().y/1e6-C, t.GetEnd().x/1e6-C, t.GetEnd().y/1e6-C, t.GetWidth()/1e6, t.GetLayerName(), t.GetNetname()))
zo = [(z, z.GetZoneName(), z.GetNetname()) for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu)]
out = []
x = win[0]
while x <= win[2]:
    y = win[1]
    while y <= win[3]:
        q = pcbnew.VECTOR2I(int((x+C)*1e6), int((y+C)*1e6)); ok = True
        for poly, name, l in pads:
            if poly.SquaredDistance(q) < (.275e6)**2 and not (name in ("U3.41", "U3.42", "U3.43")): ok = False; break
        if ok and any(math.hypot(x-a, y-c) < .40 for a, c, _ in vias): ok = False
        if ok:
            blk = collections.Counter()
            for x0, y0, x1, y1, w, l, n in trk:
                dx, dy = x1-x0, y1-y0; L = dx*dx+dy*dy or 1; u = max(0, min(1, ((x-x0)*dx+(y-y0)*dy)/L))
                if math.hypot(x0+u*dx-x, y0+u*dy-y) < .275+w/2: blk[(l, n.split("/")[-1])] += 1
            zz = [nm for z, nm, n in zo if z.GetFilledPolysList(pcbnew.B_Cu).Contains(q)]
            out.append((len(blk), round(x, 2), round(y, 2), sorted(blk), zz))
        y += .05
    x += .05
out.sort(key=lambda r: r[0])
print(len(out), "spots clear of pads and vias")
seen = set()
for r in out:
    k = tuple(r[3])
    if k in seen: continue
    seen.add(k); print(r)
    if len(seen) > 14: break
