#!/usr/bin/env python3
"""matrix_only.py VARIANT: a BOUND, not a design. Starting point with every part except the LEDs and two drivers deleted, and U3's zones and rule area gone. Whatever stays open here no back-side move can fix."""
import sys, pcbnew
V = sys.argv[1]
b = pcbnew.LoadBoard("hw/round-pendant/c/route/preroute.kicad_pcb")
n = 0
keep = []
for f in list(b.GetFootprints()):
    r = f.GetReference()
    if r in ("U1", "U2") or (r.startswith("D") and r != "D235"): continue
    keep.append(f); b.Remove(f); n += 1
for z in list(b.Zones()):
    if z.GetZoneName() in ("RP2350 band", "RP2350 ring", "LX no plane", "plane 3V3", "U3 no tracks inside pads"): keep.append(z); b.Remove(z)
print("removed parts", n, flush=True)
pcbnew.SaveBoard(f"hw/round-pendant/{V}/round-pendant.kicad_pcb", b)
print("saved", flush=True)
import os; os._exit(0)
