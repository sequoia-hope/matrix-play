#!/usr/bin/env python3
"""survive.py VARIANT_DIR [seeded board name]: how much of the seeded copper the router kept; opens and errors by kind."""
import json, os, re, sys, collections, subprocess, tempfile
D = sys.argv[1]; here = os.path.dirname(os.path.abspath(__file__))
def dump(p):
    o = tempfile.mktemp(suffix=".json"); subprocess.run(["python3", here+"/dump.py", p, o], capture_output=True); return json.load(open(o))
s = dump(D+"/route/seeded.kicad_pcb"); j = json.load(open(D+"/route/autoroute.json")); run = j["runs"][0]; f = dump(D+f"/route/s{run['seed']}.kicad_pcb")
key = lambda t: (t["layer"], t["net"], *sorted(((round(t["x1"], 3), round(t["y1"], 3)), (round(t["x2"], 3), round(t["y2"], 3)))))
fs = collections.Counter(key(t) for t in f["tracks"])
un = [t for t in s["tracks"] if not t["locked"]]
tot = collections.Counter(); kept = collections.Counter(); ln = collections.Counter(); ll = collections.Counter()
import math
L = lambda t: math.hypot(t["x1"]-t["x2"], t["y1"]-t["y2"])
for t in un:
    tot[t["layer"]] += 1; ln[t["layer"]] += L(t)
    if fs[key(t)]: kept[t["layer"]] += 1; ll[t["layer"]] += L(t)
print("seeded segments kept unchanged:", {k: f"{kept[k]}/{tot[k]}, {ll[k]:.0f}/{ln[k]:.0f} mm" for k in tot})
print("seeded vias:", sum(not v["locked"] for v in s["vias"]), "kept", sum(1 for v in s["vias"] if not v["locked"] and any(abs(v["x"]-q["x"]) < 1e-3 and abs(v["y"]-q["y"]) < 1e-3 for q in f["vias"])))
print("final", run["open"], run["plane_open"], run["new_errors"], run["vias"])
ly = collections.Counter(); tn = lambda n: "CS" if "/CS" in n else "SW" if "/SW" in n else "other"
for t in f["tracks"]: ly[(t["layer"], tn(t["net"]))] += L(t)
print("mm by layer/class:", {f"{k[0]} {k[1]}": round(v) for k, v in sorted(ly.items())})
vc = collections.Counter(tn(v["net"]) if v["net"] not in ("GND", "VSYS", "+3V3") else "plane" for v in f["vias"]); print("vias by class", dict(vc))
print("opens", collections.Counter(tn(re.findall(r"\[(.*?)\]", x)[0]) for x in run["open_items"]))
print("other opens", collections.Counter(re.findall(r"\[(.*?)\]", x)[0] for x in run["open_items"] if tn(re.findall(r"\[(.*?)\]", x)[0]) == "other").most_common(30))
print("errors", collections.Counter(e.split("(")[-1] for e in run["error_items"]), collections.Counter(re.findall(r"\[(.*?)\]", e)[0] for e in run["error_items"]).most_common(8))
