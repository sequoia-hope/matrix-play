#!/usr/bin/env python3
"""fix1.py BOARD_IN BOARD_OUT DRU: Gemini's step 1, as checked here.
- U3's 3V3 band from +-2.8 to +-2.9 and ten 3V3 finger zones from it into each 3V3 pin's inner end (+-3.0). Confirmed gap: it reached no pin. A band at +-3.06, as proposed, breaks solder_mask_bridge on 11 foreign pads.
- Four 1V1 spoke zones from the ring to DVDD pins 6, 23, 39, 50 (zones, so the no-track area needn't change). Changes the RP2350 reference layout: the note's spokes are vias and far-side wire.
- RELAXATION, labelled: VBAT, BAT_N, VSYS, VBUS may neck to 0.2 mm inside U5, U7, U8's courtyards (their pads are 0.25-0.3 mm wide)."""
import sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM; um = pcbnew.ToMM
fps = {f.GetReference(): f for f in b.GetFootprints()}
u = fps["U3"].GetPosition(); ux, uy = um(u.x), um(u.y)
def poly(pts):
    p = pcbnew.SHAPE_POLY_SET(); p.NewOutline()
    for x, y in pts: p.Append(mm(x), mm(y))
    return p
for z in b.Zones():
    if z.GetZoneName() == "RP2350 band":
        h = 2.9; pl = poly([(ux-h, uy-h), (ux+h, uy-h), (ux+h, uy+h), (ux-h, uy+h)]); pl.thisown = False; z.SetOutline(pl)
    if z.GetZoneName() == "RP2350 ring":
        ring = z
n = 0
for p in fps["U3"].Pads():
    nn = p.GetNetname()
    if nn in ("+1V1", "+3V3"):
        c = p.GetPosition(); x, y = um(c.x), um(c.y); dx, dy = x-ux, y-uy; t = .1; lo = 2.1 if nn == "+1V1" else 2.8
        if abs(dx) > abs(dy):
            s = 1 if dx > 0 else -1; pts = [(ux+s*lo, y-t), (ux+s*3.06, y-t), (ux+s*3.06, y+t), (ux+s*lo, y+t)]
        else:
            s = 1 if dy > 0 else -1; pts = [(x-t, uy+s*lo), (x-t, uy+s*3.06), (x+t, uy+s*3.06), (x+t, uy+s*lo)]
        z = pcbnew.ZONE(b); z.SetZoneName(f"U3 {nn} spoke {p.GetNumber()}"); z.SetLayer(pcbnew.B_Cu); z.SetNet(b.FindNet(nn)); z.SetAssignedPriority(4 if nn == "+1V1" else 2)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(.1)); z.SetLocalClearance(mm(.09))
        pl = poly(pts); pl.thisown = False; z.SetOutline(pl); b.Add(z); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b); print("band +-2.9,", n, "spokes and fingers")
import os
if os.environ.get("ORTH_NECK"):
  with open(sys.argv[3], "a") as f:
      f.write("\n# RELAXATION (c-orth): power nets may neck to 0.2 mm inside these narrow-pad parts' courtyards\n")
      for net_ in ("VBAT", "/Power/BAT_N", "VSYS", "VBUS"):
          f.write(f"(rule \"{net_} neck\"\n  (condition \"A.NetName == '{net_}' && (A.insideCourtyard('U5') || A.insideCourtyard('U7') || A.insideCourtyard('U8'))\")\n  (constraint track_width (min 0.2mm)))\n")
