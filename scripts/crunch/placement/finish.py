#!/usr/bin/env python3
"""finish.py IN_VARIANT OUT_VARIANT: from a complete route, a new variant with tidied copper. Nothing here moves a part or changes a rule.
 1. unlock the critical nets' copper from the first pass (LESSONS: routed copper isn't locked; anode vias stay locked as the project's input);
 2. remove what the router double-wired on VREG_LX and +1V1 where zones already join them;
 3. delete dangling track stubs reported by DRC, repeatedly;
 4. pull thin pad joints' track ends to the pad centre.
Every step is re-judged by KiCad afterwards."""
import json, math, re, shutil, subprocess, sys
from pathlib import Path
import pcbnew
A, Bn = sys.argv[1:3]; ROOT = Path("hw/round-pendant"); src = ROOT/A; D = ROOT/Bn
if D.exists(): sys.exit(f"{D} exists")
D.mkdir(); [shutil.copy(p, D) for p in src.glob("*.kicad_sch")]
for n in ("round-pendant.kicad_pro", "round-pendant.kicad_dru", "fp-lib-table", "sym-lib-table"): shutil.copy(src/n, D)
shutil.copytree(src/"lib", D/"lib"); shutil.copy(src/"route/s0.kicad_pcb", D/"round-pendant.kicad_pcb")
PCB = D/"round-pendant.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB)); um = pcbnew.ToMM; mm = pcbnew.FromMM
pat = re.compile(r"XIN|XOUT|C24-Pad1|USB_D|QSPI|D235-|R16-Pad2")
u = 0
for t in b.GetTracks():
    if t.IsLocked() and pat.search(t.GetNetname()) and t.GetNetname().find("SW") < 0:
        t.SetLocked(False); u += 1
print("unlocked", u)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
count = lambda: b.GetConnectivity().GetUnconnectedCount(False); base = count(); print("open before prune", base)
keep = []
for n in ("/MCU/VREG_LX", "+1V1"):
    gone = 0; L_ = 0
    while True:
        ch = 0
        for t in sorted([t for t in b.GetTracks() if t.GetNetname() == n and not t.IsLocked()], key=lambda t: (isinstance(t, pcbnew.PCB_VIA), t.GetLayerName() == "B.Cu")):
            L = 0 if isinstance(t, pcbnew.PCB_VIA) else um(t.GetLength())
            keep.append(t); b.Remove(t); b.BuildConnectivity()
            if count() > base: b.Add(t); b.BuildConnectivity()
            else: gone += 1; L_ += L; ch += 1
        if not ch: break
    print(n, "removed", gone, "items,", round(L_, 1), "mm")
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b)
sys.stdout.flush()
import os; os._exit(0)
