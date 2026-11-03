#!/usr/bin/env python3
"""mk8.py BOARD --gnd In2.Cu --power In5.Cu [--plane-clear 0.1] [--rp-clear 0.09]: turn a 6-layer variant board into 8 copper layers, in place.

Writes In5/In6 and the stackup into the file's text (pcbnew can't set a stackup headless), then moves the GND zone and the VSYS and 3V3 zones to the named layers, and the LX cut with GND.
Stackup is F-prepreg-In1-core-In2-prepreg-In3-core-In4-prepreg-In5-core-In6-prepreg-B, 1.0 mm. Dielectric thicknesses are an estimate that totals 1.0 mm, not JLC's table.
"""
import argparse, re, pcbnew
ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--gnd", default="In2.Cu"); ap.add_argument("--power", default="In5.Cu"); ap.add_argument("--gnd2", default="")
ap.add_argument("--plane-clear", type=float, default=.1); ap.add_argument("--rp-clear", type=float, default=.09); a = ap.parse_args()
t = open(a.board).read()
t = t.replace('(10 "In4.Cu" signal)\n', '(10 "In4.Cu" signal)\n\t\t(12 "In5.Cu" signal)\n\t\t(14 "In6.Cu" signal)\n', 1)
assert '"In6.Cu" signal' in t
STACK = [("F.SilkS", "Top Silk Screen", None), ("F.Paste", "Top Solder Paste", None), ("F.Mask", "Top Solder Mask", .01), ("F.Cu", "copper", .035)]
names = ["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]; kinds = ["prepreg", "core"]*3 + ["prepreg"]; TH = {"prepreg": .0764, "core": .1700}
s = ['\t\t(stackup']
def lay(n, k, th): return f'\t\t\t(layer "{n}" (type "{k}")' + (f' (thickness {th})' if th else '') + ')'
for n, k, th in STACK: s.append(lay(n, k, th))
for i, (n, k) in enumerate(zip(names, kinds), 1):
    s.append(f'\t\t\t(layer "dielectric {i}" (type "{k}") (thickness {TH[k]}) (material "FR4") (epsilon_r 4.1) (loss_tangent 0.02))')
    s.append(lay(n, "copper", .035 if n == "B.Cu" else .0152))
s += [lay("B.Mask", "Bottom Solder Mask", .01), lay("B.Paste", "Bottom Solder Paste", None), lay("B.SilkS", "Bottom Silk Screen", None), '\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)', '\t\t)']
t, n = re.subn(r'\t\t\(stackup.*?\n\t\t\)\n', lambda m: "\n".join(s) + "\n", t, count=1, flags=re.S); assert n == 1
open(a.board, "w").write(t)
b = pcbnew.LoadBoard(a.board); assert b.GetCopperLayerCount() == 8, b.GetCopperLayerCount()
lid = {b.GetLayerName(l): l for l in range(0, 64) if b.GetLayerName(l).endswith(".Cu")}
for z in b.Zones():
    nm = z.GetZoneName()
    if nm in ("plane VSYS", "plane 3V3"): z.SetLayer(lid[a.power])
    if nm == "plane GND" or nm == "LX no plane": z.SetLayer(lid[a.gnd])
    if nm.startswith("plane"): z.SetLocalClearance(pcbnew.FromMM(a.plane_clear))
    if nm.startswith("RP2350"): z.SetLocalClearance(pcbnew.FromMM(a.rp_clear))
if a.gnd2:
    for z in list(b.Zones()):
        if z.GetZoneName() in ("plane GND", "LX no plane"):
            c = z.Duplicate(False) if hasattr(z, "Duplicate") else z.Clone()
            c = pcbnew.Cast_to_ZONE(c) if not isinstance(c, pcbnew.ZONE) else c
            c.SetLayer(lid[a.gnd2]); c.SetZoneName(z.GetZoneName() + " 2"); b.Add(c)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    for l in z.GetLayerSet().Seq():
        ps = z.GetFilledPolysList(l); print(z.GetZoneName(), b.GetLayerName(l), "pieces", ps.OutlineCount(), "area", round(ps.Area()/1e12, 1))
pcbnew.SaveBoard(a.board, b)
