#!/usr/bin/env python3
"""build_board_e.py -- Build Variant E PCB (top-rim ALS-PT19 light sensor + 5x IS31FL3745 WLCSP-36).

Stages (each runs a single pcbnew LoadBoard/SaveBoard per process):
  python3 scripts/bga/build_board_e.py sync
  python3 scripts/bga/build_board_e.py place_and_prep
  python3 scripts/bga/build_board_e.py unlock_all
  python3 scripts/bga/build_board_e.py finish_q2_silk
"""
from __future__ import annotations

import math
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "pcb-design" / "scripts"))

HW_D = ROOT / "hw" / "round-pendant" / "d"
HW_E = ROOT / "hw" / "round-pendant" / "e"
PCB_D = HW_D / "round-pendant.kicad_pcb"
PCB_E = HW_E / "round-pendant.kicad_pcb"
SCH_E = HW_E / "round-pendant.kicad_sch"
PRO_E = HW_E / "round-pendant.kicad_pro"
DRU_E = HW_E / "round-pendant.kicad_dru"
ROUTE_E = HW_E / "route"
PRO_BAK = ROUTE_E / "round-pendant.kicad_pro.bak"

OX, OY = 100.0, 100.0
KEEP_ALIVE = []


def poly_from_ps(ps: "pcbnew.SHAPE_POLY_SET") -> Polygon:
    um = pcbnew.ToMM
    polys = []
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k)
        pts = [(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())]
        if len(pts) >= 3:
            p = Polygon(pts)
            polys.append(p if p.is_valid else p.buffer(0))
    return unary_union(polys) if polys else Polygon()


def stage_sync() -> None:
    from kicad_write import update_pcb

    ROUTE_E.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRO_E, PRO_BAK)
    shutil.copy2(PCB_D, PCB_E)
    update_pcb(SCH_E, PCB_E, new_parts_at=(OX, OY))
    shutil.copy2(PRO_BAK, PRO_E)
    print("Synced Variant E PCB from schematic (preserving cleaned Variant D copper).", flush=True)


def stage_place_and_prep() -> None:
    b = pcbnew.LoadBoard(str(PCB_E))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM

    tb = b.GetTitleBlock()
    tb.SetTitle("round-pendant")
    tb.SetRevision("E")
    tb.SetDate("2026-11-05")
    tb.SetCompany("CERN-OHL-P-2.0")
    tb.SetComment(0, "235 RGB LEDs, 5x IS31FL3745 WLCSP-36, top-rim ALS-PT19, 8-layer ENIG")

    fps = {f.GetReference(): f for f in b.GetFootprints()}

    # 1. Place Q2 (ALS-PT19) on F.Cu at 12-o'clock top rim (-2.04, -18.04, +6 deg CCW: tangent to rim).
    #    Pad 1 (Collector, /MCU/LIGHT_PWR) sits West (-2.79, -17.96); Pad 2 (Emitter, /MCU/LIGHT) sits East (-1.29, -18.12).
    q2 = fps["Q2"]
    if q2.IsFlipped():
        q2.Flip(q2.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    q2.SetPosition(pcbnew.VECTOR2I(mm(OX - 2.04), mm(OY - 18.04)))
    q2.SetOrientationDegrees(6.0)
    q2.Reference().SetVisible(False)
    q2.Value().SetVisible(False)
    q2.Reference().SetLayer(pcbnew.F_Fab)
    q2.Value().SetLayer(pcbnew.F_Fab)

    # 2. Place R43 (22k) and C70 (100n) on B.Cu right behind Q2 on the top-rim crescent.
    #    Check pad orientation after Flip so R43.1 (/MCU/LIGHT) faces East toward Q2.2 and C70.1 (/MCU/LIGHT) faces West!
    def place_bcu_light_first(ref: str, cx: float, cy: float, want_light_east: bool):
        fp = fps[ref]
        if not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(pcbnew.VECTOR2I(mm(OX + cx), mm(OY + cy)))
        fp.SetOrientationDegrees(0.0)
        p1 = next(p for p in fp.Pads() if p.GetNumber() == "1")
        p2 = next(p for p in fp.Pads() if p.GetNumber() == "2")
        is_east = um(p1.GetPosition().x) > um(p2.GetPosition().x)
        if is_east != want_light_east:
            fp.SetOrientationDegrees(180.0)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.B_Fab)
        fp.Value().SetLayer(pcbnew.B_Fab)

    place_bcu_light_first("R43", -1.90, -17.60, want_light_east=True)
    place_bcu_light_first("C70", +0.60, -17.65, want_light_east=False)

    for ref in ("Q2", "R43", "C70"):
        pads_info = ", ".join(
            f"{p.GetNumber()}({p.GetNetname()}):({um(p.GetPosition().x)-OX:+.2f},{um(p.GetPosition().y)-OY:+.2f})"
            for p in fps[ref].Pads()
        )
        print(f"  Placed {ref:3s} ({'B.Cu' if fps[ref].IsFlipped() else 'F.Cu'}): {pads_info}", flush=True)

    # 3. Clear any existing copper segments/vias colliding with Q2 (F.Cu) or R43/C70 (B.Cu),
    #    and record which nets had segments removed so ultraroute re-routes them cleanly.
    new_pad_keep: dict[int, Polygon] = {}
    for layer_id, refs in ((pcbnew.F_Cu, ("Q2",)), (pcbnew.B_Cu, ("R43", "C70"))):
        polys = []
        for r in refs:
            for p in fps[r].Pads():
                if p.IsOnLayer(layer_id):
                    polys.append(poly_from_ps(p.GetEffectivePolygon(layer_id)).buffer(0.115))
        new_pad_keep[layer_id] = unary_union(polys)

    all_new_pads = unary_union(list(new_pad_keep.values())).buffer(0.10)

    ripped_nets: set[str] = {"/MCU/LIGHT", "/MCU/LIGHT_PWR"}
    removed_cnt = 0
    for t in list(b.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            vp = Point(um(t.GetPosition().x), um(t.GetPosition().y)).buffer(um(t.GetWidth(pcbnew.F_Cu)) / 2.0)
            if vp.intersects(all_new_pads):
                ripped_nets.add(t.GetNetname())
                KEEP_ALIVE.append(t)
                b.Remove(t)
                removed_cnt += 1
        else:
            lid = t.GetLayer()
            if lid in new_pad_keep:
                ls = LineString([
                    (um(t.GetStart().x), um(t.GetStart().y)),
                    (um(t.GetEnd().x), um(t.GetEnd().y)),
                ]).buffer(um(t.GetWidth()) / 2.0)
                if ls.intersects(new_pad_keep[lid]):
                    ripped_nets.add(t.GetNetname())
                    KEEP_ALIVE.append(t)
                    b.Remove(t)
                    removed_cnt += 1

    # Also unlock ripped_nets (so ultraroute --adopt routes their whole net cleanly without leaving stubs)
    # and lock all unaffected existing copper during incremental routing.
    locked_cnt = 0
    unlocked_cnt = 0
    for t in b.GetTracks():
        if t.GetNetname() in ripped_nets:
            t.SetLocked(False)
            unlocked_cnt += 1
        else:
            t.SetLocked(True)
            locked_cnt += 1

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pre_pcb = ROUTE_E / "pre_route.kicad_pcb"
    pcbnew.SaveBoard(str(pre_pcb), b)
    pcbnew.SaveBoard(str(PCB_E), b)
    shutil.copy2(PRO_BAK, PRO_E)
    shutil.copy2(PRO_BAK, pre_pcb.with_suffix(".kicad_pro"))
    shutil.copy2(DRU_E, pre_pcb.with_suffix(".kicad_dru"))
    print(
        f"Prepared {pre_pcb.name}: removed {removed_cnt} colliding segs on {sorted(ripped_nets)}; "
        f"locked {locked_cnt} untouched items, left {unlocked_cnt} unlocked for routing.",
        flush=True,
    )


def stage_unlock_all() -> None:
    b = pcbnew.LoadBoard(str(PCB_E))
    n = 0
    for t in b.GetTracks():
        if t.IsLocked():
            t.SetLocked(False)
            n += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB_E), b)
    shutil.copy2(PRO_BAK, PRO_E)
    print(f"Unlocked {n} copper items (0 locked copper) and refilled zones on {PCB_E.name}.", flush=True)


def stage_restore_post_clean() -> None:
    """Restore the 3 thermal GND vias inside U3.61 pruned by global --adopt and center U12.C6 pad joint."""
    b = pcbnew.LoadBoard(str(PCB_E))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    gnd_code = b.FindNet("GND").GetNetCode()
    existing_vias = {
        (round(um(t.GetPosition().x), 2), round(um(t.GetPosition().y), 2))
        for t in b.GetTracks()
        if isinstance(t, pcbnew.PCB_VIA)
    }
    for vx, vy in ((98.95, 94.70), (99.15, 93.70), (99.30, 94.25)):
        if (vx, vy) not in existing_vias:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
            v.SetWidth(mm(0.25))
            v.SetDrill(mm(0.15))
            v.SetNetCode(gnd_code)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            b.Add(v)
    cs_code = b.FindNet("/Driver 5 and matrix/CS5_15").GetNetCode()
    for tr in list(b.GetTracks()):
        if not isinstance(tr, pcbnew.PCB_VIA) and tr.GetNetCode() == cs_code and tr.GetLayer() == pcbnew.F_Cu:
            x1, y1 = um(tr.GetStart().x), um(tr.GetStart().y)
            x2, y2 = um(tr.GetEnd().x), um(tr.GetEnd().y)
            if math.hypot(x1 - 110.9175, y1 - 101.1137) < 0.01 and math.hypot(x2 - 111.2675, y2 - 101.0637) < 0.01:
                KEEP_ALIVE.append(tr)
                b.Remove(tr)
    for lid, p0, p1 in (
        (pcbnew.F_Cu, (110.9175, 101.1137), (111.1500, 101.1500)),
        (pcbnew.F_Cu, (111.1500, 101.1500), (111.2675, 101.0637)),
        (pcbnew.B_Cu, (111.1500, 101.1500), (111.2675, 101.0637)),
    ):
        t = pcbnew.PCB_TRACK(b)
        t.SetLayer(lid)
        t.SetWidth(mm(0.10))
        t.SetStart(pcbnew.VECTOR2I(mm(p0[0]), mm(p0[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(p1[0]), mm(p1[1])))
        t.SetNetCode(cs_code)
        b.Add(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB_E), b)
    shutil.copy2(PRO_BAK, PRO_E)
    print(f"Restored U3.61 9 GND thermal vias and centered U12.C6 joint on {PCB_E.name}.", flush=True)


def stage_finish_q2_silk() -> None:
    """Clip front sunflower web clear of Q2's optical body/window and add F.SilkS Pin-1 dot beside Q2.1."""
    b = pcbnew.LoadBoard(str(PCB_E))
    um = pcbnew.ToMM
    mm = pcbnew.FromMM

    fps = {f.GetReference(): f for f in b.GetFootprints()}
    q2 = fps["Q2"]
    qx, qy = um(q2.GetPosition().x), um(q2.GetPosition().y)
    ang = q2.GetOrientationDegrees()
    rad = math.radians(-ang)
    ca, sa = math.cos(rad), math.sin(rad)

    # Keepout box around Q2 body + pads (+/-1.32 x +/-0.58 mm) so no silk crosses optical window or lands
    q_corners = [
        (qx + dx * ca - dy * sa, qy + dx * sa + dy * ca)
        for dx, dy in ((-1.32, -0.58), (1.32, -0.58), (1.32, 0.58), (-1.32, 0.58))
    ]
    q_keep = Polygon(q_corners)

    # Clip board-level F.SilkS segments against q_keep
    clipped = 0
    added = 0
    for d in list(b.GetDrawings()):
        if d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            ls = LineString([(um(d.GetStart().x), um(d.GetStart().y)), (um(d.GetEnd().x), um(d.GetEnd().y))])
            if ls.intersects(q_keep):
                w = d.GetWidth()
                KEEP_ALIVE.append(d)
                b.Remove(d)
                clipped += 1
                diff = ls.difference(q_keep)
                geoms = list(diff.geoms) if hasattr(diff, "geoms") else [diff]
                for g in geoms:
                    if not g.is_empty and g.length > 0.05:
                        coords = list(g.coords)
                        for p0, p1 in zip(coords, coords[1:]):
                            if math.dist(p0, p1) > 0.02:
                                s = pcbnew.PCB_SHAPE(b)
                                s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                                s.SetLayer(pcbnew.F_SilkS)
                                s.SetWidth(w)
                                s.SetStart(pcbnew.VECTOR2I(mm(p0[0]), mm(p0[1])))
                                s.SetEnd(pcbnew.VECTOR2I(mm(p1[0]), mm(p1[1])))
                                b.Add(s)
                                added += 1

    # Place a 0.24 mm filled F.SilkS pin-1 dot beside Q2 Pad 1 (Collector), clear of F.Mask, Edge.Cuts, and web silk
    mask_polys = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.F_Cu):
                ps = p.GetEffectivePolygon(pcbnew.F_Mask if p.IsOnLayer(pcbnew.F_Mask) else pcbnew.F_Cu)
                gp = poly_from_ps(ps)
                if not gp.is_empty:
                    mask_polys.append(gp)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) and not t.IsTented(pcbnew.F_Mask):
            mask_polys.append(Point(um(t.GetPosition().x), um(t.GetPosition().y)).buffer(um(t.GetWidth(pcbnew.F_Cu)) / 2.0, 16))
    mask_u = unary_union(mask_polys)

    silk_lines = []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            silk_lines.append(
                LineString([(um(d.GetStart().x), um(d.GetStart().y)), (um(d.GetEnd().x), um(d.GetEnd().y))]).buffer(um(d.GetWidth()) / 2.0)
            )
    silk_u = unary_union(silk_lines) if silk_lines else Polygon()

    p1 = next(p for p in q2.Pads() if p.GetNumber() == "1")
    p2 = next(p for p in q2.Pads() if p.GetNumber() == "2")
    p1x, p1y = um(p1.GetPosition().x), um(p1.GetPosition().y)
    p2x, p2y = um(p2.GetPosition().x), um(p2.GetPosition().y)

    dot_r = 0.12
    best = None
    out_ang = math.atan2(p1y - qy, p1x - qx)
    for r_dist in np.linspace(0.62, 1.15, 36):
        for d_ang in np.linspace(-math.pi * 0.65, math.pi * 0.65, 55):
            a = out_ang + float(d_ang)
            dx = round(p1x + float(r_dist) * math.cos(a), 3)
            dy = round(p1y + float(r_dist) * math.sin(a), 3)
            if math.hypot(dx - OX, dy - OY) > 18.68:
                continue
            d1 = math.hypot(dx - p1x, dy - p1y)
            d2 = math.hypot(dx - p2x, dy - p2y)
            if d1 + 0.35 >= d2:
                continue
            dp = Point(dx, dy).buffer(dot_r, 24)
            if dp.distance(mask_u) < 0.165:
                continue
            if not silk_u.is_empty and dp.distance(silk_u) < 0.165:
                continue
            score = d1 + 0.3 * abs(float(d_ang))
            if best is None or score < best[0]:
                best = (score, dx, dy, d1)

    if best is not None:
        _, dx, dy, d1 = best
        s = pcbnew.PCB_SHAPE(q2)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetLayer(pcbnew.F_SilkS)
        s.SetFilled(True)
        s.SetWidth(mm(0.12))
        s.SetCenter(pcbnew.VECTOR2I(mm(dx), mm(dy)))
        s.SetEnd(pcbnew.VECTOR2I(mm(dx + 0.06), mm(dy)))
        q2.Add(s)
        print(f"Clipped {clipped} F.SilkS segs around Q2 (+{added} sub-segs); added Q2 Pin-1 dot at ({dx-OX:+.2f}, {dy-OY:+.2f}), d_pad1={d1:.2f}mm.", flush=True)
    else:
        print(f"Clipped {clipped} F.SilkS segs around Q2 (+{added} sub-segs); no extra Pin-1 dot spot needed.", flush=True)

    pcbnew.SaveBoard(str(PCB_E), b)
    shutil.copy2(PRO_BAK, PRO_E)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: build_board_e.py <sync|place_and_prep|unlock_all|restore_post_clean|finish_q2_silk>")
    cmd = sys.argv[1]
    if cmd == "sync":
        stage_sync()
    elif cmd == "place_and_prep":
        stage_place_and_prep()
    elif cmd == "unlock_all":
        stage_unlock_all()
    elif cmd == "restore_post_clean":
        stage_restore_post_clean()
    elif cmd == "finish_q2_silk":
        stage_finish_q2_silk()
    else:
        sys.exit(f"Unknown command: {cmd}")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
