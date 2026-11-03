#!/usr/bin/env python3
"""thermal.py BOARD: estimated driver temperature rise for U1, U2. An ESTIMATE, not a simulation.

Finds each driver's exposed-pad copper and GND vias under it, then adds up parallel heat paths from the junction to the board and from the board to air:
  EP pad -> barrels of its GND vias -> In2 plane and other copper -> spreading in the plane -> whole-board convection plus radiation from both faces.
theta_JC is taken from the datasheet if design/parts/drivers.md gives it; otherwise assumed. Natural convection + radiation h = 12 W/m2K (assumed, still air, enclosed cell behind it not modelled).
"""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); um = pcbnew.ToMM
fps = {f.GetReference(): f for f in b.GetFootprints()}
K_CU, K_FR4 = 385.0, 0.3; PLATE = 18e-6
A_BOARD = 2*math.pi*(.019)**2     # both faces, m2
H = 12.0
THETA_AMB = 1/(H*A_BOARD)
P = {"full white, 4.2 V cell": (4.2-2.53)*.439, "300 mA limit, 4.2 V cell": (4.2-2.53)*.150, "300 mA limit, red only, USB 4.5 V": (4.5-1.95)*.150}
print(f"board to air, whole board, both faces: {THETA_AMB:.0f} K/W at h = {H} W/m2K (assumed)")
gnd_planes = [(z.GetZoneName(), b.GetLayerName(l)) for z in b.Zones() if z.GetNetname() == "GND" and not z.GetIsRuleArea() for l in z.GetLayerSet().Seq()]
print("GND planes:", gnd_planes)
for ref in ("U1", "U2"):
    f = fps[ref]; pads = [p for p in f.Pads() if p.GetNumber() == "61"]
    pts = []; area = 0.0
    for p in pads:
        q = p.GetBoundingBox(); area += um(q.GetWidth())*um(q.GetHeight()); pts.append((um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom())))
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND" and any(r[0] <= um(t.GetPosition().x) <= r[2] and r[1] <= um(t.GetPosition().y) <= r[3] for r in pts)]
    foreign = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() != "GND" and min(r[0] for r in pts)-.3 <= um(t.GetPosition().x) <= max(r[2] for r in pts)+.3 and min(r[1] for r in pts)-.3 <= um(t.GetPosition().y) <= max(r[3] for r in pts)+.3]
    n = len(vias); R_v = (.4e-3)/(K_CU*math.pi*.15e-3*PLATE)     # B.Cu to the first plane: about 0.4 mm of barrel; assumes a plane inside that distance
    R_vias = R_v/n if n else float("inf")
    # plane spreading: from an effective pad radius out to the disc edge, plus In5 ignored (other net).
    t_plane = 15.2e-6
    a = math.sqrt(area/math.pi)*1e-3; R_spread = math.log(.019/a)/(2*math.pi*K_CU*t_plane)
    # Outer copper near the EP in parallel is ignored, which is pessimistic.
    R_total = R_vias + R_spread/2 + THETA_AMB*2    # each driver heats half the board's area; spreading is split by the plane on all sides
    print(f"{ref}: EP copper {area:.1f} mm2 in {len(pads)} tiles, {n} GND vias in it, {len(foreign)} foreign vias at or under it; vias {R_vias:.0f} K/W, plane spreading about {R_spread/2:.0f} K/W, half board to air {THETA_AMB*2:.0f} K/W")
    for k, w in P.items():
        print(f"  {k}: {w:.2f} W -> rise about {w*(R_total):.0f} K; of which board to air {w*THETA_AMB*2:.0f} K")
