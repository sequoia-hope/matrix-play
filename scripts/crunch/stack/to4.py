#!/usr/bin/env python3
"""to4.py BOARD [THICK]: cut a board with nothing on In3/In4 to 4 copper layers, in the file's text (pcbnew can't set a stackup headless), then refill. Thickness is an estimate, 0.8 mm by default: F-prepreg-In1-core-In2-prepreg-B."""
import re, sys, pcbnew
p = sys.argv[1]; th = float(sys.argv[2]) if len(sys.argv) > 2 else .8
t = open(p).read()
assert '"In3.Cu"' in t
t = re.sub(r'\t\t\(8 "In3.Cu" signal\)\n\t\t\(10 "In4.Cu" signal\)\n', '', t, count=1)
PP = .0994; core = round(th-2*PP-2*.035-2*.0152-2*.01, 4)
L = lambda n, k, x: f'\t\t\t(layer "{n}" (type "{k}")' + (f' (thickness {x})' if x else '') + ')'
D = lambda i, k, x: f'\t\t\t(layer "dielectric {i}" (type "{k}") (thickness {x}) (material "FR4") (epsilon_r 4.1) (loss_tangent 0.02))'
s = ['\t\t(stackup', L("F.SilkS", "Top Silk Screen", None), L("F.Paste", "Top Solder Paste", None), L("F.Mask", "Top Solder Mask", .01), L("F.Cu", "copper", .035), D(1, "prepreg", PP), L("In1.Cu", "copper", .0152), D(2, "core", core), L("In2.Cu", "copper", .0152), D(3, "prepreg", PP), L("B.Cu", "copper", .035), L("B.Mask", "Bottom Solder Mask", .01), L("B.Paste", "Bottom Solder Paste", None), L("B.SilkS", "Bottom Silk Screen", None), '\t\t\t(copper_finish "ENIG")', '\t\t\t(dielectric_constraints no)', '\t\t)']
t, n = re.subn(r'\t\t\(stackup.*?\n\t\t\)\n', lambda m: "\n".join(s)+"\n", t, count=1, flags=re.S); assert n == 1
assert '"In3.Cu"' not in t and '"In4.Cu"' not in t, "something still on In3/In4"
open(p, "w").write(t)
b = pcbnew.LoadBoard(p); assert b.GetCopperLayerCount() == 4
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(p, b); print("4 layers ok, core", core)
