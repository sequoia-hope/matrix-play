#!/usr/bin/env python3
"""undangle.py VARIANT: repeat: DRC, delete tracks and vias DRC calls dangling (never locked ones), and report. Then snap pad_joints failures."""
import json, re, subprocess, sys, math, os, tempfile
import pcbnew
V = sys.argv[1]; D = f"hw/round-pendant/{V}"; PCB = f"{D}/round-pendant.kicad_pcb"
def drc():
    o = f"{D}/drc.json"; subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "--severity-warning", "-o", o, PCB], capture_output=True); return json.load(open(o))
for it in range(6):
    d = drc(); dang = [v for v in d["violations"] if v["type"] in ("track_dangling",)]
    print("pass", it, "dangling", len(dang))
    if not dang: break
    code = "\n".join(["import pcbnew,json,sys", f"b=pcbnew.LoadBoard('{PCB}');n=0;keep=[]", "pos=json.loads(sys.argv[1])", "for t in list(b.GetTracks()):",
        "    if isinstance(t,pcbnew.PCB_VIA) or t.IsLocked(): continue", "    for x,y,net,ln,lay in pos:",
        "        s=t.GetStart();e=t.GetEnd()", "        if t.GetNetname().endswith(net) and t.GetLayerName()==lay and abs(pcbnew.ToMM(t.GetLength())-ln)<.001 and min(abs(s.x/1e6-x)+abs(s.y/1e6-y),abs(e.x/1e6-x)+abs(e.y/1e6-y),abs((s.x+e.x)/2e6-x)+abs((s.y+e.y)/2e6-y))<.03:",
        "            keep.append(t);b.Remove(t);n+=1;break", "print('removed',n)", "pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(sys.argv[2],b)", "import os;os._exit(0)"])
    pos = []
    for v in dang:
        i = v["items"][0]; net = re.search(r"\[([^\]]+)\]", i["description"]).group(1).split("/")[-1]; m = re.search(r"on (\S+), length ([0-9.]+) mm", i["description"]); pos.append((i["pos"]["x"], i["pos"]["y"], net, float(m.group(2)), m.group(1)))
    print(pos[:5]); r = subprocess.run([sys.executable, "-c", code, json.dumps(pos), PCB], capture_output=True, text=True); print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])
d = drc()
import collections; print(collections.Counter(v["type"] for v in d["violations"]).most_common(), "unconnected", len(d["unconnected_items"]))
