#!/usr/bin/env python3
"""closure.py PLACED_DIR ROUTED_DIR OUT_DIR BASE_DIR NET,NET...: transplant the named nets from the routed board, DRC, add every net in a new copper violation, repeat.
Prints each round. Finds the smallest set of nets a pass really needed to move. Never copies nets in EXCLUDE without saying."""
import collections, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
placed, routed, out, base, names = sys.argv[1:6]; names = set(names.split(","))
EXCL = set(os.environ.get("EXCLUDE", "/MCU/VREG_LX,+1V1,GND,+3V3,VSYS").split(","))
HERE = Path(__file__).parent; Path(out).mkdir(parents=True, exist_ok=True)
for s in (".kicad_pro", ".kicad_dru"): shutil.copy(Path(placed)/("round-pendant"+s), Path(out)/("round-pendant"+s))
DRC = """
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b)
"""
def drc(d):
    t = Path(tempfile.mkdtemp(dir=d)); c = t/"j.kicad_pcb"; shutil.copy(Path(d)/"round-pendant.kicad_pcb", c); shutil.copy(Path(d)/"round-pendant.kicad_pro", t/"j.kicad_pro"); shutil.copy(Path(d)/"round-pendant.kicad_dru", t/"j.kicad_dru")
    subprocess.run([sys.executable, "-c", DRC, str(c)], capture_output=True)
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(t/"d.json"), str(c)], capture_output=True)
    return json.load(open(t/"d.json"))
key = lambda v: (v["type"], v["description"], tuple(sorted(i["description"] for i in v["items"])))
c0 = collections.Counter(key(v) for v in drc(base)["violations"])
for rnd in range(12):
    subprocess.run([sys.executable, str(HERE/"transplant_nets.py"), str(Path(placed)/"round-pendant.kicad_pcb"), str(Path(routed)/"round-pendant.kicad_pcb"), str(Path(out)/"round-pendant.kicad_pcb"), ",".join(sorted(names))], capture_output=True)
    d = drc(out); new = collections.Counter(key(v) for v in d["violations"]) - c0
    cu = [k for k in new if not k[0].startswith("silk")]
    nets = set(); held = set()
    for k in cu:
        for desc in k[2]:
            m = re.search(r"\[(.*?)\]", desc)
            if m:
                n = m.group(1)
                if n in EXCL: held.add(n)
                elif n not in names: nets.add(n)
    print(f"round {rnd}: nets {len(names)}, unconnected {len(d['unconnected_items'])}, new copper errors {len(cu)}, adds {sorted(x.split('/')[-1] for x in nets)} held {sorted(held)}", flush=True)
    for u in d["unconnected_items"][:12]: print("   open", " / ".join(i["description"][:50] for i in u["items"]))
    if not nets:
        for k in cu: print("  ", k[0], k[1][:60], " | ".join(k[2])[:120])
        break
    names |= nets
print("final nets", sorted(names))
