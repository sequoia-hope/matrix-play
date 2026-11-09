#!/usr/bin/env python3
"""finish_last_net.py — Prepare final surgical 4-net closure pass from Pass #3 s0.kicad_pcb.

In Pass #3 s0.kicad_pcb (189/190 closed, 0 plane open, 0 thin pad joints):
  - U2.B5 (/Driver 2 and matrix/CS2_18) was blocked because outer balls SW2_4 (U2.A5) and
    CS2_15 (U2.C6) claimed its (97.8250, 113.7750) escape lane/via spot first.
  - /Driver 5 and matrix/SW5_6 left one 0.100 mm dangling F.Cu stub.

This script:
  1. Snapshots route/s0.kicad_pcb -> route/pass3_s0.kicad_pcb with matching .kicad_pro/.kicad_dru.
  2. Removes ONLY unlocked (Pass #3) copper on {CS2_18, CS2_15, SW2_4, SW5_6}.
  3. Locks the remaining 186 cleanly closed nets from Pass #3.
  4. Restores Board F's exact U2.B5 CS2_18 WLCSP escape stub + via at (97.8250, 113.7750) (locked).
  5. Refills zones and writes hw/round-pendant/f-usbc/round-pendant.kicad_pcb safely.
"""
from __future__ import annotations

import shutil
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
VAR_DIR = ROOT / "hw/round-pendant/f-usbc"
ROUTE_DIR = VAR_DIR / "route"
BOARD_F = ROOT / "hw/round-pendant/f/round-pendant.kicad_pcb"

RIP_NETS = {
    "/Driver 2 and matrix/CS2_18",
    "/Driver 2 and matrix/CS2_15",
    "/Driver 2 and matrix/SW2_4",
    "/Driver 5 and matrix/SW5_6",
}

KEEP_ALIVE: list = []


def main() -> int:
    um = pcbnew.ToMM
    fm = pcbnew.FromMM

    s0_src = ROUTE_DIR / "s0.kicad_pcb"
    snap_pcb = ROUTE_DIR / "pass3_s0.kicad_pcb"
    if not snap_pcb.exists():
        shutil.copy2(s0_src, snap_pcb)
    shutil.copy2(VAR_DIR / "round-pendant.kicad_pro", ROUTE_DIR / "pass3_s0.kicad_pro")
    shutil.copy2(VAR_DIR / "round-pendant.kicad_dru", ROUTE_DIR / "pass3_s0.kicad_dru")

    b = pcbnew.LoadBoard(str(snap_pcb))

    to_remove = []
    locked_pass3 = 0
    for item in list(b.GetTracks()):
        n = item.GetNetname()
        if n in RIP_NETS and not item.IsLocked():
            to_remove.append(item)
        elif not item.IsLocked():
            item.SetLocked(True)
            locked_pass3 += 1

    for item in to_remove:
        KEEP_ALIVE.append(item)
        b.Remove(item)

    # Check existing CS2_18 items so we don't duplicate
    cs2_18_nc = b.GetNetInfo().GetNetItem("/Driver 2 and matrix/CS2_18").GetNetCode()
    existing = set()
    for item in b.GetTracks():
        if item.GetNetname() != "/Driver 2 and matrix/CS2_18":
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            existing.add(("V", round(um(p.x), 4), round(um(p.y), 4)))
        else:
            s, e = item.GetStart(), item.GetEnd()
            existing.add(("T", item.GetLayerName(), round(um(s.x), 4), round(um(s.y), 4), round(um(e.x), 4), round(um(e.y), 4)))

    esc_segs = [
        ("B.Cu", (97.2500, 112.8250), (97.5000, 113.0750), 0.100),
        ("B.Cu", (97.5000, 113.0750), (97.5000, 113.4500), 0.100),
        ("B.Cu", (97.5000, 113.4500), (97.8250, 113.7750), 0.100),
    ]
    added = 0
    for ln, a, c, w in esc_segs:
        sig1 = ("T", ln, a[0], a[1], c[0], c[1])
        sig2 = ("T", ln, c[0], c[1], a[0], a[1])
        if sig1 not in existing and sig2 not in existing:
            trk = pcbnew.PCB_TRACK(b)
            trk.SetStart(pcbnew.VECTOR2I(fm(a[0]), fm(a[1])))
            trk.SetEnd(pcbnew.VECTOR2I(fm(c[0]), fm(c[1])))
            trk.SetWidth(fm(w))
            trk.SetLayer(b.GetLayerID(ln))
            trk.SetNetCode(cs2_18_nc)
            trk.SetLocked(True)
            b.Add(trk)
            KEEP_ALIVE.append(trk)
            added += 1

    via_pos = (97.8250, 113.7750)
    if ("V", via_pos[0], via_pos[1]) not in existing:
        via = pcbnew.PCB_VIA(b)
        via.SetPosition(pcbnew.VECTOR2I(fm(via_pos[0]), fm(via_pos[1])))
        via.SetDrill(fm(0.150))
        via.SetWidth(fm(0.250))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNetCode(cs2_18_nc)
        via.SetLocked(True)
        b.Add(via)
        KEEP_ALIVE.append(via)
        added += 1

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    unconn = b.GetConnectivity().GetUnconnectedCount(False)

    out_pcb = VAR_DIR / "round-pendant.kicad_pcb"
    pro_path = VAR_DIR / "round-pendant.kicad_pro"
    dru_path = VAR_DIR / "round-pendant.kicad_dru"
    pro_bak = pro_path.read_bytes()
    dru_bak = dru_path.read_bytes()
    pcbnew.SaveBoard(str(out_pcb), b)
    pro_path.write_bytes(pro_bak)
    dru_path.write_bytes(dru_bak)

    print(
        f"Prepared {out_pcb}: removed={len(to_remove)} unlocked items on 4 nets, "
        f"locked_pass3={locked_pass3}, added_cs2_18_esc={added}, unconnected={unconn}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
