#!/usr/bin/env python3
"""board_outline.py -- phase 4: the outline-only board: circle, J1, buttons, BT1, placed and on the back."""
import json, math
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[3]
import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
st = json.loads((ROOT / "design/study/sites.json").read_text())
b = pcbnew.NewBoard(str(HW / "round-pendant.kicad_pcb"))
b.SetCopperLayerCount(6)
OX, OY = 100.0, 100.0
mm = pcbnew.FromMM
c = pcbnew.PCB_SHAPE(b); c.SetShape(pcbnew.SHAPE_T_CIRCLE); c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(mm(0.1))
c.SetCenter(pcbnew.VECTOR2I(mm(OX), mm(OY))); c.SetEnd(pcbnew.VECTOR2I(mm(OX + 19), mm(OY))); b.Add(c)
sys_fp = "/usr/share/kicad/footprints/"
def add(lib, name, ref, x, y, deg):
    f = pcbnew.FootprintLoad(lib, name); f.SetReference(ref)
    f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
    b.Add(f)
    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(180 - deg)  # back-side part: the mirror image in x of the part at rotation deg
    return f
if VARIANT != "a":
    b.Save(str(HW / "round-pendant.kicad_pcb"))
    print("saved"); raise SystemExit
j = st["j1"]
add(sys_fp + "Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", "J1", j[0], j[1], 0)
for ref, deg in st["buttons_deg"].items():
    a = math.radians(deg); r = st["button_radius"]
    add(sys_fp + "Button_Switch_SMD.pretty", "SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010", ref, r*math.cos(a), r*math.sin(a), deg - 90)
add(str(HW / "lib/round_pendant.pretty"), "BatteryPads", "BT1", 8.0, 10.6, 0)
b.Save(str(HW / "round-pendant.kicad_pcb"))
print("saved")
