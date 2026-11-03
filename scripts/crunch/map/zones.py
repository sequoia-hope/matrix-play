#!/usr/bin/env python3
"""zones.py BOARD AUTOROUTE_JSON: cathode land open rate by square zone round each chip: EP, pad ring, fan-out ring, outer, rest."""
import json, re, sys, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
ch = {"U1": ((-11.4, 3.4), 2.975), "U2": ((10.6, 3.4), 2.975), "U3": ((-1.4, -6.6), 1.975)}
def zone(x, y):
    best = "rest"
    for r, (c, ep) in ch.items():
        m = max(abs(x-c[0]), abs(y-c[1]))
        if m < ep: return r+" EP"
        if m < 3.9: return r+" pads"
        if m < 5.3: return r+" fan"
        if m < 7.5: best = r+" outer"
    return best
d = json.load(open(sys.argv[2])); run = d["runs"][d["best"]]
pat = re.compile(r"Pad (\S*) \[[^\]]*\] of (D\d+) on")
openp = set()
for o in run["open_items"]:
    openp |= {(m.group(2), m.group(1)) for m in pat.finditer(o)}
st = collections.defaultdict(lambda: [0, 0, 0, 0])
for f in b.GetFootprints():
    ref = f.GetReference()
    if not ref.startswith("D") or ref == "D235": continue
    for p in f.Pads():
        c = p.GetPosition(); z = zone(um(c.x)-100, um(c.y)-100)
        i = 2 if p.GetNumber() == "3" else 0
        st[z][i] += 1; st[z][i+1] += (ref, p.GetNumber()) in openp
for z in sorted(st):
    v = st[z]; print(f"{z:10s} cathode {v[1]:3d}/{v[0]:3d} = {100*v[1]/max(v[0],1):3.0f}%   anode {v[3]}/{v[2]}")
