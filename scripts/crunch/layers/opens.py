#!/usr/bin/env python3
"""opens.py DIR: opens by net kind, error kinds by net, and an open map (radius bands, side) from the rejudge DRC or autoroute.json."""
import sys, json, re, collections, pathlib, math
d = pathlib.Path(sys.argv[1]); j = d/"route"/"rejudge"/"drc.json"
v = json.loads(j.read_text()); kinds = collections.Counter(); byr = collections.Counter(); 
def kind(s):
    m = re.search(r"\[([^\]]*)\]", s); n = m.group(1) if m else "?"
    return "CS" if "/CS" in n else "SW" if re.search(r"/SW\d_", n) else n if n in ("GND", "VSYS", "+3V3", "+1V1", "VBAT", "VBUS") else "other"
pts = []
for u in v.get("unconnected_items", []):
    kinds[kind(u["items"][0]["description"])] += 1
    for i in u["items"][:1]:
        pos = i["pos"]; pts.append((pos["x"]-100, pos["y"]-100))
for x, y in pts: byr[min(int(math.hypot(x, y)/3)*3, 18)] += 1
print(d.name, "opens by kind", kinds.most_common()); print(" by radius band (mm)", sorted(byr.items()))
errs = collections.Counter()
for a in v["violations"]:
    if a["type"].startswith("silk"): continue
    m = [kind(i["description"]) for i in a["items"]]; errs[(a["type"], m[0] if m else "?")] += 1
print(" errors", errs.most_common(12))
for a in [a for a in v["violations"] if a["type"] == "track_width"][:3]: print("  ex:", a["description"][:90], a["items"][0]["description"][:80])
