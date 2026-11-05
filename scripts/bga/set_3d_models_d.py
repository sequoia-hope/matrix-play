#!/usr/bin/env python3
"""set_3d_models_d.py BOARD.kicad_pcb [OUT.kicad_pcb] -- attach 3D STEP models including WLCSP-36."""
import os
import sys
import pcbnew

BASE = "${KIPRJMOD}/../../../3dmodels/"
M = {
    "LED_XL-1010RGB": ("XL-1010RGB-YG.step", 0),
    "WLCSP-36_2.9x2.9mm_P0.5mm": ("WLCSP-36_2.9x2.9mm_P0.5mm.step", 0),
    "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias": ("QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0),
    "L_pol_2016": ("IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T.step", 180),
    "SW_Panasonic_EVQP7C": ("SW-SMD_EVQP7C01P-L3.6-W3.5-H1.4-P3.6-LS4.7.step", 0),
    "XySemi_DFN-6_1.8x1.4mm": ("DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step", 0),
    "Texas_X2SON-4_1x1mm_P0.65mm": ("X2SON-4_L1.0-W1.0-H0.4-P0.65-TL-EPSLDPRT.step", 270),
}
ZUP = {"XySemi_DFN-6_1.8x1.4mm": 0.56}

b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for f in b.GetFootprints():
    name = str(f.GetFPID().GetUniStringLibItemName())
    if name in M:
        file, rot = M[name]
        ms = f.Models()
        ms.clear()
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = BASE + file
        m.m_Rotation = pcbnew.VECTOR3D(0, 0, rot)
        m.m_Show = True
        m.m_Offset = pcbnew.VECTOR3D(0, 0, ZUP.get(name, 0))
        ms.push_back(m)
        n += 1
pcbnew.SaveBoard(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], b)
print("models set on", n, "footprints", flush=True)
os._exit(0)
