#!/usr/bin/env python3
"""blocked.py DIR: for each signal open, in rejudge/drc.json, say what it joins, how far apart, and how crowded the spot is (vias within 0.5 mm, B.Cu pad under it)."""
import sys, json, re, math, collections, pcbnew
d = sys.argv[1]; v = json.load(open(f"{d}/route/rejudge/drc.json")); b = pcbnew.LoadBoard(f"{d}/round-pendant.kicad_pcb"); um = pcbnew.ToMM
vias = [(um(t.GetPosition().x), um(t.GetPosition().y)) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
back = []
for f in b.GetFootprints():
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.B_Cu) and not f.GetReference().startswith("D"):
            bb = p.GetBoundingBox(); back.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom()), f.GetReference()))
c = collections.Counter(); rows = []
for u in v["unconnected_items"]:
    a = u["items"]
    if any(f"[{n}]" in a[0]["description"] for n in ("GND", "VSYS", "+3V3")): continue
    x0, y0 = a[0]["pos"]["x"], a[0]["pos"]["y"]; x1, y1 = a[-1]["pos"]["x"], a[-1]["pos"]["y"]
    L = math.hypot(x1-x0, y1-y0)
    n = sum(1 for q in vias if math.hypot(q[0]-x0, q[1]-y0) < .5)
    un = [bool(re.match(r"Pad", i["description"])) for i in a]
    ep = "pad-pad" if all(un) else "pad-copper" if any(un) else "copper-copper"
    near = min(((max(l-x0, 0, x0-r)**2+max(t-y0, 0, y0-g)**2)**.5, ref) for l, t, r, g, ref in back)
    c[ep] += 1; rows.append((round(L, 1), n, ep, near[1] if near[0] < .6 else "-", a[0]["description"][:44], a[-1]["description"][:44]))
print(c.most_common()); L = sorted(r[0] for r in rows); print("gap length quartiles", L[len(L)//4], L[len(L)//2], L[3*len(L)//4], "max", L[-1]); print("under B.Cu part", collections.Counter(r[3][:2] if r[3] != "-" else "-" for r in rows).most_common(8))
for r in sorted(rows, reverse=True)[:45]: print(r)
