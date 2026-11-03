#!/usr/bin/env python3
"""ERC summary plus netlist sanity for the matrix. Usage: check_sch.py <scratch dir>"""
import collections, json, subprocess, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
HW = Path(__file__).resolve().parents[1] / f"hw/round-pendant/{VARIANT}"
sp = Path(sys.argv[1]); sch = HW / "round-pendant.kicad_sch"
subprocess.run(["kicad-cli", "sch", "erc", "--severity-all", "--format", "json", "-o", sp / "erc.json", sch], capture_output=True)
c = collections.Counter()
for s in json.load(open(sp / "erc.json"))["sheets"]:
    for v in s["violations"]:
        c[(v["severity"], v["type"])] += 1
        if v["type"] != "footprint_link_issues":
            print(s["path"], v["description"], [(i["description"], i.get("pos")) for i in v["items"]][:2])
print(dict(c))
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", sp / "nl.xml", sch], capture_output=True)
r = ET.parse(sp / "nl.xml").getroot()
nets = {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.findall("node")] for n in r.find("nets")}
print(len(r.find("components")), "components", len(nets), "nets", dict(collections.Counter(x.get("ref")[0] for x in r.find("components"))))
for n in (1, 2):
    for i in range(1, 10):
        v = [k for k in nets if k.endswith(f"SW{n}_{i}")]
        assert len(v) == 1 and len(nets[v[0]]) == 14, (n, i, v)
    for i in range(1, 40):
        v = [k for k in nets if k.endswith(f"CS{n}_{i}")]
        assert len(v) == 1 and len(nets[v[0]]) == 10, (n, i, v)
print("matrix ok: 18 SW nets of 13 LEDs + driver, 78 CS nets of 9 LEDs + driver")
for k, v in sorted(nets.items()):
    if "SW" in k.replace("SWCLK","").replace("SWDIO","") or "/CS" in k or k.startswith("CS") or k.startswith("unconnected"):
        continue
    print(k, len(v), v if len(v) <= 8 else str(v[:8]) + "...")
