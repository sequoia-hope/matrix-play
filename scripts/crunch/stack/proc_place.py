#!/usr/bin/env python3
"""proc_place.py STAGE: processor half for the two-board stack, using board_stack's env. Stage 'place': delete LEDs and driver parts, place the rest on the north half, cut the outline to a half disc with a straight edge at y=0, add seam pads. Stage 'zones': GND plane on In1, RP2350 ring and band (no foreign vias on this board). A first-answer placement, not reviewed."""
import os, sys, math, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import board_stack as bs
import pcbnew
PCB = bs.PCB; OX, OY = bs.OX, bs.OY; mm = pcbnew.FromMM
# ref: x, y[, rot]. Unlisted rot keeps the main board's.
D2 = "U3 C8 C9 C10 C11 C12 C13 C14 C16 C17 C18 C19 C20 C21 L1 R13 R14 R15 R17 Y1 C23 C24 R40 R41 R42".split()   # the RP2350 block moves as one, 2 mm north
FIX = dict(U4=(-10.8, -7.3), U6=(-6.0, -1.9), C4=(-4.4, -1.9), C3=(-7.5, -1.9, 90), C22=(-5.5, -3.8), U7=(-6.4, -4.0) , J1=(-13.4, -2.2), R1=(-9.3, -12.8), R2=(-11.3, -12.8),
           U5=(7.8, -3.05), C2=(11.7, -1.9), C5=(11.7, -3.5), C1=(10.7, -4.75), U8=(13.0, -5.0), C6=(11.1, -5.6), R3=(11.2, -6.5, 90), R4=(12.2, -6.5, 90), R5=(13.2, -6.5, 90),
           BT1=(15.85, -1.9), Q1=(11.6, -10.6), R9=(13.6, -10.2), R10=(12.8, -12.6), R11=(8.7, -8.7), R12=(13.0, -8.7), C7=(10.4, -8.7), R8=(11.6, -8.7),
           TP1=(7.6, -6.2), TP3=(9.6, -6.2), TP2=(-14.5, -10.5), TP4=(6.2, -11.8), TP6=(3.6, -16.6), TP7=(5.6, -16.6),
           R19=(5.6, -13.6), R20=(3.6, -13.6), R6=(11.6, -13.6), R7=(9.6, -13.6), R30=(-8.4, -15.4), R33=(7.6, -15.4))
KEEP_AT = "C25 C26 C27 U9 R16 R18 R21 R22 TP5 TP8 SW1 SW2".split()
SEAM = [(-13.5, "INTB1"), (-12, "SDB1"), (-10.5, "I2C_SCL"), (-9, "I2C_SDA"), (-7.5, "GND"), (-6, "VSYS"), (-4.5, "GND"), (-3, "Net-(D235-R)"), (-1.5, "Net-(D235-G)"), (2.45, "Net-(D235-B)"), (4, "+3V3"), (5.5, "GND"), (7, "VSYS"), (8.5, "VSYS"), (10, "SDB2"), (11.5, "INTB2")]

def place():
    b = pcbnew.LoadBoard(str(PCB)); gone = []; codes = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname(): codes[p.GetNetname()] = p.GetNetCode()
    fps = {}
    for f in list(b.GetFootprints()):
        r = f.GetReference()
        if r in bs.KEEP or r.startswith("D"):
            gone.append(f); b.Remove(f)
        else:
            fps[r] = f
    missing = set(fps)-set(D2)-set(FIX)-set(KEEP_AT); assert not missing, missing
    for r in D2:
        p = fps[r].GetPosition(); fps[r].SetPosition(pcbnew.VECTOR2I(p.x, p.y-mm(2)))
    for r, v in FIX.items():
        fps[r].SetPosition(pcbnew.VECTOR2I(mm(OX+v[0]), mm(OY+v[1])))
        if len(v) > 2: fps[r].SetOrientationDegrees(v[2])
    # Legaliser: fixed parts stay; the rest, in order, take the nearest free spot to where the table put them. Boxes are the parts' courtyard-size bounding boxes plus a margin.
    FIXED = set(D2) | {"U4", "J1", "BT1", "SW1", "SW2"}
    def box(f):
        bb = f.GetBoundingBox(False, False); q = (bb.GetLeft()/1e6-OX, bb.GetTop()/1e6-OY, bb.GetRight()/1e6-OX, bb.GetBottom()/1e6-OY)
        if f.GetReference().startswith("TP"):    # 1 mm pad; its 2 mm courtyard is the probe's, not copper
            cx, cy = f.GetPosition().x/1e6-OX, f.GetPosition().y/1e6-OY; return (cx-.6, cy-.6, cx+.6, cy+.6)
        return q
    placed = {r: box(fps[r]) for r in FIXED}
    M = float(os.environ.get("MARGIN", ".02"))
    def free(bx):
        if bx[3] > -1.1: return False
        if any(math.hypot(x, y) > 18.65 for x in (bx[0], bx[2]) for y in (bx[1], bx[3])): return False
        return not any(bx[0] < q[2]+M and q[0] < bx[2]+M and bx[1] < q[3]+M and q[1] < bx[3]+M for q in placed.values())
    moved = {}; nof = []
    rest = sorted((r for r in fps if r not in FIXED), key=lambda r: -(box(fps[r])[2]-box(fps[r])[0])*(box(fps[r])[3]-box(fps[r])[1]))
    for r in rest:
        bx = box(fps[r]); cx0, cy0 = fps[r].GetPosition().x/1e6-OX, fps[r].GetPosition().y/1e6-OY
        best = None
        for ri in range(0, 300):
            rad = ri*.1
            for k in range(max(1, 8*ri)):
                a = 2*math.pi*k/max(1, 8*ri); dx, dy = rad*math.cos(a), rad*math.sin(a)
                q = (bx[0]+dx, bx[1]+dy, bx[2]+dx, bx[3]+dy)
                if free(q):
                    best = (dx, dy, q); break
            if best: break
        
        if not best:
            print("NO ROOM", r, flush=True); nof.append(r); continue
        fps[r].SetPosition(pcbnew.VECTOR2I(mm(OX+cx0+best[0]), mm(OY+cy0+best[1]))); placed[r] = best[2]
        if rad > 0: moved[r] = round(rad, 1)
    print("legalised, moved", moved, "no room", nof, "bbox area", round(sum((q[2]-q[0])*(q[3]-q[1]) for q in placed.values())), flush=True)
    for s in list(b.GetDrawings()):
        if s.GetLayer() == pcbnew.Edge_Cuts: gone.append(s); b.Remove(s)
    R = 19.0
    a = pcbnew.PCB_SHAPE(b); a.SetShape(pcbnew.SHAPE_T_ARC); a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(.05))
    a.SetArcGeometry(pcbnew.VECTOR2I(mm(OX-R), mm(OY)), pcbnew.VECTOR2I(mm(OX), mm(OY-R)), pcbnew.VECTOR2I(mm(OX+R), mm(OY))); b.Add(a)
    l = pcbnew.PCB_SHAPE(b); l.SetShape(pcbnew.SHAPE_T_SEGMENT); l.SetLayer(pcbnew.Edge_Cuts); l.SetWidth(mm(.05)); l.SetStart(pcbnew.VECTOR2I(mm(OX-R), mm(OY))); l.SetEnd(pcbnew.VECTOR2I(mm(OX+R), mm(OY))); b.Add(l)
    f = pcbnew.FOOTPRINT(b); f.SetReference("J8"); f.SetValue("seam"); f.SetFPID(pcbnew.LIB_ID("round_pendant", "SeamProc")); b.Add(f); f.SetLayer(pcbnew.B_Cu); f.SetPosition(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    net = lambda s: [v for k, v in codes.items() if k == s or k.endswith("/"+s)][0]
    for i, (x, name) in enumerate(SEAM, 1):
        pd = pcbnew.PAD(f); pd.SetShape(pcbnew.PAD_SHAPE_RECT); pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.B_Mask); pd.SetLayerSet(ls); pd.SetSize(pcbnew.VECTOR2I(mm(.9), mm(.7))); pd.SetNumber(str(i)); f.Add(pd)
        pd.SetPosition(pcbnew.VECTOR2I(mm(OX+x), mm(OY-.5))); pd.SetNetCode(net(name))
    pcbnew.SaveBoard(str(PCB), b); print("placed proc", len(fps), "parts", flush=True); os._exit(0)

def zones():
    b = pcbnew.LoadBoard(str(PCB)); fps = {f.GetReference(): f for f in b.GetFootprints()}
    def poly(pts):
        p = pcbnew.SHAPE_POLY_SET(); p.NewOutline()
        for x, y in pts: p.Append(mm(OX+x), mm(OY+y))
        return p
    def add(name, layer, net, pts, prio, connect=pcbnew.ZONE_CONNECTION_FULL, minw=.1, clear=.2):
        z = pcbnew.ZONE(b); z.SetZoneName(name); z.SetLayer(layer); z.SetNet(b.FindNet(net)); z.SetAssignedPriority(prio)
        z.SetPadConnection(connect); z.SetMinThickness(mm(minw)); z.SetThermalReliefGap(mm(.2)); z.SetThermalReliefSpokeWidth(mm(.2)); z.SetLocalClearance(mm(clear))
        pl = poly(pts); pl.thisown = False; z.SetOutline(pl); b.Add(z)
    half = [(18.8*math.cos(math.pi+math.pi*k/64), 18.8*math.sin(math.pi+math.pi*k/64)-.2) for k in range(65)]
    add("plane GND", pcbnew.In1_Cu, "GND", half, 0)
    u = fps["U3"].GetPosition(); ux, uy = pcbnew.ToMM(u.x)-OX, pcbnew.ToMM(u.y)-OY
    sq = lambda h: [(ux-h, uy-h), (ux+h, uy-h), (ux+h, uy+h), (ux-h, uy+h)]
    add("RP2350 band", pcbnew.B_Cu, "+3V3", sq(2.8), 1, clear=.09)
    add("RP2350 ring", pcbnew.B_Cu, "+1V1", sq(2.2), 3, connect=pcbnew.ZONE_CONNECTION_THERMAL, minw=.2, clear=.09)
    lx = [p for p in fps["L1"].Pads() if p.GetNetname().endswith("VREG_LX")]+[p for p in fps["U3"].Pads() if p.GetNetname().endswith("VREG_LX")]
    bb = [p.GetBoundingBox() for p in lx]
    x0 = min(pcbnew.ToMM(q.GetLeft()) for q in bb)-OX-.3; x1 = max(pcbnew.ToMM(q.GetRight()) for q in bb)-OX+.3; y0 = min(pcbnew.ToMM(q.GetTop()) for q in bb)-OY-.3; y1 = max(pcbnew.ToMM(q.GetBottom()) for q in bb)-OY+.3
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName("LX no plane"); k.SetLayer(pcbnew.In1_Cu); k.SetDoNotAllowCopperPour(True); k.SetDoNotAllowTracks(False); k.SetDoNotAllowVias(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    pl = poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]); pl.thisown = False; k.SetOutline(pl); b.Add(k)
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName("U3 no tracks inside pads"); k.SetLayer(pcbnew.B_Cu); k.SetDoNotAllowCopperPour(False); k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    pl = poly(sq(2.9)); pl.thisown = False; k.SetOutline(pl); b.Add(k)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b); print("zones", [z.GetZoneName() for z in b.Zones()])

{"place": place, "zones": zones}[sys.argv[1]]()
