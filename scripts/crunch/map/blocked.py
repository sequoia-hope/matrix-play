#!/usr/bin/env python3
"""blocked.py [BOARD AUTOROUTE_JSON]: LED lands where the back side refuses a through via (static, via_probe.json); with a routed board, how often those lands stay open."""
import json, math, re, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import mapkit
P = json.loads(mapkit.PROBE.read_text())
chips = {"U1": (-11.4, 3.4), "U2": (10.6, 3.4), "U3": (-1.4, -6.6)}
hist = collections.Counter(); byz = collections.defaultdict(collections.Counter)
for s, v in P.items():
    x, y = map(float, s.split(","))
    n = sum(1 for a, b in v if b == 0)
    hist[n] += 1
    z = min(chips, key=lambda c: max(abs(x-chips[c][0]), abs(y-chips[c][1])))
    if max(abs(x-chips[z][0]), abs(y-chips[z][1])) > 5.5: z = "rest"
    byz[z][n] += 1
print("sites by lands where a via fits", sorted(hist.items()))
for z in sorted(byz): print(z, sorted(byz[z].items()))
if len(sys.argv) > 2:
    import pcbnew
    b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
    d = json.load(open(sys.argv[2])); run = d["runs"][d["best"]]
    pat = re.compile(r"Pad (\S*) \[[^\]]*\] of (D\d+) on")
    openp = collections.Counter()
    for o in run["open_items"]:
        for m in pat.finditer(o):
            openp[(m.group(2), m.group(1))] += 1
    st = collections.defaultdict(lambda: [0, 0])
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not ref.startswith("D") or ref == "D235": continue
        c = f.GetPosition(); x, y = um(c.x)-100, um(c.y)-100
        key = min(P, key=lambda s: math.dist(tuple(map(float, s.split(","))), (x, y)))
        n = sum(1 for a, b_ in P[key] if b_ == 0)
        st[n][0] += 3; st[n][1] += sum(1 for pn in ("1", "2", "4") if (ref, pn) in openp)
    print("cathode lands open, by LED's lands where a via fits:", {k: f"{v[1]}/{v[0]}" for k, v in sorted(st.items())})
