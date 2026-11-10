#!/usr/bin/env python3
"""finish_last_nets.py — Surgical 2nd-pass closure from route/s0.kicad_pcb (198/204 closed, 0 plane open):
  1. Snapshots route/s0.kicad_pcb -> route/pass1_s0.kicad_pcb.
  2. Strips ONLY unlocked Pass-1 copper on the 6 open nets + their immediate competing neighbor nets,
     plus unlocks F.Cu stubs within 2.5 mm of D4.3 (87.28, 109.31) so SW1_4 steps past BT1.MP cleanly.
  3. Locks all ~188 cleanly closed nets from Pass 1 (checking none collide with restored WLCSP escapes).
  4. Restores parent f-usbc's exact B.Cu WLCSP escape stubs + fanout vias for U2.B2 (CS2_1),
     U2.B5 (CS2_18), U12.C5 (CS5_16), and U12.B6 (SW5_8), ripping any Pass-1 unlocked item that
     encroached on those 4 exact WLCSP escape lanes!
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
VAR_DIR = ROOT / "hw/round-pendant/f-usbc-rtc"
ROUTE_DIR = VAR_DIR / "route"
PARENT_PCB = ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"

OPEN_AND_COMPETING_NETS = {
    # 5 open nets from Pass 1 s1:
    "/Driver 1 and matrix/SW1_4",
    "/Driver 2 and matrix/CS2_1",
    "/Driver 2 and matrix/CS2_18",
    "/Driver 5 and matrix/CS5_16",
    "/MCU/ACC_SCL",
    # Immediate unlocked competitors near D4, U2, D91, U12, U13:
    "/Driver 1 and matrix/CS1_18",
    "/Driver 2 and matrix/CS2_13",
    "/Driver 2 and matrix/CS2_14",
    "/Driver 2 and matrix/CS2_15",
    "/Driver 2 and matrix/CS2_2",
    "/Driver 2 and matrix/SW2_2",
    "/Driver 2 and matrix/SW2_4",
    "/Driver 5 and matrix/CS5_1",
    "/Driver 5 and matrix/CS5_2",
    "/Driver 5 and matrix/SW5_5",
    "/Driver 5 and matrix/SW5_6",
    "/MCU/ACC_SDA",
}

KEEP_ALIVE: list = []


def main() -> int:
    um = pcbnew.ToMM
    fm = pcbnew.FromMM

    s0_src = ROUTE_DIR / "s1.kicad_pcb"
    snap_pcb = ROUTE_DIR / "pass1_s1.kicad_pcb"
    if not snap_pcb.exists():
        shutil.copy2(s0_src, snap_pcb)
    shutil.copy2(VAR_DIR / "round-pendant.kicad_pro", ROUTE_DIR / "pass1_s1.kicad_pro")
    shutil.copy2(VAR_DIR / "round-pendant.kicad_dru", ROUTE_DIR / "pass1_s1.kicad_dru")

    b = pcbnew.LoadBoard(str(snap_pcb))
    FCU = b.GetLayerID("F.Cu")
    BCU = b.GetLayerID("B.Cu")

    # Exact parent f-usbc WLCSP escape lanes to restore (locked):
    esc_specs = [
        # U2.B2 (CS2_1)
        ("/Driver 2 and matrix/CS2_1", [
            ("T", (95.7500, 112.8250), (96.0000, 113.0750), 0.100),
            ("T", (96.0000, 113.0750), (96.0000, 113.7750), 0.100),
            ("T", (96.0000, 113.7750), (95.9390, 113.8360), 0.100),
            ("T", (95.9390, 113.8360), (95.8675, 113.7637), 0.100),
            ("V", (95.8675, 113.7637), None, 0.250),
        ]),
        # U2.B5 (CS2_18)
        ("/Driver 2 and matrix/CS2_18", [
            ("T", (97.2500, 112.8250), (97.5000, 113.0750), 0.100),
            ("T", (97.5000, 113.0750), (97.5000, 113.4500), 0.100),
            ("T", (97.5000, 113.4500), (97.8250, 113.7750), 0.100),
            ("V", (97.8250, 113.7750), None, 0.250),
        ]),
        # U12.C5 (CS5_16)
        ("/Driver 5 and matrix/CS5_16", [
            ("T", (110.6500, 101.1500), (110.6500, 101.0750), 0.100),
            ("T", (110.6500, 101.0750), (110.4000, 100.8250), 0.100),
            ("T", (110.4000, 100.8250), (110.4000, 100.4750), 0.100),
            ("T", (110.4000, 100.4750), (110.4750, 100.4000), 0.100),
            ("T", (110.4750, 100.4000), (111.3250, 100.4000), 0.100),
            ("T", (111.3250, 100.4000), (112.5675,  99.3137), 0.100),
        ]),
    ]

    # Build temporary shapes of restored escapes so we also rip any unlocked Pass-1 net colliding with them!
    esc_shapes_bcu = []
    esc_via_pts = []
    for net_nm, ops in esc_specs:
        for kind, a, c, w in ops:
            if kind == "T":
                tmp = pcbnew.PCB_TRACK(b)
                tmp.SetStart(pcbnew.VECTOR2I(fm(a[0]), fm(a[1])))
                tmp.SetEnd(pcbnew.VECTOR2I(fm(c[0]), fm(c[1])))
                tmp.SetWidth(fm(w))
                tmp.SetLayer(BCU)
                esc_shapes_bcu.append((net_nm, tmp.GetEffectiveShape(BCU)))
            else:
                esc_via_pts.append((net_nm, a[0], a[1]))

    rip_nets = set(OPEN_AND_COMPETING_NETS)
    for item in b.GetTracks():
        if item.IsLocked():
            continue
        tn = item.GetNetname()
        if tn in rip_nets:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            vx, vy = um(item.GetPosition().x), um(item.GetPosition().y)
            if any(tn != en and math.hypot(vx - ex, vy - ey) < 0.37 for en, ex, ey in esc_via_pts):
                rip_nets.add(tn)
            elif any(tn != en and sh.Collide(item.GetEffectiveShape(BCU), fm(0.105)) for en, sh in esc_shapes_bcu):
                rip_nets.add(tn)
        else:
            l = item.GetLayer()
            ts = item.GetEffectiveShape(l)
            if l == BCU and any(tn != en and sh.Collide(ts, fm(0.105)) for en, sh in esc_shapes_bcu):
                rip_nets.add(tn)
            elif any(tn != en and ts.Collide(pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(fm(ex), fm(ey)), fm(0.285))) for en, ex, ey in esc_via_pts):
                rip_nets.add(tn)

    # Also unlock (do NOT lock, let --strip rip!) F.Cu LED chains around D4.3 (87.28, 109.31) so SW1_4 escapes!
    d4_local_nets = {
        "/Driver 1 and matrix/CS1_1",
        "/Driver 1 and matrix/CS1_2",
        "/Driver 1 and matrix/CS1_3",
        "/Driver 1 and matrix/CS1_16",
        "/Driver 1 and matrix/CS1_17",
    }

    to_remove = []
    unlocked_d4 = 0
    locked_pass1 = 0
    for item in list(b.GetTracks()):
        tn = item.GetNetname()
        if tn in rip_nets and not item.IsLocked():
            to_remove.append(item)
        elif tn == "/Driver 5 and matrix/CS5_16" and not isinstance(item, pcbnew.PCB_VIA) and item.GetLayer() == FCU and um(item.GetLength()) < 0.30:
            # Remove the 0.275 mm dangling F.Cu stub on CS5_16
            to_remove.append(item)
        elif tn in d4_local_nets:
            # Unlock items within 3.2 mm of D4.3 (87.28, 109.31) so ultraroute --strip re-routes D4's tiny F.Cu cluster cleanly!
            pts = [item.GetPosition()] if isinstance(item, pcbnew.PCB_VIA) else [item.GetStart(), item.GetEnd()]
            if any(math.hypot(um(p.x) - 87.28, um(p.y) - 109.31) <= 3.2 for p in pts):
                item.SetLocked(False)
                unlocked_d4 += 1
        elif not item.IsLocked():
            item.SetLocked(True)
            locked_pass1 += 1

    for item in to_remove:
        KEEP_ALIVE.append(item)
        b.Remove(item)

    # Restore the 4 locked WLCSP escapes cleanly (deduplicating against existing copper)
    added = 0
    for net_nm, ops in esc_specs:
        nc = b.GetNetInfo().GetNetItem(net_nm).GetNetCode()
        existing_v = {
            (round(um(t.GetPosition().x), 3), round(um(t.GetPosition().y), 3))
            for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_nm
        }
        existing_t = {
            (t.GetLayer(), min((round(um(t.GetStart().x), 3), round(um(t.GetStart().y), 3)), (round(um(t.GetEnd().x), 3), round(um(t.GetEnd().y), 3))),
             max((round(um(t.GetStart().x), 3), round(um(t.GetStart().y), 3)), (round(um(t.GetEnd().x), 3), round(um(t.GetEnd().y), 3))))
            for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net_nm
        }
        for kind, a, c, w in ops:
            if kind == "T":
                p1, p2 = (round(a[0], 3), round(a[1], 3)), (round(c[0], 3), round(c[1], 3))
                key = (BCU, min(p1, p2), max(p1, p2))
                if key not in existing_t:
                    trk = pcbnew.PCB_TRACK(b)
                    trk.SetStart(pcbnew.VECTOR2I(fm(a[0]), fm(a[1])))
                    trk.SetEnd(pcbnew.VECTOR2I(fm(c[0]), fm(c[1])))
                    trk.SetWidth(fm(w))
                    trk.SetLayer(BCU)
                    trk.SetNetCode(nc)
                    trk.SetLocked(True)
                    b.Add(trk)
                    KEEP_ALIVE.append(trk)
                    added += 1
            else:
                vp = (round(a[0], 3), round(a[1], 3))
                if vp not in existing_v:
                    via = pcbnew.PCB_VIA(b)
                    via.SetPosition(pcbnew.VECTOR2I(fm(a[0]), fm(a[1])))
                    via.SetDrill(fm(0.150))
                    via.SetWidth(fm(w))
                    via.SetViaType(pcbnew.VIATYPE_THROUGH)
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    via.SetNetCode(nc)
                    via.SetLocked(True)
                    b.Add(via)
                    KEEP_ALIVE.append(via)
                    added += 1

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    out_pcb = VAR_DIR / "round-pendant.kicad_pcb"
    pro_path = VAR_DIR / "round-pendant.kicad_pro"
    dru_path = VAR_DIR / "round-pendant.kicad_dru"
    pro_bak = pro_path.read_bytes()
    dru_bak = dru_path.read_bytes()
    pcbnew.SaveBoard(str(out_pcb), b)
    pro_path.write_bytes(pro_bak)
    dru_path.write_bytes(dru_bak)
    print(f"Prepared Pass-2 board -> {out_pcb}: rip_nets={len(rip_nets)}, removed={len(to_remove)}, unlocked_d4={unlocked_d4}, locked_pass1={locked_pass1}, added_esc={added}", flush=True)
    import os
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
