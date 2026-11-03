#!/usr/bin/env python3
"""finish2.py VARIANT: vias DRC calls dangling are deleted if the board's open count stays the same (they cut copper for nothing)."""
import json, re, sys, pcbnew
V = sys.argv[1]; D = f"hw/round-pendant/{V}"; PCB = f"{D}/round-pendant.kicad_pcb"
b = pcbnew.LoadBoard(PCB); mm = pcbnew.FromMM; um = pcbnew.ToMM
fps = {f.GetReference(): f for f in b.GetFootprints()}; lid = {b.GetLayerName(l): l for l in range(64)}
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
count = lambda: b.GetConnectivity().GetUnconnectedCount(False); base = count(); print("open", base)
hold = []
for z in list(b.Zones()):
    if z.GetZoneName() == "U2 GND finger 8": hold.append(z); b.Remove(z); print("dropped U2 GND finger 8: on U2 pin 8 is VSYS (ADDR)")
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity(); base = count()
d = json.load(open(f"{D}/drc.json")); gone = 0; keep = []; stay = []
pos = [(v["items"][0]["pos"]["x"], v["items"][0]["pos"]["y"]) for v in d["violations"] if v["type"] == "via_dangling"]
for t in list(b.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = um(t.GetPosition().x), um(t.GetPosition().y)
        if any(abs(x-a) < .01 and abs(y-c) < .01 for a, c in pos):
            keep.append(t); b.Remove(t); b.BuildConnectivity()
            if count() > base: b.Add(t); b.BuildConnectivity(); stay.append(t.GetNetname())
            else: gone += 1
print("dangling vias removed", gone, "of", len(pos), "kept", stay)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(PCB, b)
import os; sys.stdout.flush(); os._exit(0)
