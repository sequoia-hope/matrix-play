#!/usr/bin/env python3
"""zoneclear.py IN OUT PLANE_MM [RP2350_MM]: set clearance of zones named plane* (built with KiCad's default 0.5 mm) and optionally the RP2350 ring and band, refill, report each fill."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); c = pcbnew.FromMM(float(sys.argv[3]))
r = pcbnew.FromMM(float(sys.argv[4])) if len(sys.argv) > 4 else None
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    if z.GetZoneName().startswith("plane"): z.SetLocalClearance(c)
    elif r is not None and z.GetZoneName().startswith("RP2350"): z.SetLocalClearance(r)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    for lid in z.GetLayerSet().Seq():
        ps = z.GetFilledPolysList(lid); print(z.GetZoneName(), b.GetLayerName(lid), "pieces", ps.OutlineCount(), "area", round(ps.Area()/1e12, 1))
pcbnew.SaveBoard(sys.argv[2], b)
