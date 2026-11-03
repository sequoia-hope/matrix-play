#!/usr/bin/env python3
"""replane.py BOARD --gnd L --power L [--gnd2 L]: move plane zones on an existing 8-layer board (the shared 8L start). LX cut follows GND. Refills."""
import argparse, pcbnew
ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--gnd", required=True); ap.add_argument("--power", required=True); ap.add_argument("--gnd2", default=""); a = ap.parse_args()
b = pcbnew.LoadBoard(a.board); assert b.GetCopperLayerCount() == 8
lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
if a.gnd2:
    txt = open(a.board).read()
for z in b.Zones():
    n = z.GetZoneName()
    if n in ("plane VSYS", "plane 3V3"): z.SetLayer(lid[a.power])
    if n in ("plane GND", "LX no plane"): z.SetLayer(lid[a.gnd])
if a.gnd2:
    for z in list(b.Zones()):
        if z.GetZoneName() in ("plane GND", "LX no plane"):
            c = pcbnew.ZONE(z); c.SetLayer(lid[a.gnd2]); c.SetZoneName(z.GetZoneName() + " 2"); b.Add(c)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    for l in z.GetLayerSet().Seq():
        ps = z.GetFilledPolysList(l); print(z.GetZoneName(), b.GetLayerName(l), "pieces", ps.OutlineCount(), "area", round(ps.Area()/1e12, 1))
pcbnew.SaveBoard(a.board, b)
