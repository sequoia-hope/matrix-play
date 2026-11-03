#!/usr/bin/env python3
"""set_3d_models.py BOARD.kicad_pcb [OUT.kicad_pcb] -- give each custom footprint its real 3D model, in place unless OUT is given. Files are in 3dmodels/.

Vendor shapes are the EasyEDA models for each part's LCSC number, with the rotation EasyEDA's own footprint uses (pad 1 sits on the same side as ours). The LED is drawn from its
datasheet (make_led_model.py). L1 turns 180 so its dot sits at the pad the footprint marks (pad 1, the dot = + end); U3 uses 0, because EasyEDA's 270 put its dot off pin 1. The IS31FL3741A model has a 5.3 mm pad against our 5.4 mm footprint, which doesn't show on the top of the package.
"""
import sys
import pcbnew
BASE = "${KIPRJMOD}/../../../3dmodels/"
M = {  # footprint name: (file, z rotation)
    "LED_XL-1010RGB": ("XL-1010RGB-YG.step", 0),
    "QFN-60-1EP_7x7mm_P0.4mm_EP5.4x5.4mm": ("QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0),
    "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias": ("QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0),
    "L_pol_2016": ("IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T.step", 180),
    "SW_Panasonic_EVQP7C": ("SW-SMD_EVQP7C01P-L3.6-W3.5-H1.4-P3.6-LS4.7.step", 0),
    "XySemi_DFN-6_1.8x1.4mm": ("DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step", 0),
    "Texas_X2SON-4_1x1mm_P0.65mm": ("X2SON-4_L1.0-W1.0-H0.4-P0.65-TL-EPSLDPRT.step", 270),
}
ZUP = {"XySemi_DFN-6_1.8x1.4mm": .56}  # its STEP sits below z = 0, inside the board
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for f in b.GetFootprints():
    name = str(f.GetFPID().GetUniStringLibItemName())
    if name in M:
        file, rot = M[name]
        ms = f.Models(); ms.clear()
        m = pcbnew.FP_3DMODEL(); m.m_Filename = BASE + file; m.m_Rotation = pcbnew.VECTOR3D(0, 0, rot); m.m_Show = True
        m.m_Offset = pcbnew.VECTOR3D(0, 0, ZUP.get(name, 0))
        ms.push_back(m); n += 1
pcbnew.SaveBoard(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], b)
print("models set on", n, "footprints")
