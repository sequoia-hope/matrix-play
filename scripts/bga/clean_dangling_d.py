#!/usr/bin/env python3
"""clean_dangling_d.py BOARD.kicad_pcb [OUT.kicad_pcb]

Removes any DRC-flagged `track_dangling` or `via_dangling` items (including locked
pre-escape stubs whose continuation routed another way) ONLY when removing the item
does not increase KiCad's unconnected count. Preserves `.kicad_pro`.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

KEEP_ALIVE = []


def run_drc(pcb_path: Path, drc_json: Path) -> dict:
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--format", "json", "--severity-error", "--severity-warning", "-o", str(drc_json), str(pcb_path)],
        capture_output=True,
        check=True,
    )
    return json.loads(drc_json.read_text())


def main():
    pcb_in = Path(sys.argv[1])
    pcb_out = Path(sys.argv[2]) if len(sys.argv) > 2 else pcb_in
    if pcb_in != pcb_out:
        pcb_out.write_bytes(pcb_in.read_bytes())
    pro_path = pcb_out.with_suffix(".kicad_pro")
    pro_bytes = pro_path.read_bytes() if pro_path.exists() else None
    drc_json = Path("/tmp/d-clean-dangling.json")

    um = pcbnew.ToMM
    for it in range(8):
        d = run_drc(pcb_out, drc_json)
        t_dang = [v for v in d.get("violations", []) if v["type"] == "track_dangling"]
        v_dang = [v for v in d.get("violations", []) if v["type"] == "via_dangling"]
        print(f"pass {it}: track_dangling={len(t_dang)}, via_dangling={len(v_dang)}, unconnected={len(d.get('unconnected_items', []))}")
        if not t_dang and not v_dang:
            break

        b = pcbnew.LoadBoard(str(pcb_out))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.BuildConnectivity()
        base_open = b.GetConnectivity().GetUnconnectedCount(False)
        removed = 0

        for v in t_dang:
            item = v["items"][0]
            px, py = item["pos"]["x"], item["pos"]["y"]
            m_net = re.search(r"\[([^\]]+)\]", item["description"])
            m_lay = re.search(r"on (\S+), length ([0-9.]+) mm", item["description"])
            if not m_net or not m_lay:
                continue
            net = m_net.group(1)
            lay = m_lay.group(1)
            ln = float(m_lay.group(2))
            for t in list(b.GetTracks()):
                if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net or t.GetLayerName() != lay:
                    continue
                if abs(um(t.GetLength()) - ln) > 0.003:
                    continue
                s, e = t.GetStart(), t.GetEnd()
                sx, sy, ex, ey = um(s.x), um(s.y), um(e.x), um(e.y)
                d_pos = min(math.hypot(sx - px, sy - py), math.hypot(ex - px, ey - py), math.hypot((sx + ex) / 2 - px, (sy + ey) / 2 - py))
                if d_pos < 0.035:
                    KEEP_ALIVE.append(t)
                    b.Remove(t)
                    b.BuildConnectivity()
                    if b.GetConnectivity().GetUnconnectedCount(False) > base_open:
                        b.Add(t)
                        b.BuildConnectivity()
                    else:
                        removed += 1
                    break

        for v in v_dang:
            item = v["items"][0]
            px, py = item["pos"]["x"], item["pos"]["y"]
            for t in list(b.GetTracks()):
                if not isinstance(t, pcbnew.PCB_VIA):
                    continue
                c = t.GetPosition()
                if math.hypot(um(c.x) - px, um(c.y) - py) < 0.015:
                    KEEP_ALIVE.append(t)
                    b.Remove(t)
                    b.BuildConnectivity()
                    if b.GetConnectivity().GetUnconnectedCount(False) > base_open:
                        b.Add(t)
                        b.BuildConnectivity()
                    else:
                        removed += 1
                    break

        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(str(pcb_out), b)
        if pro_bytes is not None:
            pro_path.write_bytes(pro_bytes)
        print(f"  removed={removed}")
        if removed == 0:
            break

    if drc_json.exists():
        drc_json.unlink()
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
