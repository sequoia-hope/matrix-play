#!/usr/bin/env python3
"""transplant_nets.py SENSOR_BOARD ROUTED_BOARD OUT NET[,NET...]: take the placed board (all other copper exactly as it was) and replace only the named
nets' unlocked tracks and vias with ROUTED_BOARD's. Keeps a pass from rewriting nets it had no need to touch. Short net names match on the last path part."""
import sys
import pcbnew
pre, routed, out, names = sys.argv[1:5]; names = set(names.split(","))
match = lambda n: n in names or n.split("/")[-1] in names
b = pcbnew.LoadBoard(pre); r = pcbnew.LoadBoard(routed); rm = 0; add = 0
for t in list(b.GetTracks()):
    if match(t.GetNetname()) and not t.IsLocked(): b.Remove(t); rm += 1
V = pcbnew.VECTOR2I
locked = {(t.GetPosition().x, t.GetPosition().y, t.GetNetname()) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T}
for t in r.GetTracks():
    n = t.GetNetname()
    if not match(n): continue
    net = b.FindNet(n)
    if t.Type() == pcbnew.PCB_VIA_T:
        if (t.GetPosition().x, t.GetPosition().y, n) in locked: continue
        v = pcbnew.PCB_VIA(b); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth(pcbnew.F_Cu)); v.SetDrill(t.GetDrill()); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net.GetNetCode()); b.Add(v)
    else:
        q = pcbnew.PCB_TRACK(b); q.SetStart(t.GetStart()); q.SetEnd(t.GetEnd()); q.SetWidth(t.GetWidth()); q.SetLayer(t.GetLayer()); q.SetNetCode(net.GetNetCode()); b.Add(q)
    add += 1
pcbnew.SaveBoard(out, b); print("removed", rm, "added", add)
