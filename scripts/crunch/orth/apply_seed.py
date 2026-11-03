#!/usr/bin/env python3
"""apply_seed.py BOARD_IN SEED.json BOARD_OUT [--lock]: add seed.py's copper to a board as unlocked (or locked) tracks and vias."""
import json, sys
import pcbnew
OX, OY = 100.0, 100.0; mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1]); s = json.load(open(sys.argv[2])); lock = "--lock" in sys.argv
n = 0
for g in s["segs"]:
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(OX+g["x1"]), mm(OY+g["y1"]))); t.SetEnd(pcbnew.VECTOR2I(mm(OX+g["x2"]), mm(OY+g["y2"])))
    t.SetWidth(mm(g["w"])); t.SetLayer(b.GetLayerID(g["layer"])); t.SetNetCode(b.FindNet(g["net"]).GetNetCode()); t.SetLocked(lock); b.Add(t); n += 1
for v_ in s.get("vias", []):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(OX+v_["x"]), mm(OY+v_["y"]))); v.SetWidth(mm(v_.get("d", .25))); v.SetDrill(mm(v_.get("drill", .15)))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(b.FindNet(v_["net"]).GetNetCode()); v.SetLocked(lock); b.Add(v)
pcbnew.SaveBoard(sys.argv[3], b); print("laid", n, "tracks", len(s.get("vias", [])), "vias")
