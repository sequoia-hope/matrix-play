#!/usr/bin/env python3
"""drc.py BOARD.kicad_pcb [OUT.json]: kicad-cli DRC summary, copper errors only (silk not counted)."""
import json, subprocess, sys, collections, tempfile, os
o = sys.argv[2] if len(sys.argv) > 2 else tempfile.mktemp(suffix=".json")
subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format", "json", "-o", o, sys.argv[1]], capture_output=True)
d = json.load(open(o)); c = collections.Counter(v["type"] for v in d["violations"])
print({k: v for k, v in c.items() if not k.startswith("silk")}, "unconnected", len(d["unconnected_items"]))
for v in d["violations"]:
    if not v["type"].startswith("silk"):
        print(" ", v["type"], " | ".join(i["description"][:48] for i in v["items"]), round(v["items"][0]["pos"]["x"]-100, 2), round(v["items"][0]["pos"]["y"]-100, 2))
