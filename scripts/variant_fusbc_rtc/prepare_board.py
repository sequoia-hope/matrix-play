#!/usr/bin/env python3
"""prepare_board.py — Sync round-pendant-f-usbc-rtc schematics onto parent f-usbc PCB,
place inward-facing BT1 (A1251WR-S-2P, C225111) + SW/South support parts + East U13 (RX8130CE:BB, C1542426) RTC block,
add B.Cu rule area RX8130_xtal_end under U13's crystal inspection edge (ETM50E-10 Fig. 9 *1),
perform surgical zero-dangling local rip-up preserving all 236 front parts and all 147 locked RP2350 tracks,
and pre-place legal GND/VSYS plane vias + tight U13 decoupling links ready for ultraroute.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))

import pcbnew
from kicad_write import update_pcb

SRC_PCB = ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"
DST_DIR = ROOT / "hw/round-pendant/f-usbc-rtc"
DST_SCH = DST_DIR / "round-pendant.kicad_sch"
DST_PCB = DST_DIR / "round-pendant.kicad_pcb"
DST_PRO = DST_DIR / "round-pendant.kicad_pro"
DST_DRU = DST_DIR / "round-pendant.kicad_dru"
ROUTE_DIR = DST_DIR / "route"

# Verified 0-courtyard-overlap, 0-edge-violation, 0-placement_check-error constellation on B.Cu:
POSES = {
    # SW inward-facing 1.25 mm battery receptacle (mouth facing NNE +28 deg from North, 5.25+ mm clear runway)
    "BT1": ( 89.200, 110.550,  -28.00),
    # SW / South battery protection, VBAT_SENSE divider, U2 decouplers, and CC1/CC2 pull-downs
    "C43": ( 94.250, 112.000,  -90.00),
    "C40": ( 93.750, 114.550,  -90.00),
    "U8":  ( 91.500, 114.800,  -90.00),
    "C6":  ( 89.900, 114.300,  -90.00),
    "TP3": ( 95.250, 116.750,  180.00),
    "R8":  ( 97.000, 115.500,  180.00),
    "Q1":  ( 99.000, 116.250,  -90.00),
    "R9":  ( 97.500, 117.000,  -90.00),
    "R10": (100.500, 116.000,  -90.00),
    "R11": ( 99.250, 118.000,  180.00),
    "R12": (101.500, 116.000,  -90.00),
    "C7":  (101.250, 114.500,  180.00),
    "R1":  (102.500, 116.750,  -90.00),
    "R2":  (104.000, 117.000,  180.00),
    # East RX8130CE RTC pocket (0 existing parts moved; clears U12 CS5_12 via @(112.775,101.275)!)
    "U13": (114.750, 101.200,    0.00),
    "C75": (117.550, 101.050,    0.00),
    "C76": (117.550, 102.050,    0.00),
    "R32": (114.750,  98.350,    0.00),
}

FULL_RIP_NETS = {
    "/Power/BAT_N",
    "Net-(U8-VDD)",
    "/Power/CC1",
    "/Power/CC2",
    "VBAT_EN",
    "VBAT_SENSE",
    "Net-(Q1A-D)",
    "Net-(Q1B-D)",
    "/MCU/RTC_INT",
    "/MCU/RTC_VOUT",
    "CHG",
    "PGOOD",
}

PLANE_NETS = {"GND", "VSYS", "+3V3", "+1V1"}

um = pcbnew.ToMM
mm = lambda v: pcbnew.FromMM(float(v))
TOL = 3500


def is_via(t) -> bool:
    return isinstance(t, pcbnew.PCB_VIA)


def ends(t):
    return [t.GetPosition()] if is_via(t) else [t.GetStart(), t.GetEnd()]


def near(a, c, tol=TOL) -> bool:
    return abs(a.x - c.x) <= tol and abs(a.y - c.y) <= tol


def add_track(b, netcode: int, layer_id: int, x1: float, y1: float, x2: float, y2: float, w_mm: float, locked: bool = True):
    if math.hypot(x2 - x1, y2 - y1) < 1e-4:
        return None
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w_mm))
    t.SetLayer(layer_id)
    t.SetNetCode(netcode)
    t.SetLocked(locked)
    b.Add(t)
    return t


def add_via(b, netcode: int, x: float, y: float, width_mm: float = 0.25, drill_mm: float = 0.15, locked: bool = True):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(width_mm))
    v.SetDrill(mm(drill_mm))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(netcode)
    v.SetLocked(locked)
    b.Add(v)
    return v


def main():
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    # Sync .kicad_pro netclass assignments
    pro = json.loads(DST_PRO.read_text(encoding="utf-8"))
    nca = pro.setdefault("net_settings", {}).setdefault("netclass_assignments", {}) or {}
    nca["/MCU/RTC_INT"] = "SIGNAL"
    nca["/MCU/RTC_VOUT"] = "POWER"
    pro["net_settings"]["netclass_assignments"] = nca
    DST_PRO.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8")

    # Start cleanly from parent f-usbc PCB and run update_pcb from f-usbc-rtc schematic
    shutil.copy2(SRC_PCB, DST_PCB)
    update_pcb(DST_SCH, DST_PCB, new_parts_at=(114.3, 101.2))
    shutil.copy2(DST_PCB, ROUTE_DIR / "synced_post_eco.kicad_pcb")
    shutil.copy2(DST_PRO, ROUTE_DIR / "synced_post_eco.kicad_pro")
    shutil.copy2(DST_DRU, ROUTE_DIR / "synced_post_eco.kicad_dru")

    b_parent = pcbnew.LoadBoard(str(SRC_PCB))
    b = pcbnew.LoadBoard(str(DST_PCB))
    B_CU = b.GetLayerID("B.Cu")
    F_CU = b.GetLayerID("F.Cu")
    B_SILK = b.GetLayerID("B.SilkS")

    fps_parent = {f.GetReference(): f for f in b_parent.GetFootprints()}
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    # 1. Verify all 236 front parts match f-usbc 100%
    for ref, fp_p in fps_parent.items():
        if not fp_p.IsFlipped():
            f = fps[ref]
            dx = abs(um(fp_p.GetPosition().x - f.GetPosition().x))
            dy = abs(um(fp_p.GetPosition().y - f.GetPosition().y))
            da = abs((fp_p.GetOrientationDegrees() - f.GetOrientationDegrees() + 180) % 360 - 180)
            assert dx < 1e-4 and dy < 1e-4 and da < 1e-3, f"Front part {ref} moved!"
    print("Verified: 236 front parts (235 LEDs + Q2) 100% identical to f-usbc.")

    old_pads = {
        ref: [(p.GetNumber(), p.GetNetname(), p.GetPosition()) for p in fps_parent[ref].Pads()]
        for ref in POSES if ref in fps_parent
    }

    # 2. Flip new RTC parts to B.Cu and apply POSES
    for ref in ("U13", "C75", "C76", "R32"):
        f = fps[ref]
        if not f.IsFlipped():
            f.Flip(f.GetPosition(), False)

    for ref, (x, y, rot) in POSES.items():
        f = fps[ref]
        assert f.IsFlipped(), f"{ref} expected on B.Cu"
        f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        f.SetOrientationDegrees(rot)
        f.Reference().SetVisible(False)
        if ref == "BT1":
            f.SetLocked(True)

    # Remove inherited board-level B.SilkS items (polish_board.py places final silk cleanly after routing)
    for d in list(b.GetDrawings()):
        if d.GetLayer() == B_SILK:
            b.Remove(d)

    # 3. Add B.Cu rule area RX8130_xtal_end under U13's Pin 1..10 crystal inspection edge (ETM50E-10 Fig. 9 *1)
    # U13 at (114.75, 101.20, rot=0): pads are at x = 113.65±0.50 (inner 114.15) and x = 115.85±0.50 (inner 115.35),
    # Pin 1 & 10 at y = 102.75, body south edge at y = 102.80.
    # Rule area x=[114.30..115.20], y=[102.30..103.05] keeps B.Cu copper/vias/pours strictly out from under the *1 pads!
    ra = pcbnew.ZONE(b)
    ra.SetZoneName("RX8130_xtal_end")
    ra.SetIsRuleArea(True)
    ra.SetDoNotAllowTracks(True)
    ra.SetDoNotAllowVias(True)
    ra.SetDoNotAllowCopperPour(True)
    ra.SetDoNotAllowFootprints(False)
    ra.SetDoNotAllowPads(False)
    ls = pcbnew.LSET()
    ls.AddLayer(B_CU)
    ra.SetLayerSet(ls)
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for rx, ry in [(114.30, 102.30), (115.20, 102.30), (115.20, 103.05), (114.30, 103.05)]:
        poly.Append(mm(rx), mm(ry))
    poly.thisown = False
    ra.SetOutline(poly)
    ra.SetLocked(True)
    b.Add(ra)
    print("Added B.Cu rule area RX8130_xtal_end [114.30..115.20, 102.30..103.05] for ETM50E-10 *1 crystal inspection pads.")

    # 4. Surgical local copper rip-up
    items = list(b.GetTracks())
    all_pads = [p for f in b.GetFootprints() for p in f.Pads()]
    by_net = {}
    for i, t in enumerate(items):
        by_net.setdefault(t.GetNetname(), []).append(i)

    rip_idx = set()
    rip_reasons = {}

    def mark_rip(i: int, reason: str):
        if i not in rip_idx:
            rip_idx.add(i)
            rip_reasons.setdefault(items[i].GetNetname(), set()).add(reason)

    def walk_branch(seed_indices, reason: str, stop_at_pads: bool = True):
        stack = list(seed_indices)
        seed_set = set(seed_indices)
        while stack:
            i = stack.pop()
            if i in rip_idx:
                continue
            t = items[i]
            mark_rip(i, reason)
            net = t.GetNetname()
            npads = [p for p in all_pads if p.GetNetname() == net]
            for e in ends(t):
                if stop_at_pads and i not in seed_set and any(p.HitTest(e) for p in npads):
                    continue
                touching = [
                    j for j in by_net.get(net, [])
                    if j != i and any(near(e, f_end) for f_end in ends(items[j]))
                ]
                if i not in seed_set and not is_via(t) and len(touching) >= 2:
                    continue
                for j in touching:
                    if j not in rip_idx:
                        stack.append(j)

    # 4a. Full rip of moved local nets + VBAT south of C5/U5 (y > 106.6)
    for i, t in enumerate(items):
        nm = t.GetNetname()
        if nm in FULL_RIP_NETS:
            mark_rip(i, "moved_local_net")
        elif nm == "VBAT":
            if max(um(e.y) for e in ends(t)) > 106.60:
                mark_rip(i, "moved_VBAT_south")

    # 4b. Walk old GND and VSYS branches from old moved pads
    old_pad_seeds = []
    for ref, plist in old_pads.items():
        for pnum, pnet, ppos in plist:
            if pnet in ("GND", "VSYS"):
                for i in by_net.get(pnet, []):
                    t = items[i]
                    if any(near(e, ppos, tol=80000) for e in ends(t)) or t.HitTest(ppos):
                        old_pad_seeds.append(i)
    walk_branch(old_pad_seeds, "old_moved_pad_branch", stop_at_pads=True)

    # 4c. Check collisions against all 19 placed footprints' B.Cu pads AND RX8130_xtal_end!
    wlcsp_centers = [
        (um(fps[r].GetPosition().x), um(fps[r].GetPosition().y))
        for r in ("U1", "U2", "U10", "U11", "U12")
    ]

    def is_wlcsp_fanout_via(idx_item: int) -> bool:
        t = items[idx_item]
        if not is_via(t) or t.GetNetname() in PLANE_NETS or t.GetNetname() in FULL_RIP_NETS:
            return False
        vx, vy = um(t.GetPosition().x), um(t.GetPosition().y)
        return any(math.hypot(vx - cx, vy - cy) <= 2.55 for cx, cy in wlcsp_centers)

    clash_seeds = []
    xtal_box = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(114.25), mm(99.75)), pcbnew.VECTOR2I(mm(1.00), mm(3.35)))
    xtal_sh = pcbnew.SHAPE_RECT(xtal_box)
    for i, t in enumerate(items):
        if i in rip_idx:
            continue
        if is_via(t):
            if t.GetEffectiveShape(B_CU).Collide(xtal_sh, mm(0.10)):
                clash_seeds.append(i)
        elif t.GetLayer() == B_CU:
            if t.GetEffectiveShape(B_CU).Collide(xtal_sh, mm(0.10)):
                clash_seeds.append(i)

    moving_pads = [p for ref in POSES for p in fps[ref].Pads() if p.IsOnLayer(B_CU)]
    for p in moving_pads:
        pnet = p.GetNetname()
        clr = 0.165 if "USB_D" in pnet else 0.115
        pshape = p.GetEffectiveShape(B_CU)
        for i, t in enumerate(items):
            if i in rip_idx:
                continue
            tnet = t.GetNetname()
            if is_via(t):
                vpos = t.GetPosition()
                v_r = um(t.GetWidth(B_CU)) / 2.0
                v_dr = um(t.GetDrill()) / 2.0
                c_cu = pcbnew.SHAPE_CIRCLE(vpos, mm(v_r + (0.01 if tnet == pnet else clr)))
                c_hl = pcbnew.SHAPE_CIRCLE(vpos, mm(v_dr + (0.01 if tnet == pnet else 0.215)))
                if pshape.Collide(c_cu) or pshape.Collide(c_hl):
                    clash_seeds.append(i)
            elif t.GetLayer() == B_CU:
                if pshape.Collide(t.GetEffectiveShape(B_CU), mm(0.01 if tnet == pnet else clr)):
                    clash_seeds.append(i)

    clash_seed_set = set(clash_seeds)
    # Walk clash_seeds, stopping at non-colliding WLCSP fanout vias so U1/U2/U10/U11/U12 BGA escapes stay 100% intact!
    stack = list(clash_seeds)
    while stack:
        i = stack.pop()
        if i in rip_idx:
            continue
        if i not in clash_seed_set and is_wlcsp_fanout_via(i):
            continue
        t = items[i]
        mark_rip(i, "pad_or_rule_collision")
        net = t.GetNetname()
        npads = [p for p in all_pads if p.GetNetname() == net]
        for e in ends(t):
            if i not in clash_seed_set and any(p.HitTest(e) for p in npads):
                continue
            touching = [
                j for j in by_net.get(net, [])
                if j != i and any(near(e, f_end) for f_end in ends(items[j]))
            ]
            if i not in clash_seed_set and not is_via(t) and len(touching) >= 2:
                continue
            for j in touching:
                if j not in rip_idx and not (j not in clash_seed_set and is_wlcsp_fanout_via(j)):
                    stack.append(j)

    # Also unlock (rip) F.Cu LED daisy-chain stubs ONLY for matrix nets that lost a via in clash_seeds,
    # within 4.0 mm of the ripped items so trapped LEDs (e.g. D4, D91, D196) can step 1 LED hop on F.Cu!
    clash_matrix_nets = {items[i].GetNetname() for i in rip_idx if "/SW" in items[i].GetNetname() or "/CS" in items[i].GetNetname()}
    ripped_pts = [(um(e.x), um(e.y)) for i in list(rip_idx) for e in ends(items[i])]
    fcu_local = []
    for i, t in enumerate(items):
        if i in rip_idx or is_via(t) or t.GetLayer() != F_CU or t.GetNetname() not in clash_matrix_nets:
            continue
        sx, sy = um(t.GetStart().x), um(t.GetStart().y)
        if any(math.hypot(sx - rx, sy - ry) <= 3.8 for rx, ry in ripped_pts):
            fcu_local.append(i)
    walk_branch(fcu_local, "fcu_touched_net_escape", stop_at_pads=False)

    # 4e. Iterative zero-dangling dead-end pruner ONLY on touched nets!
    touched_nets = set(rip_reasons.keys())
    pruned_dangling = 0
    changed = True
    while changed:
        changed = False
        alive = [i for i in range(len(items)) if i not in rip_idx]
        alive_by_net = {}
        for i in alive:
            nm = items[i].GetNetname()
            if nm in touched_nets:
                alive_by_net.setdefault(nm, []).append(i)

        for nm, peers in alive_by_net.items():
            if nm in ("+1V1", "+3V3"):
                continue
            npads = [p for p in all_pads if p.GetNetname() == nm]
            for i in list(peers):
                if i in rip_idx:
                    continue
                t = items[i]
                if is_via(t):
                    pos = t.GetPosition()
                    if nm in PLANE_NETS:
                        has_conn = any(p.HitTest(pos) for p in npads) or any(
                            j != i and (any(near(pos, e) for e in ends(items[j])) or items[j].HitTest(pos, mm(0.01)))
                            for j in peers if j not in rip_idx
                        )
                        if not has_conn:
                            mark_rip(i, "orphan_plane_via")
                            pruned_dangling += 1
                            changed = True
                    else:
                        cu_layers = [lid for lid in range(64) if b.IsLayerEnabled(lid) and b.GetLayerName(lid).endswith(".Cu")]
                        layers_touched = set()
                        for p in npads:
                            if p.HitTest(pos):
                                for lid in cu_layers:
                                    if p.IsOnLayer(lid):
                                        layers_touched.add(lid)
                        for j in peers:
                            if j != i and j not in rip_idx and not is_via(items[j]):
                                if any(near(pos, e) for e in ends(items[j])) or items[j].HitTest(pos, mm(0.01)):
                                    layers_touched.add(items[j].GetLayer())
                        if len(layers_touched) < 2 and not is_wlcsp_fanout_via(i):
                            mark_rip(i, "dangling_via_prune")
                            pruned_dangling += 1
                            changed = True
                else:
                    l = t.GetLayer()
                    dangling_end = False
                    end_pads = []
                    for e in (t.GetStart(), t.GetEnd()):
                        hit_p = next((p for p in npads if p.IsOnLayer(l) and p.HitTest(e)), None)
                        ex, ey = um(e.x), um(e.y)
                        on_peer = False
                        for j in peers:
                            if j == i or j in rip_idx:
                                continue
                            tj = items[j]
                            if is_via(tj):
                                if near(e, tj.GetPosition(), tol=2500):
                                    on_peer = True
                                    break
                            elif tj.GetLayer() == l:
                                if any(near(e, pe, tol=2500) for pe in ends(tj)):
                                    on_peer = True
                                    break
                                s_j, e_j = tj.GetStart(), tj.GetEnd()
                                if LineString([(um(s_j.x), um(s_j.y)), (um(e_j.x), um(e_j.y))]).distance(Point(ex, ey)) <= 0.0025:
                                    on_peer = True
                                    break
                        end_pads.append((hit_p.GetPosition().x, hit_p.GetPosition().y) if hit_p is not None else None)
                        if hit_p is None and not on_peer:
                            dangling_end = True
                            break
                    if not dangling_end and end_pads[0] is not None and end_pads[0] == end_pads[1] and um(t.GetLength()) < 0.25:
                        dangling_end = True
                    if dangling_end:
                        mark_rip(i, "dangling_track_prune")
                        pruned_dangling += 1
                        changed = True

    ripped_items = [items[i] for i in sorted(rip_idx)]
    rip_vias = [t for t in ripped_items if is_via(t)]
    rip_trks = [t for t in ripped_items if not is_via(t)]
    ripped_nets = sorted({t.GetNetname() for t in ripped_items})
    print(f"Local rip-up: {len(rip_trks)} track segs + {len(rip_vias)} vias across {len(ripped_nets)} nets (pruned {pruned_dangling} dangling).")

    for t in ripped_items:
        b.Remove(t)

    # Bridge any pad whose stub was ripped while an adjacent same-net track still grazes its edge (<0.09 mm connection_width)
    surviving_trks = [t for t in b.GetTracks() if not is_via(t)]
    connected_pcs = set()
    for p in all_pads:
        nm = p.GetNetname()
        if nm not in touched_nets:
            continue
        pc = p.GetPosition()
        for t2 in surviving_trks:
            if t2.GetNetname() == nm and p.IsOnLayer(t2.GetLayer()) and any(near(pc, e2, tol=5000) for e2 in ends(t2)):
                connected_pcs.add((p.GetParentAsString(), p.GetNumber(), t2.GetLayer()))
                break

    snapped_pads = 0
    for p in all_pads:
        nm = p.GetNetname()
        if nm not in touched_nets:
            continue
        pc = p.GetPosition()
        for lid in (F_CU, B_CU):
            if not p.IsOnLayer(lid) or (p.GetParentAsString(), p.GetNumber(), lid) in connected_pcs:
                continue
            ps = p.GetEffectiveShape(lid)
            for t in surviving_trks:
                if t.GetNetname() == nm and t.GetLayer() == lid and ps.Collide(t.GetEffectiveShape(lid), 0):
                    # Bridge pad center to nearest endpoint of t
                    s, e = t.GetStart(), t.GetEnd()
                    ep = s if math.hypot(pc.x - s.x, pc.y - s.y) <= math.hypot(pc.x - e.x, pc.y - e.y) else e
                    add_track(b, t.GetNetCode(), lid, um(ep.x), um(ep.y), um(pc.x), um(pc.y), um(t.GetWidth()), locked=True)
                    connected_pcs.add((p.GetParentAsString(), p.GetNumber(), lid))
                    snapped_pads += 1
                    break
    if snapped_pads:
        print(f"Bridged {snapped_pads} pad-grazing endpoints to exact pad centers.")

    # Lock 100% of surviving copper so ultraroute --strip keeps all intact routes untouched!
    for t in b.GetTracks():
        t.SetLocked(True)

    # 5. Pre-route tight datasheet local B.Cu links on U13 (RX8130CE) & U8 bar
    gnd_code = b.FindNet("GND").GetNetCode()
    vsys_code = b.FindNet("VSYS").GetNetCode()
    p3v3_code = b.FindNet("+3V3").GetNetCode()
    vout_code = b.FindNet("/MCU/RTC_VOUT").GetNetCode()
    rtc_int_code = b.FindNet("/MCU/RTC_INT").GetNetCode()

    def pad_xy(ref: str, num: str) -> tuple[float, float]:
        p = next(p for p in fps[ref].Pads() if p.GetNumber() == num)
        return (um(p.GetPosition().x), um(p.GetPosition().y))

    # U13 local decoupling & pull-up links (all non-crossing and clear of RX8130_xtal_end [114.30..115.20, 99.80..103.05]):
    #   U13.8 (+3V3, 115.85, 101.20) -> C75.1 (+3V3, 116.87, 101.05) (1.03 mm straight east!)
    p_u13_8 = pad_xy("U13", "8")
    p_c75_1 = pad_xy("C75", "1")
    add_track(b, p3v3_code, B_CU, p_u13_8[0], p_u13_8[1], 116.40, p_u13_8[1], 0.20, locked=True)
    add_track(b, p3v3_code, B_CU, 116.40, p_u13_8[1], p_c75_1[0], p_c75_1[1], 0.20, locked=True)

    #   U13.9 (RTC_VOUT, 115.85, 101.90) -> C76.1 (RTC_VOUT, 116.87, 102.05) (1.03 mm straight east!)
    p_u13_9 = pad_xy("U13", "9")
    p_c76_1 = pad_xy("C76", "1")
    add_track(b, vout_code, B_CU, p_u13_9[0], p_u13_9[1], 116.40, p_u13_9[1], 0.20, locked=True)
    add_track(b, vout_code, B_CU, 116.40, p_u13_9[1], p_c76_1[0], p_c76_1[1], 0.20, locked=True)

    #   U13.7 (GND, 115.85, 100.50) -> C75.2 (GND, 117.83, 101.05) around north of C75
    p_u13_7 = pad_xy("U13", "7")
    p_c75_2 = pad_xy("C75", "2")
    add_track(b, gnd_code, B_CU, p_u13_7[0], p_u13_7[1], p_c75_2[0], p_u13_7[1], 0.20, locked=True)
    add_track(b, gnd_code, B_CU, p_c75_2[0], p_u13_7[1], p_c75_2[0], p_c75_2[1], 0.20, locked=True)

    #   U13.6 (/IRQ, 115.85, 99.65) -> R32.2 (115.26, 98.35),
    #   PLUS U3.31 (102.0375, 90.60) B.Cu escape out to (102.650, 90.600) past RP2350 band (x=102.10)!
    p_u13_6 = pad_xy("U13", "6")
    p_r32_2 = pad_xy("R32", "2")
    p_u3_31 = pad_xy("U3", "31")
    add_track(b, rtc_int_code, B_CU, p_u13_6[0], p_u13_6[1], p_u13_6[0], p_r32_2[1], 0.15, locked=True)
    add_track(b, rtc_int_code, B_CU, p_u13_6[0], p_r32_2[1], p_r32_2[0], p_r32_2[1], 0.15, locked=True)
    add_track(b, rtc_int_code, B_CU, p_u3_31[0], p_u3_31[1], 102.650, p_u3_31[1], 0.10, locked=True)

    # Tie U8's small pads 1,2,3 to U8's pad 1 bar center on B.Cu
    u8_bar = next(p for p in fps["U8"].Pads() if p.GetNumber() == "1" and um(p.GetSize().x) >= 0.8)
    bx, by = um(u8_bar.GetPosition().x), um(u8_bar.GetPosition().y)
    for p in fps["U8"].Pads():
        if p.GetNumber() in ("1", "2", "3") and p != u8_bar:
            add_track(b, gnd_code, B_CU, bx, by, um(p.GetPosition().x), um(p.GetPosition().y), 0.20, locked=True)

    # 6. Place verified legal locked plane vias (GND -> In2.Cu, VSYS -> In5.Cu) for all moved/new pads!
    rule_areas = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    npth_pts = [
        (um(p.GetPosition().x), um(p.GetPosition().y), um(p.GetDrillSize().x) / 2.0)
        for f in b.GetFootprints() for p in f.Pads()
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
    ]
    board_pads = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            px_c, py_c = um(p.GetPosition().x), um(p.GetPosition().y)
            sh_f = p.GetEffectiveShape(F_CU) if p.IsOnLayer(F_CU) else None
            sh_b = p.GetEffectiveShape(B_CU) if p.IsOnLayer(B_CU) else None
            board_pads.append((px_c, py_c, p.GetNetname(), p, sh_f, sh_b))

    def build_all_tracks():
        out = []
        for t in b.GetTracks():
            if is_via(t):
                tpos = t.GetPosition()
                tx, ty = um(tpos.x), um(tpos.y)
                out.append(("V", tx, ty, tx, ty, t.GetNetname(), um(t.GetWidth(B_CU)) / 2.0, um(t.GetDrill()) / 2.0, B_CU, t.GetEffectiveShape(B_CU)))
            else:
                s, e = t.GetStart(), t.GetEnd()
                x1, y1, x2, y2 = um(s.x), um(s.y), um(e.x), um(e.y)
                l = t.GetLayer()
                out.append(("T", min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), t.GetNetname(), 0.0, 0.0, l, t.GetEffectiveShape(l)))
        return out

    def can_place_plane_via(ppos, vx: float, vy: float, target_net: str, trks, vr=0.125, vdr=0.075, stub_w=0.20) -> bool:
        if math.hypot(vx - 100.0, vy - 100.0) > 19.0 - vr - 0.32:
            return False
        vp = pcbnew.VECTOR2I(mm(vx), mm(vy))
        for r_area in rule_areas:
            if r_area.Outline().Contains(vp):
                return False
        for nx, ny, nr in npth_pts:
            if math.hypot(vx - nx, vy - ny) < nr + max(vdr, vr) + 0.215:
                return False
        c_cu_def = pcbnew.SHAPE_CIRCLE(vp, mm(vr + 0.110))
        c_cu_usb = pcbnew.SHAPE_CIRCLE(vp, mm(vr + 0.165))
        c_hl = pcbnew.SHAPE_CIRCLE(vp, mm(vdr + 0.210))

        for px_c, py_c, pnet, p, sh_f, sh_b in board_pads:
            if abs(px_c - vx) > 2.8 or abs(py_c - vy) > 2.8:
                continue
            if pnet == target_net:
                # Allow via inside large BT1 MP pads, otherwise keep outside SMD pads
                if p.HitTest(vp) and um(p.GetSize().x) < 1.8:
                    return False
                continue
            cc = c_cu_usb if "USB_D" in pnet else c_cu_def
            for sh in (sh_f, sh_b):
                if sh is not None and (sh.Collide(cc) or sh.Collide(c_hl)):
                    return False

        for kind, x1, y1, x2, y2, tnet, tr, tdr, l, ts in trks:
            if vx < x1 - 1.2 or vx > x2 + 1.2 or vy < y1 - 1.2 or vy > y2 + 1.2:
                continue
            same = (tnet == target_net)
            if kind == "V":
                if math.hypot(x1 - vx, y1 - vy) < vdr + tdr + 0.210:
                    return False
                if not same:
                    clr = 0.165 if "USB_D" in tnet else 0.110
                    if math.hypot(x1 - vx, y1 - vy) < vr + tr + clr:
                        return False
            else:
                if same:
                    continue
                cc = c_cu_usb if "USB_D" in tnet else c_cu_def
                if ts.Collide(cc) or ts.Collide(c_hl):
                    return False

        if ppos.x != vp.x or ppos.y != vp.y:
            sx1, sy1 = min(um(ppos.x), vx) - 1.2, min(um(ppos.y), vy) - 1.2
            sx2, sy2 = max(um(ppos.x), vx) + 1.2, max(um(ppos.y), vy) + 1.2
            tmp = pcbnew.PCB_TRACK(b)
            tmp.SetStart(ppos)
            tmp.SetEnd(vp)
            tmp.SetWidth(mm(stub_w))
            tmp.SetLayer(B_CU)
            sts = tmp.GetEffectiveShape(B_CU)
            for r_area in rule_areas:
                if B_CU in list(r_area.GetLayerSet().Seq()) and r_area.Outline().Collide(sts):
                    return False
            for px_c, py_c, pnet, p, sh_f, sh_b in board_pads:
                if pnet == target_net or sh_b is None or px_c < sx1 or px_c > sx2 or py_c < sy1 or py_c > sy2:
                    continue
                clr = 0.165 if "USB_D" in pnet else 0.110
                if sts.Collide(sh_b, mm(clr)):
                    return False
            for kind, x1, y1, x2, y2, tnet, tr, tdr, l, ts in trks:
                if tnet == target_net or x2 < sx1 or x1 > sx2 or y2 < sy1 or y1 > sy2:
                    continue
                if kind == "V":
                    clr_cu = 0.165 if "USB_D" in tnet else 0.110
                    v_hl = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(x1), mm(y1)), mm(tdr + 0.210))
                    if sts.Collide(ts, mm(clr_cu)) or sts.Collide(v_hl):
                        return False
                elif l == B_CU:
                    clr = 0.165 if "USB_D" in tnet else 0.110
                    if sts.Collide(ts, mm(clr)):
                        return False
        return True

    plane_targets = []
    for ref in POSES:
        for p in fps[ref].Pads():
            pnet = p.GetNetname()
            if pnet in ("GND", "VSYS") and p.IsOnLayer(B_CU):
                if ref == "U8" and p.GetNumber() in ("2", "3"):
                    continue
                if ref == "U8" and p.GetNumber() == "1" and um(p.GetSize().x) < 0.8:
                    continue
                if ref == "U13" and p.GetNumber() == "7":
                    continue  # shared with C75.2!
                plane_targets.append((f"{ref}.{p.GetNumber()}", p, pnet, 2 if ref == "U8" else 1))

    placed_plane = 0
    total_needed = sum(cnt for _, _, _, cnt in plane_targets)
    for label, pad_obj, pnet, count_needed in plane_targets:
        netcode = gnd_code if pnet == "GND" else vsys_code
        vw = 0.30 if (label.startswith("U8.") or pnet == "VSYS") else 0.25
        px, py = um(pad_obj.GetPosition().x), um(pad_obj.GetPosition().y)
        ppos = pad_obj.GetPosition()
        start_ri = 0 if label.startswith("BT1.MP") else 10
        got = 0
        for _ in range(count_needed):
            trks = build_all_tracks()
            found = None
            for ri in range(start_ri, 56):
                rad = ri * 0.05
                n_ang = 1 if rad == 0 else max(24, int(2 * math.pi * rad / 0.08))
                for ai in range(n_ang):
                    ang = 2 * math.pi * ai / n_ang
                    vx = round(px + rad * math.cos(ang), 3)
                    vy = round(py + rad * math.sin(ang), 3)
                    if can_place_plane_via(ppos, vx, vy, pnet, trks, vr=vw / 2.0, vdr=0.075, stub_w=min(0.25, vw)):
                        found = (vx, vy)
                        break
                if found:
                    break
            if found:
                vx, vy = found
                add_via(b, netcode, vx, vy, width_mm=vw, drill_mm=0.15, locked=True)
                add_track(b, netcode, B_CU, px, py, vx, vy, min(0.25, vw), locked=True)
                placed_plane += 1
                got += 1
                print(f"  Placed locked {pnet:4s} via ({vw:.2f}/0.15) for {label:8s}: ({px:.3f},{py:.3f}) -> ({vx:.3f},{vy:.3f})")
            else:
                print(f"  NOTE: router will connect {pnet} for {label} at ({px:.3f},{py:.3f})")

    # 7. Verify all 147 locked RP2350 decoupling tracks survive 100% intact!
    def item_sig(t, brd):
        if is_via(t):
            p = t.GetPosition()
            return ("V", t.GetNetname(), p.x, p.y, t.GetDrill())
        return ("T", t.GetNetname(), brd.GetLayerName(t.GetLayer()), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth())

    b_locked = {item_sig(t, b) for t in b.GetTracks() if t.IsLocked()}
    f_decap = [
        t for t in b_parent.GetTracks()
        if not is_via(t) and t.GetNetname() in ("+3V3", "+1V1") and um(t.GetStart().y) < 102.0 and t.IsLocked()
    ]
    for t in f_decap:
        assert item_sig(t, b_parent) in b_locked, f"CRITICAL: RP2350 decap track missing: {item_sig(t, b_parent)}"
    print(f"Verified: all {len(f_decap)} locked RP2350 +3V3/+1V1 decoupling tracks survive 100% intact & locked.")

    tb = b.GetTitleBlock()
    tb.SetRevision("FUR")
    tb.SetDate("2026-11-09")

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(str(DST_PCB), b)
    shutil.copy2(DST_PCB, ROUTE_DIR / "pre_autoroute.kicad_pcb")
    shutil.copy2(DST_PRO, ROUTE_DIR / "pre_autoroute.kicad_pro")
    shutil.copy2(DST_DRU, ROUTE_DIR / "pre_autoroute.kicad_dru")
    print(f"Saved {DST_PCB} ({placed_plane}/{total_needed} plane vias pre-placed).")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
