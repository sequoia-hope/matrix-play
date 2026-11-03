#!/usr/bin/env python3
"""two_pass.py -- variant b routes the control and power nets first, then the LED matrix. ultraroute has no net order, so:

    two_pass.py strip  PRE OUT     scratch board: PRE with matrix pads, vias and stubs on no net, so only other nets route
    two_pass.py dump   ROUTED      JSON on stdout: tracks and vias on non-matrix nets
    two_pass.py merge  PRE JSON    add them to PRE, locked, so the matrix pass routes round them
"""
import json, re, sys
import pcbnew
MATRIX = re.compile(r"/(CS|SW)\d_\d+$")

def strip(pre, out):
    b = pcbnew.LoadBoard(pre); n = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            if MATRIX.search(p.GetNetname()):
                p.SetNetCode(0); n += 1
    for t in b.GetTracks():
        if MATRIX.search(t.GetNetname()):
            t.SetNetCode(0)
    pcbnew.SaveBoard(out, b); print("pads off net", n)

def dump(routed):
    b = pcbnew.LoadBoard(routed); out = []
    for t in b.GetTracks():
        if t.IsLocked() or not t.GetNetname() or MATRIX.search(t.GetNetname()):
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            out.append(dict(via=1, x=t.GetPosition().x, y=t.GetPosition().y, w=t.GetWidth(pcbnew.F_Cu), d=t.GetDrill(), net=t.GetNetname()))
        else:
            out.append(dict(x0=t.GetStart().x, y0=t.GetStart().y, x1=t.GetEnd().x, y1=t.GetEnd().y, w=t.GetWidth(), l=t.GetLayer(), net=t.GetNetname(), arc=t.Type() == pcbnew.PCB_ARC_T))
    print(json.dumps(out))

def merge(pre, js):
    b = pcbnew.LoadBoard(pre); V = pcbnew.VECTOR2I; n = 0
    for d in json.load(open(js)):
        net = b.FindNet(d["net"]).GetNetCode()
        if "via" in d:
            v = pcbnew.PCB_VIA(b); v.SetPosition(V(d["x"], d["y"])); v.SetWidth(d["w"]); v.SetDrill(d["d"]); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
        else:
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(d["x0"], d["y0"])); t.SetEnd(V(d["x1"], d["y1"])); t.SetWidth(d["w"]); t.SetLayer(d["l"]); t.SetNetCode(net); t.SetLocked(True); b.Add(t)
        n += 1
    pcbnew.SaveBoard(pre, b); print("merged", n)

if __name__ == "__main__":
    {"strip": strip, "dump": dump, "merge": merge}[sys.argv[1]](*sys.argv[2:])
