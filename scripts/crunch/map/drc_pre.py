#!/usr/bin/env python3
"""drc_pre.py VARIANT: KiCad DRC of a variant's board in its own folder (own rules), by violation type; lists any on F.Cu tracks or vias of CS nets."""
import collections, json, subprocess, sys, tempfile
from pathlib import Path
d = Path("hw/round-pendant")/sys.argv[1]
with tempfile.TemporaryDirectory() as t:
    out = Path(t)/"d.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(out), str(d/"round-pendant.kicad_pcb")], capture_output=True)
    r = json.loads(out.read_text())
print(sys.argv[1], collections.Counter(v["type"] for v in r["violations"]).most_common(), "unconnected", len(r["unconnected_items"]))
for v in r["violations"]:
    s = " | ".join(i["description"] for i in v["items"])
    if "/CS" in s and v["type"] != "track_dangling" and v["type"] != "via_dangling":
        print("  ", v["type"], s[:150])
