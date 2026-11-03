#!/usr/bin/env python3
"""opens.py BOARD AUTOROUTE_JSON: where a routed board's open connections are. Prints per-class counts, length, radius and chip-distance histograms."""
import json, math, re, sys, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
P = {}
for f in b.GetFootprints():
    for p in f.Pads():
        c = p.GetPosition(); P[(f.GetReference(), p.GetNumber())] = (um(c.x)-100, um(c.y)-100)
fps = {f.GetReference(): f for f in b.GetFootprints()}
chips = {r: (um(fps[r].GetPosition().x)-100, um(fps[r].GetPosition().y)-100) for r in ("U1", "U2", "U3")}
print(chips)
d = json.load(open(sys.argv[2])); r = d["runs"][d["best"]]
print({k: r[k] for k in ("open", "plane_open", "new_errors", "vias")})
pat = re.compile(r"Pad (\S*) \[([^\]]*)\] of (\S+) on")
cat = collections.Counter(); L = []; rad = collections.Counter(); chip_d = collections.Counter(); nets = collections.Counter(); per = collections.Counter(); pts = []
for o in r["open_items"]:
    its = o.split(" / ")
    m = [pat.search(i) for i in its]
    net = re.search(r"\[([^\]]*)\]", its[0]).group(1)
    kind = "CS" if "/CS" in net else "SW" if "/SW" in net else "other"
    nets[net.split("/")[-1]] += 1
    if not all(m):
        cat[kind+" track"] += 1; continue
    a, c = [P[(x.group(3), x.group(1))] for x in m]
    toc = any(x.group(3).startswith("U") for x in m)
    cat[kind+(" led-chip" if toc else " led-led")] += 1
    if kind == "other": continue
    L.append(round(math.dist(a, c), 1))
    mid = ((a[0]+c[0])/2, (a[1]+c[1])/2)
    rad[int(math.hypot(*mid)//3*3)] += 1
    for x in m:
        if x.group(3).startswith("D"):
            q = P[(x.group(3), x.group(1))]
            per[x.group(3)] += 1
            chip_d[int(min(math.dist(q, c_) for c_ in chips.values())//2*2)] += 1
            pts.append(q)
print(cat); print("len", sorted(L)); print("radius bins", sorted(rad.items())); print("LED pad distance to nearest chip", sorted(chip_d.items()))
print("nets", nets.most_common(30))
print("LEDs with >=2 open pads", sum(v >= 2 for v in per.values()), "distinct", len(per))
oth = [o[:100] for o in r["open_items"] if "/CS" not in o and "/SW" not in o]; print("\n".join(oth[:30]))
