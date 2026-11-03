#!/usr/bin/env python3
"""score.py DIR PLANENETS [PLANE_CL RP_CL]: re-judge a routed board in its own folder with optional zone clearances. Copies board to DIR/route/ rejudge.kicad_pcb with DIR's .kicad_pro and .kicad_dru."""
import sys, json, shutil, subprocess, collections, pathlib
d = pathlib.Path(sys.argv[1]); nets = sys.argv[2].split(",")
r = d/"route"/"rejudge"; r.mkdir(exist_ok=True, parents=True)
for s in ("kicad_pro", "kicad_dru"): shutil.copy(d/f"round-pendant.{s}", r/f"round-pendant.{s}")
out = r/"round-pendant.kicad_pcb"
root = pathlib.Path(__file__).parent
if len(sys.argv) > 3:
    subprocess.run([sys.executable, str(root/"zoneclear.py"), str(d/"round-pendant.kicad_pcb"), str(out), sys.argv[3], *sys.argv[4:5]], capture_output=True)
else: shutil.copy(d/"round-pendant.kicad_pcb", out)
j = r/"drc.json"; subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "-o", str(j), str(out)], capture_output=True)
v = json.loads(j.read_text()); u = v.get("unconnected_items", [])
pl = [x for x in u if all(any(f"[{n}]" in i["description"] for n in nets) for i in x["items"])]
print(d.name, "open", len(u)-len(pl), "plane_open", len(pl), "violations", collections.Counter(a["type"] for a in v["violations"] if not a["type"].startswith("silk")).most_common(6))
