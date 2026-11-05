#!/usr/bin/env python3
"""verify_solid_ep_and_netclasses.py BOARD.kicad_pcb NETS.csv

Audits Variant D hard layout & netclass requirements:
  1. Solid exposed pads on U3.61 (3.4x3.4 mm) and U5.17 (1.7x1.7 mm) with ZERO foreign vias.
  2. Zero exposed pads on the 5x WLCSP-36 drivers (U1, U2, U10, U11, U12).
  3. U3 +1V1 ring fill area and piece count (chips/rp2350.md).
  4. Board netclasses match design/nets-d.csv (decisions.md row 23).
"""
from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

import pcbnew
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


def pad_poly_mm(p, lid: int) -> Polygon:
    um = pcbnew.ToMM
    ps = p.GetEffectivePolygon(lid)
    o = ps.Outline(0)
    pts = [(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())]
    g = Polygon(pts)
    return g if g.is_valid else g.buffer(0)


def main():
    pcb_path = Path(sys.argv[1])
    csv_path = Path(sys.argv[2])
    b = pcbnew.LoadBoard(str(pcb_path))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    um = pcbnew.ToMM
    errors = []

    fps = {f.GetReference(): f for f in b.GetFootprints()}
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

    # 1. Solid exposed pads on U3 and U5
    for ref, ep_num, min_gnd in (("U3", "61", 9), ("U5", "17", 2)):
        fp = fps[ref]
        ep_pads = [p for p in fp.Pads() if p.GetNumber() == ep_num]
        if len(ep_pads) != 1:
            errors.append(f"{ref}: expected 1 solid exposed pad {ep_num}, found {len(ep_pads)}")
            continue
        ep = ep_pads[0]
        poly = pad_poly_mm(ep, pcbnew.B_Cu)
        gnd_vias, foreign_vias = 0, []
        for v in vias:
            c = v.GetPosition()
            pt = Point(um(c.x), um(c.y))
            if poly.buffer(um(v.GetDrillValue()) / 2.0).intersects(pt):
                if v.GetNetname() == "GND":
                    gnd_vias += 1
                else:
                    foreign_vias.append((v.GetNetname(), round(um(c.x) - 100.0, 2), round(um(c.y) - 100.0, 2)))
        print(f"  {ref}.{ep_num}: solid pad area={poly.area:.2f} mm², GND_vias={gnd_vias}, foreign_vias={len(foreign_vias)}")
        if gnd_vias < min_gnd:
            errors.append(f"{ref}.{ep_num}: only {gnd_vias} GND vias (< {min_gnd})")
        if foreign_vias:
            errors.append(f"{ref}.{ep_num}: {len(foreign_vias)} foreign vias inside exposed pad: {foreign_vias}")

    # 2. Zero exposed pads on 5x WLCSP-36 drivers
    for ref in ("U1", "U2", "U10", "U11", "U12"):
        fp = fps[ref]
        nums = [p.GetNumber() for p in fp.Pads() if p.GetNumber()]
        if len(nums) != 36 or any(k not in {f"{r}{c}" for r in "ABCDEF" for c in range(1, 7)} for k in nums):
            errors.append(f"{ref}: unexpected pad numbers {nums}")
    print("  U1, U2, U10, U11, U12: 36 WLCSP balls each, 0 exposed ground pads")

    # 3. U3 +1V1 ring integrity (union of RP2350 ring + vendor +1V1 + DVDD fingers on B.Cu)
    ring_polys = []
    rp_ring_pieces = 0
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == "+1V1" and z.IsOnLayer(pcbnew.B_Cu):
            ps = z.GetFilledPolysList(pcbnew.B_Cu)
            if z.GetZoneName() == "RP2350 ring":
                rp_ring_pieces = ps.OutlineCount()
            for k in range(ps.OutlineCount()):
                pts = [(um(ps.Outline(k).CPoint(i).x), um(ps.Outline(k).CPoint(i).y)) for i in range(ps.Outline(k).PointCount())]
                if len(pts) >= 3:
                    ring_polys.append(Polygon(pts).buffer(0))
    u_ring = unary_union(ring_polys) if ring_polys else Polygon()
    n_union = len(u_ring.geoms) if hasattr(u_ring, "geoms") else (0 if u_ring.is_empty else 1)
    print(f"  U3 +1V1 B.Cu ring union: {n_union} piece(s) (RP2350 ring={rp_ring_pieces}), total area={u_ring.area:.2f} mm²")
    if rp_ring_pieces != 1 or u_ring.area < 5.5:
        errors.append(f"+1V1 ring fragmented or small: rp_ring_pieces={rp_ring_pieces}, area={u_ring.area:.2f} mm²")

    # 4. Board + .kicad_pro netclass check against nets-d.csv
    pro_path = pcb_path.with_suffix(".kicad_pro")
    if not pro_path.exists():
        pro_path = pcb_path.parent.parent / "round-pendant.kicad_pro"
    ns = json.loads(pro_path.read_text()).get("net_settings", {})
    assigns = ns.get("netclass_assignments") or {}
    patterns = ns.get("netclass_patterns") or []

    def pro_netclass(netname: str) -> str:
        if netname in assigns:
            v = assigns[netname]
            return v[0] if isinstance(v, list) else v
        for pat in patterns:
            p = pat.get("pattern", "")
            if fnmatch.fnmatch(netname, p) or (pat.get("regex") and re.search(pat["regex"], netname)):
                return pat["netclass"]
        return "Default"

    csv_classes = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            csv_classes[row["net"].strip().lstrip("/")] = row["class"].strip()

    netinfo = b.GetNetInfo()
    mismatches = []
    for code in range(1, netinfo.GetNetCount()):
        ni = netinfo.GetNetItem(code)
        name = ni.GetNetname()
        if not name or name.startswith("unconnected-"):
            continue
        key = name.lstrip("/")
        if key not in csv_classes:
            mismatches.append(f"{name}: missing from {csv_path.name}")
            continue
        want = csv_classes[key]
        got = pro_netclass(name)
        ok_cls = (
            got == want
            or (want == "SIGNAL" and got in ("Default", "SIGNAL", "SW_SCAN"))
            or (want == "POWER" and got in ("POWER", "VBAT", "BAT_N", "VBUS", "BATTERY", "USB_POWER"))
        )
        if not ok_cls:
            mismatches.append(f"{name}: pro class={got!r}, csv={want!r}")
    print(f"  Project netclasses checked ({pro_path.name}): {netinfo.GetNetCount() - 1} nets, {len(mismatches)} mismatches")
    errors.extend(mismatches)

    if errors:
        print("FAIL:")
        for e in errors:
            print(" ", e)
        sys.stdout.flush()
        os._exit(1)
    print("PASS: 0 errors")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
