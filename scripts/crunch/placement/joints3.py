#!/usr/bin/env python3
"""joints3.py BOARD JSON: for each pad pad_joints_fixed.py flags, add a track from the nearest own track end to the pad's centre, width 0.1 (its neck is then the track's width). Judge with DRC."""
import json, math, os, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM; bad = json.load(open(sys.argv[2])); ids = {b.GetLayerName(l): l for l in range(64)}
for r in bad:
    x, y = r["at"]; L = None; best = None
    for f in b.GetFootprints():
        for p in f.Pads():
            c = p.GetPosition()
            if p.GetNetname() == r["net"] and abs(um(c.x)-x) < .002 and abs(um(c.y)-y) < .002: L = "B.Cu" if p.IsOnLayer(ids["B.Cu"]) else "F.Cu"; pad = p
    for t in b.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == r["net"] and t.GetLayerName() == L:
            for e in (t.GetStart(), t.GetEnd()):
                d = math.hypot(um(e.x)-x, um(e.y)-y)
                if best is None or d < best[0]: best = (d, e)
    n = pcbnew.PCB_TRACK(b); n.SetStart(best[1]); n.SetEnd(pad.GetPosition()); n.SetWidth(pcbnew.FromMM(.1)); n.SetLayer(ids[L]); n.SetNetCode(pad.GetNetCode()); b.Add(n); print("joined", r["pad"], round(best[0], 3))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[1], b); sys.stdout.flush(); os._exit(0)
