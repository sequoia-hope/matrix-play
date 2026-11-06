#!/usr/bin/env python3
"""apply_jst.py <variant> -- swap BT1's hand-solder pads for the JST GH socket on an already-routed sunflower board.

Steps: lib_gen + sch_gen (BT1 now SM02B-GHS-TB, C189893), pcb_gen sync (footprint replaced by reference), pcb_gen bat
(BT1 to BAT_POS), then strip the copper the new socket needs: every track or via of another net within 0.15 mm of its
pads, and the battery nets' copper inside a disc round the old pads and the new site. The board is saved as
route/pre_jst.kicad_pcb first. The re-route is route_variant.py --continue-plough with the printed --rip-region discs.
"""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sunflower"))
from config import BAT_POS, OX, OY, VARIANTS  # noqa: E402

PY = sys.executable
SF = ROOT / "scripts/sunflower"


def run(*a):
    r = subprocess.run([PY, *map(str, a)], capture_output=True, text=True)
    out = [l for l in (r.stdout + r.stderr).splitlines() if "Debug:" not in l]
    print("\n".join(out[-4:]), flush=True)
    if r.returncode:
        raise SystemExit(f"failed: {a}")


STRIP = r'''
import json, math, sys, os, pcbnew
pcb, old = sys.argv[1], json.loads(sys.argv[2])
OX = OY = 100.0
b = pcbnew.LoadBoard(pcb)
um = pcbnew.ToMM
bt = next(f for f in b.GetFootprints() if f.GetReference() == "BT1")
pads = list(bt.Pads())
bat = {"VBAT", "/Power/BAT_N"}
c = bt.GetPosition(); cx, cy = um(c.x) - OX, um(c.y) - OY
def near_pad(t):
    for p in pads:
        if not p.IsOnLayer(t.GetLayer()) and not isinstance(t, pcbnew.PCB_VIA):
            continue
        if p.GetNetname() and p.GetNetname() == t.GetNetname():
            continue
        clr = pcbnew.FromMM(0.15)
        if isinstance(t, pcbnew.PCB_VIA):
            sh = t.GetEffectiveShape(pcbnew.B_Cu)
        else:
            sh = t.GetEffectiveShape()
        if p.GetEffectiveShape(pcbnew.B_Cu).Collide(sh, clr):
            return True
    return False
gone = {"foreign": 0, "bat_old": 0, "bat_new": 0}
doomed = []
for t in b.GetTracks():
    is_via = isinstance(t, pcbnew.PCB_VIA)
    if is_via:
        mid = t.GetPosition()
    else:
        mid = (t.GetStart() + t.GetEnd()) / 2
    mx, my = um(mid.x) - OX, um(mid.y) - OY
    if (is_via or t.GetLayer() == pcbnew.B_Cu) and near_pad(t):
        doomed.append(t); gone["foreign"] += 1; continue
    if t.GetNetname() not in bat:
        continue
    ends = [t.GetPosition()] if is_via else [t.GetStart(), t.GetEnd()]
    if any(math.hypot(um(q.x) - OX - old[0], um(q.y) - OY - old[1]) < 3.2 for q in ends):
        doomed.append(t); gone["bat_old"] += 1
    elif (is_via or t.GetLayer() == pcbnew.B_Cu) and math.hypot(mx - cx, my - cy) < 4.0:
        doomed.append(t); gone["bat_new"] += 1
keep_alive = list(doomed)
for t in doomed:
    b.Remove(t)
pcbnew.SaveBoard(pcb, b)
print(json.dumps(gone), flush=True); os._exit(0)
'''


def main():
    v = sys.argv[1]
    spec = VARIANTS[v]
    hw = spec.hw_dir
    pcb = hw / "sunflower.kicad_pcb"
    pro = hw / "sunflower.kicad_pro"
    (hw / "route").mkdir(exist_ok=True)
    keep = hw / "route/pre_jst.kicad_pcb"
    if not keep.exists():
        shutil.copy2(pcb, keep)
    pro_bytes = pro.read_bytes()
    # Old BT1 position (pads were at the Variant D spot)
    old = json.loads(subprocess.run([PY, "-c", (
        "import pcbnew,json,os,sys;b=pcbnew.LoadBoard(sys.argv[1]);f=[f for f in b.GetFootprints() if f.GetReference()=='BT1'][0];"
        "p=f.GetPosition();print(json.dumps([pcbnew.ToMM(p.x)-100,pcbnew.ToMM(p.y)-100]),flush=True);os._exit(0)"), str(pcb)],
        capture_output=True, text=True).stdout.strip().splitlines()[-1])
    run(SF / "lib_gen.py", v)
    run(SF / "sch_gen.py", v)
    run(SF / "pcb_gen.py", v, "sync")
    run(SF / "pcb_gen.py", v, "bat")
    r = subprocess.run([PY, "-c", STRIP, str(pcb), json.dumps(old)], capture_output=True, text=True)
    print("stripped:", r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-800:], flush=True)
    pro.write_bytes(pro_bytes)
    x, y, _ = BAT_POS
    # route_variant's --rip-region takes KiCad coordinates
    print(f"rip regions: --rip-region {OX + x:.2f},{OY + y:.2f},4.5 --rip-region {OX + old[0]:.2f},{OY + old[1]:.2f},3.0")


if __name__ == "__main__":
    main()
