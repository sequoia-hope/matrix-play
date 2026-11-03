#!/usr/bin/env python3
"""prune_zone_nets.py IN OUT NET...: drop tracks and vias on these nets that KiCad's own connectivity says aren't needed, because a zone already joins what they join. The router doesn't count zones on routing layers, so it double-wires them.
Removes one item at a time, keeping it out only if the board's open count doesn't rise. Unlocked items only. IN's folder needs that board's .kicad_pro."""
import sys, pcbnew
inp, out, *nets = sys.argv[1:]
b = pcbnew.LoadBoard(inp); um = pcbnew.ToMM
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity()
count = lambda: b.GetConnectivity().GetUnconnectedCount(False)
base = count(); print("open before", base)
keep = []
for n in nets:
    gone = 0; mmgone = 0.0; total = 0
    while True:
        items = [t for t in b.GetTracks() if t.GetNetname() == n and not t.IsLocked()]
        total = max(total, len(items)); changed = 0
        # Inner-layer copper first, then vias, then B.Cu: that's what the double wiring costs.
        items.sort(key=lambda t: (isinstance(t, pcbnew.PCB_VIA), t.GetLayerName() == "B.Cu"))
        for t in items:
            L = 0 if isinstance(t, pcbnew.PCB_VIA) else um(t.GetLength())
            keep.append(t); b.Remove(t); b.BuildConnectivity()
            if count() > base:
                b.Add(t); b.BuildConnectivity()
            else:
                gone += 1; mmgone += L; changed += 1
        if not changed: break
    items = range(total)
    print(n, "items", len(items), "removed", gone, "mm", round(mmgone, 1))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.BuildConnectivity(); print("open after", count())
pcbnew.SaveBoard(out, b)
import os; sys.stdout.flush(); os._exit(0)
