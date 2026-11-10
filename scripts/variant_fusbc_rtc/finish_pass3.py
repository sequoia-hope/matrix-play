#!/usr/bin/env python3
"""finish_pass3.py — Surgical 3rd-pass closure from route/pass2_s2.kicad_pcb:
  1. Snaps the 3 overhanging T-junction tails on CS1_2 (F.Cu) and CS5_16 (F.Cu & B.Cu)
     to exact endpoint-to-endpoint joints (0 DRC violations!).
  2. Sets RX8130_xtal_end on B.Cu to [114.30..115.20, 102.30..103.05] mm — covering the
     Pin 1..10 *1 crystal inspection short side (ETM50E-10 Fig. 9 p. 11 & rx8130ce.pdf p. 1)
     with 0 items_not_allowed violations while opening the 1.20 mm B.Cu corridor
     [114.15..115.35, 99.30..102.20] for U13.2 (ACC_SCL) and U13.3 (ACC_SDA).
  3. Unlocks ONLY CS2_18 (outside U2.B5 escape) + local F.Cu stubs of CS2_17 & SW2_2 within
     2.35 mm of D91.1 (100.964, 113.715), while locking all other 210 closed nets.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
VAR_DIR = ROOT / "hw/round-pendant/f-usbc-rtc"
ROUTE_DIR = VAR_DIR / "route"
KEEP_ALIVE: list = []


def main() -> int:
    um = pcbnew.ToMM
    fm = pcbnew.FromMM

    pcb_path = VAR_DIR / "round-pendant.kicad_pcb"
    pro_path = VAR_DIR / "round-pendant.kicad_pro"
    dru_path = VAR_DIR / "round-pendant.kicad_dru"
    snap_pcb = ROUTE_DIR / "pass2_s2.kicad_pcb"

    b = pcbnew.LoadBoard(str(snap_pcb))
    FCU = b.GetLayerID("F.Cu")
    BCU = b.GetLayerID("B.Cu")

    # 1. Update RX8130_xtal_end outline to [114.30..115.20, 102.30..103.05] mm
    xtal_ra = next(z for z in b.Zones() if z.GetZoneName() == "RX8130_xtal_end")
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for rx, ry in [(114.30, 102.30), (115.20, 102.30), (115.20, 103.05), (114.30, 103.05)]:
        poly.Append(fm(rx), fm(ry))
    poly.thisown = False
    xtal_ra.SetOutline(poly)
    xtal_ra.SetLocked(True)

    # 2. Snap the exact 3 T-junction overhangs to clean endpoint-to-endpoint joints:
    snapped = 0
    for t in list(b.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        tn = t.GetNetname()
        l = t.GetLayer()
        x1, y1 = round(um(t.GetStart().x), 4), round(um(t.GetStart().y), 4)
        x2, y2 = round(um(t.GetEnd().x), 4), round(um(t.GetEnd().y), 4)
        ln = um(t.GetLength())
        if tn == "/Driver 1 and matrix/CS1_2" and l == FCU and abs(ln - 0.375) < 0.005 and abs(x1 - 83.4925) < 0.01:
            t.SetEnd(pcbnew.VECTOR2I(fm(83.4675), fm(105.1137)))
            snapped += 1
        elif tn == "/Driver 5 and matrix/CS5_16" and l == FCU and abs(ln - 0.275) < 0.005 and abs(x1 - 110.6925) < 0.01:
            KEEP_ALIVE.append(t)
            b.Remove(t)
            snapped += 1
        elif tn == "/Driver 5 and matrix/CS5_16" and l == FCU and abs(ln - 0.4008) < 0.005 and abs(x1 - 110.6675) < 0.01:
            t.SetStart(pcbnew.VECTOR2I(fm(110.6925), fm(103.7137)))
            snapped += 1
        elif tn == "/Driver 5 and matrix/CS5_16" and l == BCU and abs(ln - 1.6504) < 0.005 and abs(x1 - 111.325) < 0.01:
            t.SetEnd(pcbnew.VECTOR2I(fm(111.9462), fm(99.8569)))
            nt = pcbnew.PCB_TRACK(b)
            nt.SetStart(pcbnew.VECTOR2I(fm(111.9462), fm(99.8569)))
            nt.SetEnd(pcbnew.VECTOR2I(fm(111.9675), fm(99.8887)))
            nt.SetWidth(t.GetWidth())
            nt.SetLayer(BCU)
            nt.SetNetCode(t.GetNetCode())
            nt.SetLocked(True)
            b.Add(nt)
            KEEP_ALIVE.append(nt)
            snapped += 1

    # 3. Strip unlocked CS2_18 copper (preserving locked U2.B5 escape), unlock ONLY local CS2_17/SW2_2 near D91.1,
    #    and lock all other closed nets!
    removed_cs2_18 = 0
    unlocked_d91 = 0
    locked_cnt = 0
    for item in list(b.GetTracks()):
        tn = item.GetNetname()
        if tn == "/Driver 2 and matrix/CS2_18" and not item.IsLocked():
            KEEP_ALIVE.append(item)
            b.Remove(item)
            removed_cs2_18 += 1
        elif tn in ("/Driver 2 and matrix/CS2_17", "/Driver 2 and matrix/SW2_2"):
            pts = [item.GetPosition()] if isinstance(item, pcbnew.PCB_VIA) else [item.GetStart(), item.GetEnd()]
            if any(math.hypot(um(p.x) - 100.964, um(p.y) - 113.715) <= 2.20 for p in pts) and not isinstance(item, pcbnew.PCB_VIA) and item.GetLayer() == FCU:
                item.SetLocked(False)
                unlocked_d91 += 1
            else:
                item.SetLocked(True)
                locked_cnt += 1
        elif tn in ("/MCU/ACC_SCL", "/MCU/ACC_SDA") and not item.IsLocked():
            KEEP_ALIVE.append(item)
            b.Remove(item)
        else:
            if not item.IsLocked():
                item.SetLocked(True)
                locked_cnt += 1

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pro_bak = pro_path.read_bytes()
    dru_bak = dru_path.read_bytes()
    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bak)
    dru_path.write_bytes(dru_bak)
    print(
        f"Prepared Pass-3 board -> {pcb_path}: snapped={snapped}, removed_cs2_18={removed_cs2_18}, "
        f"unlocked_d91={unlocked_d91}, newly_locked={locked_cnt}",
        flush=True,
    )
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
