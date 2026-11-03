#!/usr/bin/env python3
"""Dump a board's geometry to JSON (mm from board centre): LEDs, pads, vias, tracks, zones. Usage: dump.py board.kicad_pcb out.json"""
import json, math, sys
import pcbnew
OX, OY = 100.0, 100.0
um = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
out = {"pads": [], "vias": [], "tracks": [], "fps": {}, "zones": []}
for f in b.GetFootprints():
    r = f.GetReference(); c = f.GetPosition()
    out["fps"][r] = dict(x=um(c.x)-OX, y=um(c.y)-OY, rot=f.GetOrientationDegrees(), back=f.IsFlipped(), locked=f.IsLocked())
    for p in f.Pads():
        c = p.GetPosition(); s = p.GetSize(); bb = p.GetBoundingBox()
        out["pads"].append(dict(ref=r, num=p.GetNumber(), net=p.GetNetname(), x=um(c.x)-OX, y=um(c.y)-OY, w=um(s.x), h=um(s.y),
            rot=p.GetOrientationDegrees(), shape=int(p.GetShape()), F=p.IsOnLayer(pcbnew.F_Cu), B=p.IsOnLayer(pcbnew.B_Cu),
            pth=p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH), drill=um(p.GetDrillSizeX()),
            l=um(bb.GetLeft())-OX, t=um(bb.GetTop())-OY, r=um(bb.GetRight())-OX, b=um(bb.GetBottom())-OY))
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        c = t.GetPosition()
        out["vias"].append(dict(x=um(c.x)-OX, y=um(c.y)-OY, net=t.GetNetname(), d=um(t.GetWidth(pcbnew.F_Cu)), drill=um(t.GetDrill()), locked=t.IsLocked()))
    else:
        s, e = t.GetStart(), t.GetEnd()
        out["tracks"].append(dict(x1=um(s.x)-OX, y1=um(s.y)-OY, x2=um(e.x)-OX, y2=um(e.y)-OY, w=um(t.GetWidth()), layer=b.GetLayerName(t.GetLayer()), net=t.GetNetname(), locked=t.IsLocked()))
for z in b.Zones():
    bb = z.GetBoundingBox()
    out["zones"].append(dict(name=z.GetZoneName(), net=z.GetNetname(), rule=z.GetIsRuleArea(), layers=[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
        l=um(bb.GetLeft())-OX, t=um(bb.GetTop())-OY, r=um(bb.GetRight())-OX, b=um(bb.GetBottom())-OY))
json.dump(out, open(sys.argv[2], "w"))
print(len(out["pads"]), "pads", len(out["vias"]), "vias", len(out["tracks"]), "tracks", len(out["zones"]), "zones")
