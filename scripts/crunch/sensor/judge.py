#!/usr/bin/env python3
"""judge.py DIR [BASE_DIR]: refill zones and run DRC on DIR/round-pendant.kicad_pcb with DIR's own rules, in place on a copy; print opens, and error counts against BASE_DIR."""
import collections, json, shutil, subprocess, sys, tempfile
from pathlib import Path
import pcbnew
def run(d):
    d = Path(d); t = Path(tempfile.mkdtemp(dir=d)); c = t/"j.kicad_pcb"
    shutil.copy(d/"round-pendant.kicad_pcb", c); shutil.copy(d/"round-pendant.kicad_pro", t/"j.kicad_pro"); shutil.copy(d/"round-pendant.kicad_dru", t/"j.kicad_dru")
    b = pcbnew.LoadBoard(str(c)); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(c), b)
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(t/"d.json"), str(c)], capture_output=True)
    return json.load(open(t/"d.json")), b
d, b = run(sys.argv[1])
S = lambda ds: collections.Counter(v["type"] for v in ds["violations"])
print("unconnected", len(d["unconnected_items"]), [" / ".join(i["description"][:60] for i in u["items"]) for u in d["unconnected_items"]][:10])
print("errors", dict(S(d)))
if len(sys.argv) > 2:
    d0, _ = run(sys.argv[2])
    key = lambda v: (v["type"], v["description"], tuple(sorted(i["description"] for i in v["items"])))
    c0 = collections.Counter(key(v) for v in d0["violations"]); c1 = collections.Counter(key(v) for v in d["violations"])
    new = c1 - c0; gone = c0 - c1
    print("base unconnected", len(d0["unconnected_items"]), "base", dict(S(d0))); print("new", sum(new.values()), dict(collections.Counter(k[0] for k in new.elements())), "gone", sum(gone.values()))
    for k in list(new)[:40]:
        if not k[0].startswith("silk"): print("  NEW", k[0], k[1][:70], " | ".join(k[2])[:130])
