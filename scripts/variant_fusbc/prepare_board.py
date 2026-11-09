#!/usr/bin/env python3
"""prepare_board.py — Place J1 (TYPE-C-31-M-22) and the 8 displaced B.Cu parts on f-usbc,
pre-route locked 0-via B.Cu USB_DP/USB_DM links into U7 and locked legal GND plane vias/stubs,
update B.SilkS pin-1 dots & clip F.SilkS Voronoi art clear of J1's two NPTHs,
and perform a surgical zero-dangling local branch rip-up while keeping all 235 front LEDs
and Variant F's locked RP2350 decoupling tracks 100% untouched.
"""
import math
import os
import shutil
import sys
import pcbnew
from shapely.geometry import LineString, Point

BOARD_F = "hw/round-pendant/f/round-pendant.kicad_pcb"
PRO_F = "hw/round-pendant/f/round-pendant.kicad_pro"
IN_PCB = "hw/round-pendant/f-usbc/route/synced_post_eco.kicad_pcb"
OUT_PCB = "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"
OUT_PRO = "hw/round-pendant/f-usbc/round-pendant.kicad_pro"

# Verified zero-courtyard-overlap, zero-LED-move, zero-U2-escape-collision constellation on B.Cu:
POSES = {
    "J1":  (107.787, 110.926, 203.95),
    "U7":  (100.100, 112.400, 113.95),
    "C1":  (102.500, 108.800, 180.00),
    "R5":  (107.500, 106.400,  90.00),
    "BT1": (100.000, 117.100, 180.00),
    "U8":  ( 96.400, 116.400, 270.00),
    "C6":  ( 94.500, 116.600, 180.00),
    "R8":  ( 99.700, 115.000, 180.00),
    "TP3": (104.000, 117.500, 180.00),
}

# Self-contained local nets whose endpoints moved -> rip 100% cleanly
FULL_RIP_NETS = {
    "VBUS",
    "/Power/USB_DP_C",
    "/Power/USB_DM_C",
    "/Power/CC1",
    "/Power/CC2",
    "/Power/BAT_N",
    "Net-(U8-VDD)",
    "Net-(U5-ILIM)",
    "Net-(U5-ISET)",  # tiny 2-pin R4.1->U5.16 net whose old via sat in USB_DP's B.Cu lane
}

PLANE_NETS = {"GND", "VSYS", "+3V3", "+1V1"}

um = pcbnew.ToMM
mm = lambda v: pcbnew.FromMM(float(v))
TOL = 3500  # nm endpoint match tolerance


def is_via(t):
    return isinstance(t, pcbnew.PCB_VIA)


def ends(t):
    return [t.GetPosition()] if is_via(t) else [t.GetStart(), t.GetEnd()]


def near(a, c, tol=TOL):
    return abs(a.x - c.x) <= tol and abs(a.y - c.y) <= tol


def add_track(b, netcode, layer_id, x1, y1, x2, y2, w_mm, locked=True):
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


def add_via(b, netcode, x, y, width_mm=0.25, drill_mm=0.15, locked=True):
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
    bf = pcbnew.LoadBoard(BOARD_F)
    # Ensure .kicad_pro sits beside IN_PCB before loading so LoadBoard keeps all netclasses
    shutil.copy2(PRO_F, "hw/round-pendant/f-usbc/route/synced_post_eco.kicad_pro")
    b = pcbnew.LoadBoard(IN_PCB)

    fps_f = {f.GetReference(): f for f in bf.GetFootprints()}
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    # 1. Verify all 235 LEDs + Q2 match Board F 100%
    for ref, ff in fps_f.items():
        if not ff.IsFlipped():
            f = fps[ref]
            dx = abs(um(ff.GetPosition().x - f.GetPosition().x))
            dy = abs(um(ff.GetPosition().y - f.GetPosition().y))
            da = abs((ff.GetOrientationDegrees() - f.GetOrientationDegrees() + 180) % 360 - 180)
            assert dx < 1e-4 and dy < 1e-4 and da < 1e-3, f"Front part {ref} moved!"
    print("Verified: 236 front parts (235 LEDs + Q2) 100% identical to Board F.")

    old_pads = {
        ref: [(p.GetNumber(), p.GetNetname(), p.GetPosition()) for p in fps_f[ref].Pads()]
        for ref in POSES
    }

    # 2. Place J1 and the 8 displaced B.Cu footprints
    for ref, (x, y, rot) in POSES.items():
        f = fps[ref]
        assert f.IsFlipped(), f"{ref} expected on B.Cu"
        f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        f.SetOrientationDegrees(rot)
        if ref == "J1":
            f.SetLocked(True)

    # Set DRC- & silk_check-compliant designator positions/sizes (w=0.15 mm, h=0.80 mm)
    desig_updates = {
        "J1":  (112.60, 105.05, 0.0, True),
        "C1":  (102.50, 109.75, 0.0, False),
        "R5":  (108.55, 106.40, 0.0, False),
        "U7":  ( 99.50, 110.20, 0.0, False),
        "BT1": (100.00, 115.65, 0.0, False),
        "TP3": (105.45, 116.80, 0.0, False),
        "U8":  ( 96.40, 114.80, 0.0, False),
        "C6":  ( 94.50, 115.70, 0.0, False),
        "R8":  ( 99.70, 114.10, 0.0, False),
        "R1":  ( 92.80, 115.60, 0.0, False),
        "R4":  ( 99.20, 108.35, 0.0, False),
        "TP1": (108.85, 104.30, 0.0, False),
        "U5":  (103.40, 103.30, 0.0, False),
        "U2":  ( 96.50, 109.95, 0.0, False),
    }
    for ref, (tx, ty, trot, vis) in desig_updates.items():
        rt = fps[ref].Reference()
        rt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        rt.SetTextThickness(mm(0.15))
        rt.SetPosition(pcbnew.VECTOR2I(mm(tx), mm(ty)))
        rt.SetTextAngleDegrees(trot)
        rt.SetVisible(vis)

    # 3. Update B.SilkS IC pin-1 dots for U7 and U8, and clip F.SilkS Voronoi around J1 NPTHs
    B_SILK = b.GetLayerID("B.SilkS")
    F_SILK = b.GetLayerID("F.SilkS")

    u7_p1 = next(p.GetPosition() for p in fps["U7"].Pads() if p.GetNumber() == "1")
    u8_p1 = next(
        p.GetPosition() for p in fps["U8"].Pads()
        if p.GetNumber() == "1" and um(p.GetSize().x) < 0.8
    )

    moved_dots = 0
    for d in list(b.GetDrawings()):
        if d.GetLayer() == B_SILK and isinstance(d, pcbnew.PCB_SHAPE):
            cx, cy = um(d.GetBoundingBox().GetCenter().x), um(d.GetBoundingBox().GetCenter().y)
            if math.hypot(cx - 103.71, cy - 108.86) < 0.5:
                ux, uy = POSES["U7"][0], POSES["U7"][1]
                px, py = um(u7_p1.x), um(u7_p1.y)
                vx, vy = px - ux, py - uy
                vl = math.hypot(vx, vy)
                nx, ny = px + 0.50 * (vx / vl), py + 0.50 * (vy / vl)
                r = um(d.GetEnd().x - d.GetStart().x)
                d.SetStart(pcbnew.VECTOR2I(mm(nx - r / 2), mm(ny)))
                d.SetEnd(pcbnew.VECTOR2I(mm(nx + r / 2), mm(ny)))
                moved_dots += 1
            elif math.hypot(cx - 106.60, cy - 113.81) < 0.5:
                ux, uy = POSES["U8"][0], POSES["U8"][1]
                px, py = um(u8_p1.x), um(u8_p1.y)
                vx, vy = px - ux, py - uy
                vl = math.hypot(vx, vy)
                nx, ny = px + 0.52 * (vx / vl), py + 0.52 * (vy / vl)
                r = um(d.GetEnd().x - d.GetStart().x)
                d.SetStart(pcbnew.VECTOR2I(mm(nx - r / 2), mm(ny)))
                d.SetEnd(pcbnew.VECTOR2I(mm(nx + r / 2), mm(ny)))
                moved_dots += 1
    print(f"Relocated {moved_dots} B.SilkS IC pin-1 dots (U7, U8).")

    npth_pts = [
        (um(p.GetPosition().x), um(p.GetPosition().y))
        for p in fps["J1"].Pads()
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
    ]
    clip_union = Point(npth_pts[0]).buffer(0.60, resolution=64).union(
        Point(npth_pts[1]).buffer(0.60, resolution=64)
    )
    to_remove_silk, to_add_silk = [], []
    for d in list(b.GetDrawings()):
        if d.GetLayer() == F_SILK and isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s = (um(d.GetStart().x), um(d.GetStart().y))
            e = (um(d.GetEnd().x), um(d.GetEnd().y))
            seg = LineString([s, e])
            if seg.intersects(clip_union):
                diff = seg.difference(clip_union)
                w = d.GetWidth()
                to_remove_silk.append(d)
                geoms = [diff] if diff.geom_type == "LineString" else list(getattr(diff, "geoms", []))
                for g in geoms:
                    if g.length >= 0.15:
                        c0, c1 = g.coords[0], g.coords[-1]
                        ns = pcbnew.PCB_SHAPE(b)
                        ns.SetShape(pcbnew.SHAPE_T_SEGMENT)
                        ns.SetLayer(F_SILK)
                        ns.SetWidth(w)
                        ns.SetStart(pcbnew.VECTOR2I(mm(c0[0]), mm(c0[1])))
                        ns.SetEnd(pcbnew.VECTOR2I(mm(c1[0]), mm(c1[1])))
                        to_add_silk.append(ns)
    for ns in to_add_silk:
        b.Add(ns)
    for d in to_remove_silk:
        b.Remove(d)
    print(f"Clipped {len(to_remove_silk)} F.SilkS Voronoi segment(s) around J1 NPTHs (kept {len(to_add_silk)} trimmed sub-segments).")

    # 4. Prepare proposed locked 0-via B.Cu segments for USB_DP and USB_DM into U7.4 and U7.6
    B_CU = b.GetLayerID("B.Cu")
    F_CU = b.GetLayerID("F.Cu")
    cu_layers = [l for l in range(64) if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)]

    u7_p4 = next(p.GetPosition() for p in fps["U7"].Pads() if p.GetNumber() == "4")  # USB_DP
    u7_p6 = next(p.GetPosition() for p in fps["U7"].Pads() if p.GetNumber() == "6")  # USB_DM
    dp_target = (um(u7_p4.x), um(u7_p4.y))
    dm_target = (um(u7_p6.x), um(u7_p6.y))

    # USB_DP on Board F has segment (100.280,108.760)->(100.550,109.030)->(100.550,109.700);
    # we replace everything south of (100.550, 109.030) with clean 0-via B.Cu path into U7.4!
    usb_dp_pts = [
        (100.550, 109.030),
        (100.550, 109.450),
        ( 99.780, 110.220),
        ( 99.780, 110.500),
        ( 99.040, 111.240),
        dp_target,
    ]
    # USB_DM on Board F has (100.340, 108.440)->(100.850, 108.440);
    # we extend from (100.850, 108.440) straight south at x=100.920 into U7.6!
    usb_dm_pts = [
        (100.850, 108.440),
        (100.920, 108.510),
        (100.920, 110.731),
        dm_target,
    ]
    # Direct 0-via 0.25 mm B.Cu VBUS bus: J1.A4B9 + J1.B4A9 -> C1.1 (decouples VBUS immediately on B.Cu!)
    vbus_main_pts = [
        (109.047, 107.850),
        (108.680, 107.220),
        (107.500, 107.520),
        (106.050, 107.780),
        (104.220, 108.650),
        (102.980, 108.800),
    ]
    vbus_tap_pts = [
        (104.660, 109.798),
        (104.220, 108.650),
    ]
    # Inward NNE 0-via B.Cu GND tie for U7.2 -> J1.S1 (NW), leaving U7.3/U7.1's SE lane 100% unobstructed!
    u7_gnd_pts = [
        (100.475, 113.245),
        (100.430, 112.320),
        (101.350, 111.850),
        (102.480, 111.467),
    ]

    # 5. Copper rip-up & branch walking
    items = list(b.GetTracks())
    all_pads = [p for f in b.GetFootprints() for p in f.Pads()]
    by_net = {}
    for i, t in enumerate(items):
        by_net.setdefault(t.GetNetname(), []).append(i)

    rip_idx = set()
    rip_reasons = {}

    def mark_rip(i, reason):
        if i not in rip_idx:
            rip_idx.add(i)
            rip_reasons.setdefault(items[i].GetNetname(), set()).add(reason)

    def walk_branch(seed_indices, reason, stop_at_pads=True):
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

    # 5a. Full rip of moved local nets
    for i, t in enumerate(items):
        if t.GetNetname() in FULL_RIP_NETS:
            mark_rip(i, "moved_local_net")

    # 5b. Rip old tails of USB_DP (south of 109.035), USB_DM (south of 108.445), and south/east VBAT branch
    for i, t in enumerate(items):
        nm = t.GetNetname()
        if nm == "USB_DP":
            if max(um(e.y) for e in ends(t)) > 109.035:
                mark_rip(i, "moved_U7_USB_DP_tail")
        elif nm == "USB_DM":
            if max(um(e.y) for e in ends(t)) > 108.445:
                mark_rip(i, "moved_U7_USB_DM_tail")
        elif nm == "VBAT":
            max_y = max(um(e.y) for e in ends(t))
            max_x = max(um(e.x) for e in ends(t))
            on_in6 = (not is_via(t)) and b.GetLayerName(t.GetLayer()) == "In6.Cu"
            if (max_x > 92.55 and max_y > 106.50) or max_y > 112.95 or (on_in6 and max_y > 110.0):
                mark_rip(i, "moved_VBAT_south_branch")

    # Walk old GND branches from old moved pads on Board F
    old_pad_seeds = []
    for ref, plist in old_pads.items():
        for pnum, pnet, ppos in plist:
            if pnet == "GND":
                for i in by_net.get(pnet, []):
                    t = items[i]
                    if any(near(e, ppos, tol=80000) for e in ends(t)) or t.HitTest(ppos):
                        old_pad_seeds.append(i)
    walk_branch(old_pad_seeds, "old_moved_pad_branch", stop_at_pads=True)

    # 5c. Exact pcbnew collision check for J1 NPTHs (all 8 layers), moved B.Cu pads, and new USB_DP/USB_DM B.Cu segments
    clash_seeds = []
    for nx, ny in npth_pts:
        P = pcbnew.VECTOR2I(mm(nx), mm(ny))
        hc = pcbnew.SHAPE_CIRCLE(P, mm(0.325 + 0.215))
        for i, t in enumerate(items):
            if i in rip_idx:
                continue
            if is_via(t):
                v_dr = um(t.GetDrill()) / 2.0
                if math.hypot(um(t.GetPosition().x) - nx, um(t.GetPosition().y) - ny) < 0.325 + v_dr + 0.215:
                    clash_seeds.append(i)
                    continue
                if t.GetEffectiveShape(B_CU).Collide(hc):
                    clash_seeds.append(i)
            else:
                l = t.GetLayer()
                if t.GetEffectiveShape(l).Collide(hc):
                    clash_seeds.append(i)

    moving_pads = [p for ref in POSES for p in fps[ref].Pads() if p.IsOnLayer(B_CU)]
    for p in moving_pads:
        pnet = p.GetNetname()
        clr = 0.165 if "USB_D" in pnet else 0.110
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
                c_hl = pcbnew.SHAPE_CIRCLE(vpos, mm(v_dr + (0.01 if tnet == pnet else 0.210)))
                if pshape.Collide(c_cu) or pshape.Collide(c_hl):
                    clash_seeds.append(i)
            elif t.GetLayer() == B_CU:
                if pshape.Collide(t.GetEffectiveShape(B_CU), mm(0.01 if tnet == pnet else clr)):
                    clash_seeds.append(i)

    # Also check collisions on B.Cu against our new pre-placed USB_DP, USB_DM, VBUS, and U7.2 GND segments
    preplaced_bcu = [
        ("USB_DP", usb_dp_pts, 0.15, 0.158),
        ("USB_DM", usb_dm_pts, 0.15, 0.158),
        ("VBUS", vbus_main_pts, 0.25, 0.110),
        ("VBUS", vbus_tap_pts, 0.25, 0.110),
        ("GND", u7_gnd_pts, 0.12, 0.110),
    ]
    for pnet, pts_list, pw, def_clr in preplaced_bcu:
        for (x1, y1), (x2, y2) in zip(pts_list, pts_list[1:]):
            tmp = pcbnew.PCB_TRACK(b)
            tmp.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
            tmp.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            tmp.SetWidth(mm(pw))
            tmp.SetLayer(B_CU)
            ts = tmp.GetEffectiveShape(B_CU)
            for i, t in enumerate(items):
                if i in rip_idx or t.GetNetname() == pnet:
                    continue
                clr = 0.160 if ("USB_D" in t.GetNetname() or "USB_D" in pnet) else def_clr
                if is_via(t):
                    vdr = um(t.GetDrill()) / 2.0
                    vhl = pcbnew.SHAPE_CIRCLE(t.GetPosition(), mm(vdr + 0.210))
                    if ts.Collide(t.GetEffectiveShape(B_CU), mm(clr)) or ts.Collide(vhl):
                        clash_seeds.append(i)
                elif t.GetLayer() == B_CU:
                    if ts.Collide(t.GetEffectiveShape(B_CU), mm(clr)):
                        clash_seeds.append(i)

    walk_branch(clash_seeds, "npth_or_pad_collision", stop_at_pads=True)

    # 5c-bis. Unlock F.Cu LED cathode/anode cages above J1, U7, C1, R5, BT1, U8, C6, R8, TP3
    # so LEDs whose pad-3 vias were covered on B.Cu can step horizontally on F.Cu to drop legal vias!
    fcu_escape_seeds = []
    for i, t in enumerate(items):
        if i in rip_idx or is_via(t) or t.GetLayer() != F_CU:
            continue
        if t.GetNetname() in ("+1V1", "+3V3", "VSYS", "GND"):
            continue
        s, e = t.GetStart(), t.GetEnd()
        max_x = max(um(s.x), um(e.x))
        max_y = max(um(s.y), um(e.y))
        if (max_x >= 100.15 and max_y >= 105.80) or (max_x >= 94.00 and max_y >= 114.60):
            fcu_escape_seeds.append(i)
    walk_branch(fcu_escape_seeds, "fcu_led_escape", stop_at_pads=True)

    # 5d. Iterative zero-dangling dead-end pruner ONLY on nets touched by rip-up!
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
                        layers_touched = set()
                        for p in npads:
                            if p.HitTest(pos):
                                layers_touched.add("PAD_" + str(p.GetLayer()))
                        for j in peers:
                            if j != i and j not in rip_idx and not is_via(items[j]):
                                if any(near(pos, e) for e in ends(items[j])) or items[j].HitTest(pos, mm(0.01)):
                                    layers_touched.add(items[j].GetLayer())
                        if len(layers_touched) < 2:
                            mark_rip(i, "dangling_via_prune")
                            pruned_dangling += 1
                            changed = True
                else:
                    l = t.GetLayer()
                    dangling_end = False
                    end_pads = []
                    end_peers = []
                    for e in (t.GetStart(), t.GetEnd()):
                        if nm == "USB_DP" and near(e, pcbnew.VECTOR2I(mm(100.550), mm(109.030))):
                            end_pads.append(None)
                            end_peers.append(True)
                            continue
                        if nm == "USB_DM" and near(e, pcbnew.VECTOR2I(mm(100.850), mm(108.440))):
                            end_pads.append(None)
                            end_peers.append(True)
                            continue
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
                        end_peers.append(on_peer)
                        if hit_p is None and not on_peer:
                            dangling_end = True
                            break
                    if not dangling_end and end_pads[0] is not None and end_pads[0] == end_pads[1] and um(t.GetLength()) < 0.25:
                        dangling_end = True
                    if dangling_end:
                        mark_rip(i, "dangling_track_prune")
                        pruned_dangling += 1
                        changed = True

    print(f"Pruned {pruned_dangling} residual degree-1 dangling segments/vias.")

    # Compute exact rip-up summary BEFORE removing items
    ripped_items = [items[i] for i in sorted(rip_idx)]
    rip_vias = [t for t in ripped_items if is_via(t)]
    rip_trks = [t for t in ripped_items if not is_via(t)]
    rip_xs = [um(e.x) for t in ripped_items for e in ends(t)]
    rip_ys = [um(e.y) for t in ripped_items for e in ends(t)]
    rip_bbox = (min(rip_xs), min(rip_ys), max(rip_xs), max(rip_ys))
    rip_area = (rip_bbox[2] - rip_bbox[0]) * (rip_bbox[3] - rip_bbox[1])
    rip_len = sum(um(t.GetLength()) for t in rip_trks)
    ripped_nets = sorted({t.GetNetname() for t in ripped_items})

    print("\n=== LOCAL RIP-UP SUMMARY ===")
    print(f"  Ripped tracks: {len(rip_trks)} segments ({rip_len:.2f} mm)")
    print(f"  Ripped vias:   {len(rip_vias)} vias")
    print(f"  Ripped total:  {len(ripped_items)} copper items across {len(ripped_nets)} nets")
    print(f"  Rip-up bbox:   x=[{rip_bbox[0]:.3f}, {rip_bbox[2]:.3f}] mm, y=[{rip_bbox[1]:.3f}, {rip_bbox[3]:.3f}] mm "
          f"({rip_bbox[2]-rip_bbox[0]:.2f} x {rip_bbox[3]-rip_bbox[1]:.2f} mm = {rip_area:.2f} mm^2)")
    for net in ripped_nets:
        nv = sum(1 for t in rip_vias if t.GetNetname() == net)
        nt = sum(1 for t in rip_trks if t.GetNetname() == net)
        nl = sum(um(t.GetLength()) for t in rip_trks if t.GetNetname() == net)
        rs = ",".join(sorted(rip_reasons.get(net, [])))
        print(f"    {net:30s}: {nv:2d} vias, {nt:3d} trks ({nl:6.2f} mm)  [{rs}]")

    for t in ripped_items:
        b.Remove(t)

    # Lock 100% of surviving copper so ultraroute --strip keeps all intact branches untouched!
    for t in b.GetTracks():
        t.SetLocked(True)

    # 6. Add the clean locked 0-via B.Cu USB_DP, USB_DM, and VBUS (J1->C1.1) links
    dp_code = b.FindNet("USB_DP").GetNetCode()
    dm_code = b.FindNet("USB_DM").GetNetCode()
    vbus_code = b.FindNet("VBUS").GetNetCode()
    for (x1, y1), (x2, y2) in zip(usb_dp_pts, usb_dp_pts[1:]):
        add_track(b, dp_code, B_CU, x1, y1, x2, y2, 0.15, locked=True)
    for (x1, y1), (x2, y2) in zip(usb_dm_pts, usb_dm_pts[1:]):
        add_track(b, dm_code, B_CU, x1, y1, x2, y2, 0.15, locked=True)
    for (x1, y1), (x2, y2) in zip(vbus_main_pts, vbus_main_pts[1:]):
        add_track(b, vbus_code, B_CU, x1, y1, x2, y2, 0.25, locked=True)
    for (x1, y1), (x2, y2) in zip(vbus_tap_pts, vbus_tap_pts[1:]):
        add_track(b, vbus_code, B_CU, x1, y1, x2, y2, 0.25, locked=True)
    print(
        f"Added locked 0-via B.Cu links: USB_DP ({len(usb_dp_pts)-1} segs), "
        f"USB_DM ({len(usb_dm_pts)-1} segs), VBUS J1.A4B9+B4A9->C1.1 ({len(vbus_main_pts)+len(vbus_tap_pts)-2} segs)."
    )

    # 7. Place verified legal locked GND plane vias + B.Cu stubs for all moved GND pads + U5.15
    gnd_code = b.FindNet("GND").GetNetCode()
    gnd_targets = []
    for ref in ("C1", "R5", "U7", "C6", "U8", "J1"):
        for p in fps[ref].Pads():
            if p.GetNetname() == "GND" and p.IsOnLayer(B_CU):
                # Skip U8's duplicate pad "1" bar if small pad "1" is handled, or tie U8's bar center once
                if ref == "U8" and p.GetNumber() in ("2", "3"):
                    continue
                if ref == "U8" and p.GetNumber() == "1" and um(p.GetSize().x) < 0.8:
                    continue
                gnd_targets.append((f"{ref}.{p.GetNumber()}", p))
    for p in fps["U5"].Pads():
        if p.GetNumber() == "15":
            gnd_targets.append(("U5.15", p))

    # Direct B.Cu GND ties: U5.15 -> U5.17 (EP), J1.A1B12 -> NE J1.S1, and inward NNE U7.2 -> NW J1.S1!
    add_track(b, gnd_code, B_CU, 103.150, 107.463, 103.150, 106.500, 0.20, locked=True)
    add_track(b, gnd_code, B_CU, 109.778, 107.525, 111.500, 107.351, 0.25, locked=True)
    add_track(b, gnd_code, B_CU, u7_gnd_pts[0][0], u7_gnd_pts[0][1], u7_gnd_pts[1][0], u7_gnd_pts[1][1], 0.12, locked=True)
    add_track(b, gnd_code, B_CU, u7_gnd_pts[1][0], u7_gnd_pts[1][1], u7_gnd_pts[2][0], u7_gnd_pts[2][1], 0.15, locked=True)
    add_track(b, gnd_code, B_CU, u7_gnd_pts[2][0], u7_gnd_pts[2][1], u7_gnd_pts[3][0], u7_gnd_pts[3][1], 0.20, locked=True)
    print("  Added direct locked B.Cu GND links: U5.15 -> U5.17 (EP), J1.A1B12 -> J1.S1 (NE), and inward U7.2 -> J1.S1 (NW).")

    # Legal GND via + B.Cu stub finder (checks all 8 layers, F.Cu pads, B.Cu pads, NPTHs, Edge.Cuts, rule areas)
    rule_areas = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
    south_pads = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            py_c = um(p.GetPosition().y)
            if py_c < 102.5:
                continue
            px_c = um(p.GetPosition().x)
            sh_f = p.GetEffectiveShape(F_CU) if p.IsOnLayer(F_CU) else None
            sh_b = p.GetEffectiveShape(B_CU) if p.IsOnLayer(B_CU) else None
            south_pads.append((px_c, py_c, p.GetNetname(), p, sh_f, sh_b))

    def build_south_tracks():
        out = []
        for t in b.GetTracks():
            if is_via(t):
                tpos = t.GetPosition()
                tx, ty = um(tpos.x), um(tpos.y)
                if ty < 102.5:
                    continue
                out.append(("V", tx, ty, tx, ty, t.GetNetname(), um(t.GetWidth(B_CU)) / 2.0, um(t.GetDrill()) / 2.0, B_CU, t.GetEffectiveShape(B_CU)))
            else:
                s, e = t.GetStart(), t.GetEnd()
                x1, y1, x2, y2 = um(s.x), um(s.y), um(e.x), um(e.y)
                if max(y1, y2) < 102.5:
                    continue
                l = t.GetLayer()
                out.append(("T", min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), t.GetNetname(), 0.0, 0.0, l, t.GetEffectiveShape(l)))
        return out

    def can_place_gnd_via_and_stub(ppos, vx, vy, south_trks, vr=0.125, vdr=0.075, stub_w=0.20):
        if math.hypot(vx - 100.0, vy - 100.0) > 19.0 - vr - 0.32:
            return False
        vp = pcbnew.VECTOR2I(mm(vx), mm(vy))
        for ra in rule_areas:
            if ra.Outline().Contains(vp):
                return False
        for nx, ny in npth_pts:
            if math.hypot(vx - nx, vy - ny) < 0.325 + max(vdr, vr) + 0.215:
                return False

        c_cu_def = pcbnew.SHAPE_CIRCLE(vp, mm(vr + 0.105))
        c_cu_usb = pcbnew.SHAPE_CIRCLE(vp, mm(vr + 0.160))
        c_hl = pcbnew.SHAPE_CIRCLE(vp, mm(vdr + 0.210))

        for px_c, py_c, pnet, p, sh_f, sh_b in south_pads:
            if abs(px_c - vx) > 2.8 or abs(py_c - vy) > 2.8:
                continue
            if pnet == "GND":
                if p.HitTest(vp):
                    return False
                continue
            cc = c_cu_usb if "USB_D" in pnet else c_cu_def
            for sh in (sh_f, sh_b):
                if sh is not None and (sh.Collide(cc) or sh.Collide(c_hl)):
                    return False

        for kind, x1, y1, x2, y2, tnet, tr, tdr, l, ts in south_trks:
            if vx < x1 - 1.2 or vx > x2 + 1.2 or vy < y1 - 1.2 or vy > y2 + 1.2:
                continue
            same = (tnet == "GND")
            if kind == "V":
                if math.hypot(x1 - vx, y1 - vy) < vdr + tdr + 0.210:
                    return False
                if not same:
                    clr = 0.160 if "USB_D" in tnet else 0.105
                    if math.hypot(x1 - vx, y1 - vy) < vr + tr + clr:
                        return False
            else:
                if same:
                    continue
                cc = c_cu_usb if "USB_D" in tnet else c_cu_def
                if ts.Collide(cc) or ts.Collide(c_hl):
                    return False

        # Check straight B.Cu stub from ppos to (vx, vy)
        if ppos.x != vp.x or ppos.y != vp.y:
            sx1, sy1 = min(um(ppos.x), vx) - 1.2, min(um(ppos.y), vy) - 1.2
            sx2, sy2 = max(um(ppos.x), vx) + 1.2, max(um(ppos.y), vy) + 1.2
            tmp = pcbnew.PCB_TRACK(b)
            tmp.SetStart(ppos)
            tmp.SetEnd(vp)
            tmp.SetWidth(mm(stub_w))
            tmp.SetLayer(B_CU)
            sts = tmp.GetEffectiveShape(B_CU)
            for px_c, py_c, pnet, p, sh_f, sh_b in south_pads:
                if pnet == "GND" or sh_b is None or px_c < sx1 or px_c > sx2 or py_c < sy1 or py_c > sy2:
                    continue
                clr = 0.160 if "USB_D" in pnet else 0.105
                if sts.Collide(sh_b, mm(clr)):
                    return False
            for kind, x1, y1, x2, y2, tnet, tr, tdr, l, ts in south_trks:
                if tnet == "GND" or x2 < sx1 or x1 > sx2 or y2 < sy1 or y1 > sy2:
                    continue
                if kind == "V":
                    clr_cu = 0.160 if "USB_D" in tnet else 0.105
                    if sts.Collide(ts, mm(clr_cu)):
                        return False
                    v_hl = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(x1), mm(y1)), mm(tdr + 0.210))
                    if sts.Collide(v_hl):
                        return False
                elif l == B_CU:
                    clr = 0.160 if "USB_D" in tnet else 0.105
                    if sts.Collide(ts, mm(clr)):
                        return False
            for nx, ny in npth_pts:
                if sts.Collide(pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(nx), mm(ny)), mm(0.325 + 0.215))):
                    return False
        return True

    placed_gnd = 0
    for label, pad_obj in gnd_targets:
        if label in ("U5.15", "J1.A1B12", "U7.2"):
            placed_gnd += 1
            continue
        south_trks = build_south_tracks()
        px, py = um(pad_obj.GetPosition().x), um(pad_obj.GetPosition().y)
        found = None
        ppos = pad_obj.GetPosition()
        for ri in range(11, 52):
            rad = ri * 0.05
            n_ang = max(24, int(2 * math.pi * rad / 0.08))
            for ai in range(n_ang):
                ang = 2 * math.pi * ai / n_ang
                vx = round(px + rad * math.cos(ang), 3)
                vy = round(py + rad * math.sin(ang), 3)
                if can_place_gnd_via_and_stub(ppos, vx, vy, south_trks, vr=0.125, vdr=0.075, stub_w=0.20):
                    found = (vx, vy)
                    break
            if found:
                break
        if found:
            vx, vy = found
            add_via(b, gnd_code, vx, vy, width_mm=0.25, drill_mm=0.15, locked=True)
            add_track(b, gnd_code, B_CU, px, py, vx, vy, 0.20, locked=True)
            placed_gnd += 1
            print(f"  Placed locked GND via+stub for {label:10s}: ({px:.3f},{py:.3f}) -> ({vx:.3f},{vy:.3f})")
        else:
            print(f"  WARNING: no immediate straight GND via for {label} at ({px:.3f},{py:.3f}) (router will connect)")

    # Tie U8's small pads 1,2,3 to U8's pad 1 bar center on B.Cu
    u8_bar = next(p for p in fps["U8"].Pads() if p.GetNumber() == "1" and um(p.GetSize().x) >= 0.8)
    bx, by = um(u8_bar.GetPosition().x), um(u8_bar.GetPosition().y)
    for p in fps["U8"].Pads():
        if p.GetNumber() in ("1", "2", "3") and p != u8_bar:
            add_track(b, gnd_code, B_CU, bx, by, um(p.GetPosition().x), um(p.GetPosition().y), 0.20, locked=True)

    # 8. Verify 100% of untouched nets and 100% of RP2350 +3V3/+1V1 decoupling/QSPI/clock copper survive intact & locked
    def item_sig(t, brd):
        if is_via(t):
            p = t.GetPosition()
            return ("V", t.GetNetname(), p.x, p.y, t.GetDrill())
        return ("T", t.GetNetname(), brd.GetLayerName(t.GetLayer()), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth())

    b_locked = {item_sig(t, b) for t in b.GetTracks() if t.IsLocked()}
    f_decap = [
        t for t in bf.GetTracks()
        if not is_via(t) and t.GetNetname() in ("+3V3", "+1V1") and um(t.GetStart().y) < 102.0 and t.IsLocked()
    ]
    for t in f_decap:
        assert item_sig(t, bf) in b_locked, f"CRITICAL: RP2350 decap track missing: {item_sig(t, bf)}"

    f_untouched = {
        item_sig(t, bf) for t in bf.GetTracks()
        if t.GetNetname() not in set(ripped_nets)
    }
    missing = f_untouched - b_locked
    assert not missing, f"CRITICAL: untouched net copper missing: {list(missing)[:5]}"
    print(f"Verified: all {len(f_decap)} locked RP2350 +3V3/+1V1 decoupling tracks and all {len(f_untouched)} copper items on {339 - len(ripped_nets)}+ untouched nets survive 100% intact & locked.")

    tb = b.GetTitleBlock()
    tb.SetRevision("F-USBC")
    tb.SetDate("2026-11-08")

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(OUT_PCB, b)
    shutil.copy2(PRO_F, OUT_PRO)
    shutil.copy2(OUT_PCB, "hw/round-pendant/f-usbc/route/pre_autoroute.kicad_pcb")
    shutil.copy2(OUT_PRO, "hw/round-pendant/f-usbc/route/pre_autoroute.kicad_pro")
    print(f"Saved prepared board -> {OUT_PCB} ({placed_gnd}/{len(gnd_targets)} GND vias pre-placed)")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
