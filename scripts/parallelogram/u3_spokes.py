#!/usr/bin/env python3
"""u3_spokes.py -- give U3's 1V1 ring the reference spokes (chips/rp2350.md, "1V1 spokes").

U3 is on B.Cu, so the reference geometry is mirrored in y (pin 23 at -y, COUT at +y).
The far ends differ from the reference: LED pads on F.Cu sit where the reference puts
its vias beyond pins 6 and 39, so W/E/S end at the via already in each DVDD pin's pad.
The N spoke ends in the vendor +1V1 zone at COUT, as in the reference.

    u3_spokes.py apply IN.kicad_pcb OUT.kicad_pcb
        drop the thin 1V1 links (In2.Cu/F.Cu wires, 0.3 mm ring vias, B.Cu wire inside
        the ring, the F.Cu detour to C19), add four 0.6/0.25 ring vias, four 0.6 mm In2.Cu
        spokes, a 0.6/0.25 via at COUT, a B.Cu pin 23 -> C19 trace and an open B.Cu tie
        through the ring joining the ring vias; all new copper locked.
    u3_spokes.py strip BOARD.kicad_pcb DRC.json
        delete every non-1V1 track or via that a DRC clearance/short names together with
        the new spoke copper, so the router can lay those nets again.
    u3_spokes.py lock BOARD.kicad_pcb RADIUS_MM
        lock all copper farther than RADIUS_MM from U3, all +1V1 and the critical nets; unlock the rest.
"""
import json
import math
import re
import sys

import pcbnew

MM = pcbnew.FromMM
CRIT = re.compile(r"XIN|XOUT|C24-Pad1|USB_D|QSPI")  # route_variant.py's CRIT_PAT
NET = "+1V1"


_ORIGIN = {}


def u3_origin(b):
    """U3's centre, read once per board (after a Remove(), SWIG can hand back an untyped footprint)."""
    if id(b) not in _ORIGIN:
        c = b.FindFootprintByReference("U3").GetPosition()
        _ORIGIN[id(b)] = (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y))
    return _ORIGIN[id(b)]


def rel(b, p):
    cx, cy = u3_origin(b)
    return pcbnew.ToMM(p.x) - cx, pcbnew.ToMM(p.y) - cy


def absv(b, x, y):
    cx, cy = u3_origin(b)
    return pcbnew.VECTOR2I(MM(cx + x), MM(cy + y))


# Geometry relative to U3 (mm, KiCad frame, y down). Reference y mirrored.
# E moves 1.0 mm from the mirrored reference (2.15, 0.40): LED pad D102.3 is above it on F.Cu
# (gap -0.20 mm); (2.15, -0.60) is the nearest spot on that side of the ring with >= 0.15 mm.
RING_VIAS = {"N": (0.49, 2.15), "S": (0.20, -2.15), "W": (-2.15, 0.80), "E": (2.15, -0.60)}
PIN_VIAS = {"S": (0.013, -3.19), "W": (-3.188, 0.81), "E": (3.338, 0.41)}  # existing, in pads 23, 6, 39
COUT_VIA = (0.50, 5.00)  # reference (0.5, 5.2) is 0.1 mm from R14.2 (USB_DM); 5.0 clears it by 0.21
SPOKES = [  # In2.Cu, 0.6 mm
    [RING_VIAS["W"], PIN_VIAS["W"]],
    [RING_VIAS["E"], PIN_VIAS["E"]],
    [RING_VIAS["S"], PIN_VIAS["S"]],
    [RING_VIAS["N"], COUT_VIA],
]
# B.Cu tie through the ring joining the four ring vias, open (no loop): the ring zone joins them in
# KiCad, but ultraroute doesn't count it and lays its own 0.2 mm 1V1 links on In2.Cu instead.
RING_TIE = [(-1.95, 0.80), (-1.95, -1.95), (0.20, -1.95), (1.95, -1.95), (1.95, -0.60), (1.95, 1.95), (0.49, 1.95)]
RING_FEET = [((-1.95, 0.80), RING_VIAS["W"]), ((0.20, -1.95), RING_VIAS["S"]), ((1.95, -0.60), RING_VIAS["E"]), ((0.49, 1.95), RING_VIAS["N"])]
PIN23_C19 = [(0.0, -3.438), (0.0, -4.12), (0.40, -4.52), (0.40, -5.02)]  # B.Cu 0.2 mm


def near(a, b_, tol=0.02):
    return math.hypot(a[0] - b_[0], a[1] - b_[1]) < tol


def apply(src, dst):
    b = pcbnew.LoadBoard(src)
    u3_origin(b)
    net = b.FindNet(NET)
    in2 = b.GetLayerID("In2.Cu")
    # One pass decides everything: in KiCad 9's SWIG, iterating the board after Remove()/Add()
    # hands back untyped objects, so removals happen last and nothing iterates after them.
    removed, doomed = [], []
    for t in list(b.GetTracks()):
        if t.GetNetname() != NET:
            continue
        if t.GetClass() == "PCB_VIA":
            p = rel(b, t.GetPosition())
            if any(near(p, v, 0.3) for v in PIN_VIAS.values()):
                t.SetLocked(True)  # the in-pad via is a spoke end now
                continue
            in_ring = max(abs(p[0]), abs(p[1])) < 2.45
            c19_detour = near(p, (0.112, -5.19))
            old_cout = near(p, (0.963, 4.385))
            if in_ring or c19_detour or old_cout:
                removed.append(("via", p)); doomed.append(t)
            continue
        s, e = rel(b, t.GetStart()), rel(b, t.GetEnd())
        if max(abs(s[0]), abs(s[1]), abs(e[0]), abs(e[1])) >= 7.0:
            continue
        inner_or_front = t.GetLayer() in (in2, pcbnew.F_Cu)
        inside_ring = t.GetLayer() == pcbnew.B_Cu and max(abs(s[0]), abs(s[1]), abs(e[0]), abs(e[1])) < 2.45
        stub_to_old = t.GetLayer() == pcbnew.B_Cu and any(near(q, v) for q in (s, e) for v in ((0.112, -5.19), (0.963, 4.385)))
        if inner_or_front or inside_ring or stub_to_old:
            removed.append((b.GetLayerName(t.GetLayer()), s, e)); doomed.append(t)
        elif t.GetLayer() == pcbnew.B_Cu and any(near(q, v, 0.3) for q in (s, e) for v in PIN_VIAS.values()):
            t.SetLocked(True)  # pad-to-via stub

    def via(p, d=0.6, drill=0.25):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(absv(b, *p)); v.SetWidth(MM(d)); v.SetDrill(MM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); v.SetLocked(True)
        b.Add(v)

    def track(a, c, layer, w):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(absv(b, *a)); t.SetEnd(absv(b, *c)); t.SetWidth(MM(w))
        t.SetLayer(layer); t.SetNet(net); t.SetLocked(True)
        b.Add(t)

    for p in RING_VIAS.values():
        via(p)
    via(COUT_VIA)
    for path in SPOKES:
        for a, c in zip(path, path[1:]):
            track(a, c, in2, 0.6)
    for a, c in zip(PIN23_C19, PIN23_C19[1:]):
        track(a, c, pcbnew.B_Cu, 0.2)
    for a, c in list(zip(RING_TIE, RING_TIE[1:])) + RING_FEET:
        track(a, c, pcbnew.B_Cu, 0.25)
    for t in doomed:
        b.Remove(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(dst, b)
    for r in removed:
        print("removed", r)
    print(f"added 5 vias 0.6/0.25, {sum(len(p) - 1 for p in SPOKES)} In2.Cu spoke segments, {len(PIN23_C19) - 1} B.Cu pin23-C19 segments")


def strip(path, drc_json):
    b = pcbnew.LoadBoard(path)
    u3_origin(b)
    d = json.load(open(drc_json))
    bad = set()
    for v in d.get("violations", []):
        if v["type"] not in ("clearance", "shorting_items", "tracks_crossing", "hole_clearance", "copper_edge_clearance", "hole_to_hole"):
            continue
        items = v["items"]
        if not any(f"[{NET}]" in i["description"] for i in items):
            continue
        for i in items:
            if f"[{NET}]" not in i["description"]:
                bad.add(i["uuid"])
    n = 0
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in bad:
            print("strip", t.GetClass(), t.GetNetname(), b.GetLayerName(t.GetLayer()) if t.GetClass() != "PCB_VIA" else "via",
                  tuple(round(x, 3) for x in rel(b, t.GetPosition() if t.GetClass() == "PCB_VIA" else t.GetStart())))
            b.Remove(t); n += 1
    pcbnew.SaveBoard(path, b)
    print(f"stripped {n} items; {len(bad) - n} named items were not tracks/vias (pads, zones): check by hand")


def lock(path, radius):
    b = pcbnew.LoadBoard(path)
    u3_origin(b)
    nl = nu = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pts = [rel(b, t.GetPosition())]
        else:
            pts = [rel(b, t.GetStart()), rel(b, t.GetEnd())]
        far = all(math.hypot(*p) > radius for p in pts)
        # ultraroute writes the copper it routed locked, so the old lock state can't be trusted:
        # critical nets (crystal, USB, QSPI) and 1V1 stay locked, everything near U3 is freed.
        # PGND's two plane vias (vendor GND zone, ~(2.5..2.9, 4.4..4.8)): ultraroute's via pass
        # dropped one as redundant on 2026-11-09; the reference needs both.
        pgnd = t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND" and all(2.2 < p[0] < 3.3 and 4.0 < p[1] < 5.2 for p in pts)
        keep = far or pgnd or t.GetNetname() == NET or bool(CRIT.search(t.GetNetname()))
        t.SetLocked(bool(keep))
        nl += keep; nu += not keep
    pcbnew.SaveBoard(path, b)
    print(f"locked {nl}, unlocked {nu} within {radius} mm of U3")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "apply":
        apply(sys.argv[2], sys.argv[3])
    elif cmd == "strip":
        strip(sys.argv[2], sys.argv[3])
    elif cmd == "lock":
        lock(sys.argv[2], float(sys.argv[3]))
    else:
        sys.exit(__doc__)
