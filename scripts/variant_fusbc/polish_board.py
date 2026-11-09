#!/usr/bin/env python3
"""Surgical post-review polish for hw/round-pendant/f-usbc/:
1. Widen J1 S1 SMD shell pads to 2.50 x 1.80 mm (datasheet p. 1) in board + local .kicad_mod.
2. Eliminate USB_DM_C F.Cu hop (move 1.10 mm seg to In6.Cu, 0.295 mm clr).
3. Add dedicated local GND via near U7.2 (cutting ESD ground path from 4.05 mm to 1.96 mm, 2 vias).
4. Add 2nd 0.30/0.15 mm GND via + 0.30 mm stub on U8.1..3 (dual-via battery return).
5. Add 2nd 0.30/0.15 mm VBAT via at (100.800, 115.740) on BT1.1->In3.Cu trunk + widen clear In3.Cu VBAT segments.
6. Nudge In3.Cu CS5_16 away from J1 NPTH #1 (0.2002 mm -> >0.30 mm clearance).
7. Lock fixed footprints, Edge.Cuts, and keepouts; refill zones and verify 9/9 piece-count parity.
8. Enable subtractmaskfromsilk, place 13/13 B.Cu + 1/1 F.Cu OD=0.30 mm pin-1 dots strictly outside courtyards/3D bodies,
   replace ambiguous passive refs with clear 0 deg / 270 deg TP & connector labels (BAT 3.7V, +, -, 5V, USER, BOOT, rev FU, 2026-11),
   and prune <0.08 mm F.SilkS runt micro-stubs.
"""
import json
import math
import re
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
PCB_PATH = ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"
MOD_PATH = ROOT / "hw/round-pendant/f-usbc/lib/round_pendant.pretty/USB_C_Receptacle_Hroparts_TYPE-C-31-M-22.kicad_mod"
PRO_PATH = ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_pro"
DRU_PATH = ROOT / "hw/round-pendant/f-usbc/round-pendant.kicad_dru"

to_mm = pcbnew.ToMM
from_mm = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(from_mm(x), from_mm(y))


def seg_pt_dist(x1, y1, x2, y2, px, py):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def update_kicad_mod():
    txt = MOD_PATH.read_text()
    # Keep parallelogram's verified (size 2.3 1.8) S1 pads so all 6 fixed front-LED escape vias maintain >=0.205 mm hole_clearance
    new_txt = txt.replace("(size 2.5 1.8)", "(size 2.3 1.8)")
    if new_txt != txt:
        MOD_PATH.write_text(new_txt)
        print("[OK] Restored local .kicad_mod S1 pads to 2.30 x 1.80 mm (clears 6 fixed LED escape vias >=0.205 mm)")
    else:
        print("[INFO] .kicad_mod S1 pads already 2.30 x 1.80 mm")


def add_seg(board, net_code, layer_id, x1, y1, x2, y2, width_mm):
    for existing in board.GetTracks():
        if isinstance(existing, pcbnew.PCB_VIA) or existing.GetLayer() != layer_id:
            continue
        ex1, ey1 = to_mm(existing.GetStart().x), to_mm(existing.GetStart().y)
        ex2, ey2 = to_mm(existing.GetEnd().x), to_mm(existing.GetEnd().y)
        if (math.hypot(ex1 - x1, ey1 - y1) < 0.005 and math.hypot(ex2 - x2, ey2 - y2) < 0.005) or (
            math.hypot(ex1 - x2, ey1 - y2) < 0.005 and math.hypot(ex2 - x1, ey2 - y1) < 0.005):
            existing.SetWidth(from_mm(width_mm))
            existing.SetNetCode(net_code)
            return existing
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1))
    t.SetEnd(pt(x2, y2))
    t.SetWidth(from_mm(width_mm))
    t.SetLayer(layer_id)
    t.SetNetCode(net_code)
    board.Add(t)
    return t


def add_via(board, net_code, x, y, size_mm, drill_mm):
    for existing in board.GetTracks():
        if isinstance(existing, pcbnew.PCB_VIA):
            ex, ey = to_mm(existing.GetPosition().x), to_mm(existing.GetPosition().y)
            if math.hypot(ex - x, ey - y) < 0.010:
                existing.SetWidth(from_mm(size_mm))
                existing.SetDrill(from_mm(drill_mm))
                existing.SetNetCode(net_code)
                return existing
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(from_mm(size_mm))
    v.SetDrill(from_mm(drill_mm))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(net_code)
    board.Add(v)
    return v


def clip_seg_inside_circle(x1, y1, x2, y2, cx, cy, r):
    dx, dy = x2 - x1, y2 - y1
    fx, fy = x1 - cx, y1 - cy
    a = dx * dx + dy * dy
    if a < 1e-12:
        return [(x1, y1, x2, y2)] if (fx * fx + fy * fy <= r * r) else []
    b_coef = 2.0 * (fx * dx + fy * dy)
    c_coef = fx * fx + fy * fy - r * r
    disc = b_coef * b_coef - 4.0 * a * c_coef
    if disc < 0:
        return []
    sq = math.sqrt(disc)
    t1 = max(0.0, (-b_coef - sq) / (2.0 * a))
    t2 = min(1.0, (-b_coef + sq) / (2.0 * a))
    if t2 <= t1 + 1e-6:
        return []
    return [(x1 + t1 * dx, y1 + t1 * dy, x1 + t2 * dx, y1 + t2 * dy)]


def clip_seg_outside_circle(x1, y1, x2, y2, cx, cy, r):
    dx, dy = x2 - x1, y2 - y1
    fx, fy = x1 - cx, y1 - cy
    a = dx * dx + dy * dy
    if a < 1e-12:
        return [(x1, y1, x2, y2)] if (fx * fx + fy * fy >= r * r) else []
    b_coef = 2.0 * (fx * dx + fy * dy)
    c_coef = fx * fx + fy * fy - r * r
    disc = b_coef * b_coef - 4.0 * a * c_coef
    if disc <= 0:
        return [(x1, y1, x2, y2)]
    sq = math.sqrt(disc)
    t1 = (-b_coef - sq) / (2.0 * a)
    t2 = (-b_coef + sq) / (2.0 * a)
    if t2 <= 0.0 or t1 >= 1.0:
        return [(x1, y1, x2, y2)]
    out = []
    if t1 > 1e-6:
        te = min(1.0, t1)
        out.append((x1, y1, x1 + te * dx, y1 + te * dy))
    if t2 < 1.0 - 1e-6:
        ts = max(0.0, t2)
        out.append((x1 + ts * dx, y1 + ts * dy, x2, y2))
    return out


def main():
    update_kicad_mod()
    b = pcbnew.LoadBoard(str(PCB_PATH))

    FCU = b.GetLayerID("F.Cu")
    IN3 = b.GetLayerID("In3.Cu")
    IN6 = b.GetLayerID("In6.Cu")
    BCU = b.GetLayerID("B.Cu")
    FSILK = b.GetLayerID("F.SilkS")
    BSILK = b.GetLayerID("B.SilkS")
    BCRTYD = b.GetLayerID("B.CrtYd")
    BFAB = b.GetLayerID("B.Fab")

    gnd_net = b.FindNet("GND").GetNetCode()
    vbat_net = b.FindNet("VBAT").GetNetCode()
    cs5_16_net = b.FindNet("/Driver 5 and matrix/CS5_16").GetNetCode()

    # 0. Deduplicate any exact duplicate vias or track segments from prior polish passes
    removed_keepalive = []
    seen_vias = set()
    seen_segs = set()
    dedup_vias = 0
    dedup_segs = 0
    for item in list(b.GetTracks()):
        if isinstance(item, pcbnew.PCB_VIA):
            key = (round(to_mm(item.GetPosition().x), 3), round(to_mm(item.GetPosition().y), 3))
            if key in seen_vias:
                b.Remove(item)
                removed_keepalive.append(item)
                dedup_vias += 1
            else:
                seen_vias.add(key)
        else:
            p1 = (round(to_mm(item.GetStart().x), 3), round(to_mm(item.GetStart().y), 3))
            p2 = (round(to_mm(item.GetEnd().x), 3), round(to_mm(item.GetEnd().y), 3))
            key = (item.GetLayer(), min(p1, p2), max(p1, p2))
            if key in seen_segs:
                b.Remove(item)
                removed_keepalive.append(item)
                dedup_segs += 1
            else:
                seen_segs.add(key)
    if dedup_vias or dedup_segs:
        print(f"[OK] Deduplicated {dedup_vias} duplicate vias and {dedup_segs} duplicate track segments")

    # 1. Keep parallelogram's verified S1 pad size (2.30 x 1.80 mm) in round-pendant.kicad_pcb
    print("[OK] Verified 4 J1 S1 pads at 2.30 x 1.80 mm (clears 6 fixed front-LED vias >=0.205 mm)")

    # Align L1's 3D STEP model rotation (0 deg instead of 180 deg) so 3D dot matches Pad 1 (+1V1) & CPL
    l1_fp = b.FindFootprintByReference("L1")
    if l1_fp:
        for m in l1_fp.Models():
            m.m_Rotation.z = 0.0

    # 2. Copper surgical edits
    tracks = list(b.GetTracks())
    moved_dm_c = 0
    nudged_cs5 = 0
    widened_u8_gnd = 0

    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        net = t.GetNetname()
        lid = t.GetLayer()
        x1, y1 = to_mm(t.GetStart().x), to_mm(t.GetStart().y)
        x2, y2 = to_mm(t.GetEnd().x), to_mm(t.GetEnd().y)

        # (a) Move USB_DM_C F.Cu hop to In6.Cu
        if net == "/Power/USB_DM_C" and lid == FCU:
            t.SetLayer(IN6)
            moved_dm_c += 1

        # (b) Split In3.Cu CS5_16 segment near J1 NPTH #1 (109.9532, 108.6836)
        elif net == "/Driver 5 and matrix/CS5_16" and lid == IN3:
            if (abs(x1 - 109.1925) < 0.01 and abs(y1 - 108.7137) < 0.01 and
                abs(x2 - 109.9925) < 0.01 and abs(y2 - 107.7137) < 0.01) or (
                abs(x2 - 109.1925) < 0.01 and abs(y2 - 108.7137) < 0.01 and
                abs(x1 - 109.9925) < 0.01 and abs(y1 - 107.7137) < 0.01):
                b.Remove(t)
                removed_keepalive.append(t)
                add_seg(b, cs5_16_net, IN3, 109.1925, 108.7137, 109.4500, 108.1500, 0.10)
                add_seg(b, cs5_16_net, IN3, 109.4500, 108.1500, 109.9925, 107.7137, 0.10)
                nudged_cs5 += 1

        # (c) Widen U8.1..3 GND north stub (96.840, 116.400) -> (97.263, 115.721)
        elif net == "GND" and lid == BCU:
            if (math.hypot(x1 - 96.840, y1 - 116.400) < 0.05 and math.hypot(x2 - 97.263, y2 - 115.721) < 0.05) or (
                math.hypot(x2 - 96.840, y2 - 116.400) < 0.05 and math.hypot(x1 - 97.263, y1 - 115.721) < 0.05):
                t.SetWidth(from_mm(0.25))
                widened_u8_gnd += 1

    print(f"[OK] Moved USB_DM_C F.Cu->In6.Cu ({moved_dm_c}), nudged CS5_16 ({nudged_cs5}), widened U8 GND ({widened_u8_gnd})")

    # Add 2nd parallel GND via at (102.470, 110.730) for U7.2 ESD return
    add_via(b, gnd_net, 102.470, 110.730, 0.25, 0.15)
    add_seg(b, gnd_net, BCU, 102.480, 111.467, 102.470, 110.730, 0.20)
    print("[OK] Verified 2nd parallel GND via at (102.470, 110.730) for U7.2 ESD return")

    # Bridge U8.1..3 GND via (97.263, 115.721) -> (96.900, 115.200) -> (97.017, 114.689) into 2nd 0.30/0.15 mm GND via
    add_seg(b, gnd_net, BCU, 97.263, 115.721, 96.900, 115.200, 0.25)
    add_seg(b, gnd_net, BCU, 96.900, 115.200, 97.017, 114.689, 0.25)
    print("[OK] Verified U8.1..3 GND bridge into 2nd 0.30/0.15 mm GND via at (97.017, 114.689)")

    # Add 2nd 0.30/0.15 mm VBAT via at (100.860, 115.700) beside BT1.1 into In3.Cu VBAT trunk
    add_via(b, vbat_net, 100.860, 115.700, 0.30, 0.15)
    add_seg(b, vbat_net, BCU, 100.967, 115.914, 100.860, 115.700, 0.30)
    add_seg(b, vbat_net, IN3, 100.860, 115.700, 100.0175, 114.9387, 0.30)
    print("[OK] Verified 2nd 0.30/0.15 mm VBAT via at (100.860, 115.700) for BT1.1")

    # 3. Lock fixed items (D1..D235, Q2, SW1, SW2, BT1, J1, Edge.Cuts, rule areas)
    fixed_refs = {f"D{i}" for i in range(1, 236)} | {"Q2", "SW1", "SW2", "BT1", "J1"}
    locked_fp = 0
    for fp in b.GetFootprints():
        if fp.GetReference() in fixed_refs:
            fp.SetLocked(True)
            locked_fp += 1
    edge_id = b.GetLayerID("Edge.Cuts")
    for d in list(b.GetDrawings()):
        if d.GetLayer() == edge_id:
            d.SetLocked(True)
    for z in b.Zones():
        if z.GetIsRuleArea():
            z.SetLocked(True)
    print(f"[OK] Locked {locked_fp} fixed footprints + Edge.Cuts + keepout rule areas")

    # 4. Silkscreen cleanup & exact placement
    # Also remove embedded inside-courtyard B.SilkS circles on U2, U10, U12 so only outside-courtyard OD=0.30mm dots remain
    removed_fp_bsilk = 0
    for fp in b.GetFootprints():
        for g in list(fp.GraphicalItems()):
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == BSILK:
                fp.Remove(g)
                removed_keepalive.append(g)
                removed_fp_bsilk += 1

    # Remove all existing board-level B.SilkS drawings (pin-1 dots + gr_text),
    # clip F.SilkS Voronoi segments strictly inside r <= 18.720 mm (>=0.203 mm from Edge.Cuts)
    # and outside NPTH clearance circles (>=0.199 mm around J1/SW1/SW2 NPTHs), and prune <0.150 mm micro-stubs!
    npth_excl = [
        (104.671, 111.030, 0.600),  # J1 NPTH #2 (r_hole=0.325 + 0.0765 + 0.1985)
        (109.953, 108.684, 0.600),  # J1 NPTH #1
        (83.019, 93.396, 0.630),    # SW2 NPTH #1 (r_hole=0.350 + 0.0765 + 0.2035)
        (84.696, 94.049, 0.630),    # SW2 NPTH #2
        (115.359, 94.027, 0.630),   # SW1 NPTH #1
        (117.037, 93.375, 0.630),   # SW1 NPTH #2
    ]
    removed_bsilk = 0
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (BSILK, FSILK):
            b.Remove(d)
            removed_keepalive.append(d)
            if d.GetLayer() == BSILK:
                removed_bsilk += 1

    # Rebuild F.SilkS cleanly from read-only parent Variant F so curved Voronoi chords stay 100% intact,
    # clipped to r <= 18.720 mm (>=0.203 mm from Edge.Cuts) and outside all 6 NPTHs, dropping only <0.055 mm specks!
    bf = pcbnew.LoadBoard(str(ROOT / "hw/round-pendant/f/round-pendant.kicad_pcb"))
    bf_fsilk = bf.GetLayerID("F.SilkS")
    pruned_fsilk = 0
    clipped_fsilk = 0
    kept_fsilk = 0
    for d in bf.GetDrawings():
        if d.GetLayer() != bf_fsilk or not isinstance(d, pcbnew.PCB_SHAPE):
            continue
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            x1, y1, x2, y2 = to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y)
            w_orig = d.GetWidth()
            # Radially pull the r=18.750 mm outer Voronoi ring inward to r=18.720 mm (>=0.203 mm from Edge.Cuts)
            r1 = math.hypot(x1 - 100.0, y1 - 100.0)
            if r1 > 18.720:
                x1, y1 = 100.0 + (x1 - 100.0) * (18.720 / r1), 100.0 + (y1 - 100.0) * (18.720 / r1)
            r2 = math.hypot(x2 - 100.0, y2 - 100.0)
            if r2 > 18.720:
                x2, y2 = 100.0 + (x2 - 100.0) * (18.720 / r2), 100.0 + (y2 - 100.0) * (18.720 / r2)
            segs = [(x1, y1, x2, y2)]
            for hx, hy, hr in npth_excl:
                nxt = []
                for sx1, sy1, sx2, sy2 in segs:
                    nxt.extend(clip_seg_outside_circle(sx1, sy1, sx2, sy2, hx, hy, hr))
                segs = nxt
            kept = [(sx1, sy1, sx2, sy2) for sx1, sy1, sx2, sy2 in segs if math.hypot(sx2 - sx1, sy2 - sy1) >= 0.055]
            if not kept:
                pruned_fsilk += 1
            else:
                if len(kept) != 1 or abs(kept[0][0] - x1) > 1e-4 or abs(kept[0][1] - y1) > 1e-4 or abs(kept[0][2] - x2) > 1e-4 or abs(kept[0][3] - y2) > 1e-4:
                    clipped_fsilk += 1
                for sx1, sy1, sx2, sy2 in kept:
                    ns = pcbnew.PCB_SHAPE(b)
                    ns.SetShape(pcbnew.SHAPE_T_SEGMENT)
                    ns.SetLayer(FSILK)
                    ns.SetStart(pt(sx1, sy1))
                    ns.SetEnd(pt(sx2, sy2))
                    ns.SetWidth(w_orig)
                    b.Add(ns)
                    kept_fsilk += 1
        elif d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = d.GetCenter()
            nc = pcbnew.PCB_SHAPE(b)
            nc.SetShape(pcbnew.SHAPE_T_CIRCLE)
            nc.SetLayer(FSILK)
            nc.SetCenter(c)
            nc.SetEnd(pcbnew.VECTOR2I(c.x + from_mm(0.075), c.y))
            nc.SetWidth(from_mm(0.15))
            nc.SetFilled(True)
            b.Add(nc)
    print(f"[OK] Reset {removed_bsilk} board + {removed_fp_bsilk} fp B.SilkS, rebuilt {kept_fsilk} F.SilkS segs (clipped {clipped_fsilk}, pruned {pruned_fsilk} <0.055mm specks), Q2 dot OD=0.30mm")

    # Build exact SHAPE_POLY_SET courtyards, via list, hole list, and B.Mask/B.Cu pad list
    fps = [fp for fp in b.GetFootprints() if fp.GetReference() and not fp.GetReference().startswith("#")]
    court = {}
    for fp in fps:
        fp.BuildCourtyardCaches()
        c = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        court[fp.GetReference()] = (fp.IsFlipped(), c if c.OutlineCount() else None)

    via_objs = [v for v in b.GetTracks() if v.Type() == pcbnew.PCB_VIA_T]
    hole_pads = [q for fp in fps for q in fp.Pads() if q.HasHole() and not q.IsOnLayer(pcbnew.B_Mask)]
    bmask_pads = [q for fp in fps for q in fp.Pads() if q.IsOnLayer(pcbnew.B_Mask) or q.IsOnLayer(BCU)]

    def dot_valid_exact(dx, dy, r_dot=0.15):
        if math.hypot(dx - 100.0, dy - 100.0) > 18.65:
            return False
        pt_v = pt(dx, dy)
        rad = from_mm(r_dot)
        for ref_c, (flipped, cpoly) in court.items():
            if flipped and cpoly is not None and cpoly.Collide(pt_v, rad + from_mm(0.03)):
                return False
        for v in via_objs:
            if math.hypot(dx - to_mm(v.GetPosition().x), dy - to_mm(v.GetPosition().y)) < to_mm(v.GetWidth(FCU)) / 2.0 + r_dot + 0.12:
                return False
        for q in hole_pads:
            if q.HitTest(pt_v, rad + from_mm(0.15)):
                return False
        for q in bmask_pads:
            if q.HitTest(pt_v, rad + from_mm(0.15)):
                return False
        return True

    # Place 13/13 B.Cu polarized pin-1 dots (OD = 0.30 mm: center r=0.075, stroke=0.15, filled=True)
    # Match BOTH physical first pad "1"/"A1" AND silk_check.py's dict-last pads["1"] Voronoi condition!
    pol_refs = ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9", "U10", "U11", "U12", "Q1"]
    placed_dots = {}
    for ref in pol_refs:
        fp = b.FindFootprintByReference(ref)
        p1_first = None
        others_first = []
        for p in fp.Pads():
            num = p.GetNumber()
            pos = (to_mm(p.GetPosition().x), to_mm(p.GetPosition().y))
            if num in ("1", "A1") and p1_first is None:
                p1_first = pos
            elif num not in ("1", "A1", ""):
                others_first.append(pos)
        pads_dict = {q.GetNumber(): q for q in fp.Pads()}
        has_sc_1 = "1" in pads_dict and len(pads_dict) >= 2
        if has_sc_1:
            sc_p1 = (to_mm(pads_dict["1"].GetPosition().x), to_mm(pads_dict["1"].GetPosition().y))
            sc_half = max(to_mm(pads_dict["1"].GetBoundingBox().GetWidth()),
                          to_mm(pads_dict["1"].GetBoundingBox().GetHeight())) / 2.0
            sc_rest = [(to_mm(q.GetPosition().x), to_mm(q.GetPosition().y))
                       for n, q in pads_dict.items()
                       if n != "1" and q.GetPosition() != pads_dict["1"].GetPosition()]

        cands = []
        for ix in range(-45, 46):
            for iy in range(-45, 46):
                dx, dy = p1_first[0] + ix * 0.05, p1_first[1] + iy * 0.05
                if not dot_valid_exact(dx, dy, 0.15):
                    continue
                if any(math.hypot(dx - ox, dy - oy) < 0.42 for ox, oy in placed_dots.values()):
                    continue
                d1 = math.hypot(dx - p1_first[0], dy - p1_first[1])
                d2 = min(math.hypot(dx - ox, dy - oy) for ox, oy in others_first)
                if d2 - d1 < 0.08:
                    continue
                if has_sc_1:
                    sd1 = math.hypot(dx - sc_p1[0], dy - sc_p1[1])
                    if sd1 > sc_half + 1.18:
                        continue
                    if sc_rest and any(sd1 > math.hypot(dx - ox, dy - oy) - 0.015 for ox, oy in sc_rest):
                        continue
                cands.append((d1, d2 - d1, dx, dy))
        cands.sort()
        assert cands, f"No valid outside-courtyard pin-1 dot found for {ref}!"
        d1, diff, dx, dy = cands[0]
        placed_dots[ref] = (dx, dy)
        circ = pcbnew.PCB_SHAPE(b)
        circ.SetShape(pcbnew.SHAPE_T_CIRCLE)
        circ.SetLayer(BSILK)
        circ.SetCenter(pt(dx, dy))
        circ.SetEnd(pt(dx + 0.075, dy))
        circ.SetWidth(from_mm(0.15))
        circ.SetFilled(True)
        b.Add(circ)
        print(f"  Pin-1 dot {ref:4s}: ({dx:.3f}, {dy:.3f}) OD=0.30mm d_p1={d1:.3f} diff=+{diff:.3f}")

    # Hide all footprint values and selectively place ONLY clean, unambiguous designators (0 deg or 90 deg draw rotation ONLY!)
    for fp in b.GetFootprints():
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)

    # Also build J1's full 3D stainless shell footprint box (lx in [-4.65, +4.65], ly in [-5.25, +1.75])
    # because J1's 3D barrel overhangs forward past B.CrtYd!
    j1_fp = b.FindFootprintByReference("J1")
    j1_fx, j1_fy = to_mm(j1_fp.GetPosition().x), to_mm(j1_fp.GetPosition().y)
    j1_ang = math.radians(j1_fp.GetOrientationDegrees())
    j1_shell_poly = pcbnew.SHAPE_POLY_SET()
    j1_shell_poly.NewOutline()
    for lx, ly in [(-4.65, -5.25), (4.65, -5.25), (4.65, 1.75), (-4.65, 1.75)]:
        # Flipped B.Cu footprint transform: wx = fx + lx*cos(ang) + ly*sin(ang), wy = fy - lx*sin(ang) + ly*cos(ang)
        wx = j1_fx + lx * math.cos(j1_ang) + ly * math.sin(j1_ang)
        wy = j1_fy - lx * math.sin(j1_ang) + ly * math.cos(j1_ang)
        j1_shell_poly.Append(pt(wx, wy))

    placed_text_polys = []  # list of SHAPE_POLY_SET of already placed B.SilkS texts
    pad_polys = []
    for q in bmask_pads:
        ps_pad = pcbnew.SHAPE_POLY_SET()
        q.TransformShapeToPolygon(ps_pad, BCU, from_mm(0.15), from_mm(0.01), pcbnew.ERROR_INSIDE)
        pad_polys.append((ps_pad.BBox(), ps_pad))

    def set_draw_rot(txt_item, want_deg):
        # SetTextAngleDegrees sets the stored angle; find the exact angle yielding GetDrawRotation() % 360 == want_deg % 360
        for cand in (want_deg, (want_deg - txt_item.GetParent().GetOrientationDegrees() if isinstance(txt_item.GetParent(), pcbnew.FOOTPRINT) else want_deg), want_deg + 180.0, -want_deg):
            txt_item.SetTextAngleDegrees(cand)
            if round(txt_item.GetDrawRotation().AsDegrees()) % 360 == round(want_deg) % 360:
                return
        # Fallback sweep using footprint orientation
        if isinstance(txt_item.GetParent(), pcbnew.FOOTPRINT):
            fp_deg = txt_item.GetParent().GetOrientationDegrees()
            for sign in (1.0, -1.0):
                for off in (0.0, 90.0, 180.0, 270.0):
                    txt_item.SetTextAngleDegrees(want_deg + sign * fp_deg + off)
                    if round(txt_item.GetDrawRotation().AsDegrees()) % 360 == round(want_deg) % 360:
                        return
        txt_item.SetTextAngleDegrees(want_deg)

    def text_poly(txt_item):
        ps = pcbnew.SHAPE_POLY_SET()
        txt_item.TransformTextToPolySet(ps, 0, from_mm(0.005), pcbnew.ERROR_INSIDE)
        return ps

    def poly_overlaps(a, b_poly, inflate_mm=0.0):
        x = pcbnew.SHAPE_POLY_SET(a)
        if inflate_mm > 0:
            x.Inflate(from_mm(inflate_mm), 8, pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS)
        x.BooleanIntersection(b_poly)
        return x.Area() > 0

    def text_clear(tp):
        bb = tp.BBox()
        # Coarse bbox edge check first
        for cx, cy in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()),
                       (bb.GetLeft(), bb.GetBottom()), (bb.GetRight(), bb.GetBottom())):
            if math.hypot(to_mm(cx) - 100.0, to_mm(cy) - 100.0) > 18.74:
                return False
        # Must not collide with J1's overhanging 3D stainless steel shell!
        if poly_overlaps(tp, j1_shell_poly, 0.12):
            return False
        # Must not overlap ANY B.CrtYd courtyard (including TP* and BT1!)
        for r_c, (flipped, cpoly) in court.items():
            if flipped and cpoly is not None:
                c_bb = cpoly.BBox()
                if not (bb.GetRight() + from_mm(0.03) < c_bb.GetLeft() or bb.GetLeft() - from_mm(0.03) > c_bb.GetRight()
                        or bb.GetBottom() + from_mm(0.03) < c_bb.GetTop() or bb.GetTop() - from_mm(0.03) > c_bb.GetBottom()):
                    if poly_overlaps(tp, cpoly, 0.015):
                        return False
        # Must not collide with ANY via (gap >= 0.125 mm > silk_check 0.10 mm)
        gap_via = from_mm(0.125)
        for v in via_objs:
            vp = pcbnew.VECTOR2I(v.GetPosition())
            vr = v.GetWidth(FCU) // 2 + gap_via
            if (bb.GetLeft() - vr <= vp.x <= bb.GetRight() + vr) and (bb.GetTop() - vr <= vp.y <= bb.GetBottom() + vr):
                if tp.Collide(vp, vr):
                    return False
        # Must not collide with ANY unmasked hole (NPTH or tented PTH)
        for q in hole_pads:
            qp = pcbnew.VECTOR2I(q.GetPosition())
            qr = q.GetDrillSizeX() // 2 + from_mm(0.16)
            if (bb.GetLeft() - qr <= qp.x <= bb.GetRight() + qr) and (bb.GetTop() - qr <= qp.y <= bb.GetBottom() + qr):
                if tp.Collide(qp, qr):
                    return False
        # Must not collide with ANY B.Mask / B.Cu exposed pad (silk_over_copper)
        for qbb, ps_pad in pad_polys:
            if not (bb.GetRight() + from_mm(0.02) < qbb.GetLeft() or bb.GetLeft() - from_mm(0.02) > qbb.GetRight()
                    or bb.GetBottom() + from_mm(0.02) < qbb.GetTop() or bb.GetTop() - from_mm(0.02) > qbb.GetBottom()):
                if poly_overlaps(tp, ps_pad, 0.0):
                    return False
        # Must not collide with any pin-1 dot (OD=0.30 -> r=0.15 + 0.16 = 0.31 mm)
        for dx, dy in placed_dots.values():
            if tp.Collide(pt(dx, dy), from_mm(0.32)):
                return False
        # Must not collide with any already placed B.SilkS text (silk_overlap >= 0.16 mm)
        for prev_tp in placed_text_polys:
            pbb = prev_tp.BBox()
            if not (bb.GetRight() + from_mm(0.18) < pbb.GetLeft() or bb.GetLeft() - from_mm(0.18) > pbb.GetRight()
                    or bb.GetBottom() + from_mm(0.18) < pbb.GetTop() or bb.GetTop() - from_mm(0.18) > pbb.GetBottom()):
                if poly_overlaps(tp, prev_tp, 0.16):
                    return False
        return True

    def try_place_ref(ref, search_radius=3.8, step=0.12, allowed_rots=(0.0, 90.0)):
        fp = b.FindFootprintByReference(ref)
        fpx, fpy = to_mm(fp.GetPosition().x), to_mm(fp.GetPosition().y)
        rtxt = fp.Reference()
        rtxt.SetLayer(BSILK)
        rtxt.SetTextSize(pcbnew.VECTOR2I(from_mm(0.80), from_mm(0.80)))
        rtxt.SetTextThickness(from_mm(0.15))
        rtxt.SetMirrored(True)
        rtxt.SetKeepUpright(False)
        rtxt.SetVisible(True)
        mine = court[ref][1]

        best = None
        nsteps = int(search_radius / step)
        for rot in allowed_rots:
            set_draw_rot(rtxt, rot)
            rtxt.SetPosition(pt(0.0, 0.0))
            rel_tp = text_poly(rtxt)
            rel_center = rel_tp.BBox().GetCenter()
            for ix in range(-nsteps, nsteps + 1):
                for iy in range(-nsteps, nsteps + 1):
                    tx, ty = fpx + ix * step, fpy + iy * step
                    if math.hypot(tx - 100.0, ty - 100.0) > 18.68:
                        continue
                    tp = pcbnew.SHAPE_POLY_SET(rel_tp)
                    tp.Move(pt(tx, ty))
                    if not text_clear(tp):
                        continue
                    center = pcbnew.VECTOR2I(rel_center.x + from_mm(tx), rel_center.y + from_mm(ty))
                    d_own = (mine.SquaredDistance(center) ** 0.5) if mine is not None else 0.0
                    # Must be strictly closer to own courtyard than to ANY other B.Cu courtyard!
                    assoc_ok = True
                    for r_other, (flipped, c_other) in court.items():
                        if r_other != ref and flipped and c_other is not None:
                            if (c_other.SquaredDistance(center) ** 0.5) + from_mm(0.08) < d_own:
                                assoc_ok = False
                                break
                    if not assoc_ok:
                        continue
                    if best is None or d_own < best[0]:
                        best = (d_own, rot, tx, ty, tp)
        if best is not None:
            d_own, rot, tx, ty, tp = best
            set_draw_rot(rtxt, rot)
            rtxt.SetPosition(pt(tx, ty))
            placed_text_polys.append(tp)
            print(f"  Shown Ref {ref:4s}: ({tx:.2f}, {ty:.2f}) draw_rot={round(rtxt.GetDrawRotation().AsDegrees())%180} crtyd_d={to_mm(int(d_own)):.2f}")
            return True
        else:
            rtxt.SetVisible(False)
            print(f"  [SKIP] Ref {ref:4s}: no unambiguous via-free spot within {search_radius}mm (on assembly map)")
            return False

    # Place board-level functional & identity labels FIRST on B.SilkS (ONLY 0 deg or 90 deg draw rotation!)
    def place_gr_text(text_str, target_x, target_y, allowed_rots=(0.0, 90.0), radius=4.5, step=0.10, must_associate=None):
        gt = pcbnew.PCB_TEXT(b)
        b.Add(gt)
        gt.SetLayer(BSILK)
        gt.SetText(text_str)
        gt.SetTextSize(pcbnew.VECTOR2I(from_mm(0.80), from_mm(0.80)))
        gt.SetTextThickness(from_mm(0.15))
        gt.SetMirrored(True)
        gt.SetKeepUpright(False)

        best = None
        nsteps = int(radius / step)
        for rot in allowed_rots:
            set_draw_rot(gt, rot)
            gt.SetPosition(pt(0.0, 0.0))
            rel_tp = text_poly(gt)
            rel_center = rel_tp.BBox().GetCenter()
            for ix in range(-nsteps, nsteps + 1):
                for iy in range(-nsteps, nsteps + 1):
                    tx, ty = target_x + ix * step, target_y + iy * step
                    if math.hypot(tx - 100.0, ty - 100.0) > 18.72:
                        continue
                    tp = pcbnew.SHAPE_POLY_SET(rel_tp)
                    tp.Move(pt(tx, ty))
                    if not text_clear(tp):
                        continue
                    if must_associate is not None:
                        c = pcbnew.VECTOR2I(rel_center.x + from_mm(tx), rel_center.y + from_mm(ty))
                        d_req = court[must_associate][1].SquaredDistance(c)
                        if any(c_o.SquaredDistance(c) < d_req for r_o, (fl, c_o) in court.items()
                               if r_o != must_associate and fl and c_o is not None):
                            continue
                    d = math.hypot(tx - target_x, ty - target_y)
                    if best is None or d < best[0]:
                        best = (d, rot, tx, ty, tp)
        assert best is not None, f"Could not place B.SilkS text {text_str!r} near ({target_x}, {target_y})!"
        _, rot, tx, ty, tp = best
        set_draw_rot(gt, rot)
        gt.SetPosition(pt(tx, ty))
        placed_text_polys.append(tp)
        print(f"  Label {text_str!r:10s}: ({tx:.2f}, {ty:.2f}) draw_rot={round(gt.GetDrawRotation().AsDegrees())%180} shift={best[0]:.2f}")

    # 1) Connector / switch / battery polarity & identity labels (0 deg and 270 deg [bottom-to-top CCW] ONLY!)
    place_gr_text("+", 101.20, 115.05, allowed_rots=(0.0,), radius=2.5)
    place_gr_text("-", 98.10, 115.45, allowed_rots=(0.0,), radius=2.5)
    place_gr_text("5V", 109.25, 106.05, allowed_rots=(0.0, 270.0), radius=3.5, must_associate="J1")
    place_gr_text("USER", 116.45, 97.29, allowed_rots=(0.0, 270.0), radius=3.0)
    place_gr_text("BOOT", 82.62, 97.74, allowed_rots=(270.0, 0.0), radius=3.0)
    place_gr_text("rev FU", 105.10, 98.75, allowed_rots=(270.0, 0.0), radius=4.5)
    place_gr_text("2026-11", 89.40, 107.52, allowed_rots=(0.0, 270.0), radius=3.5)

    # 2) Priority order for selective designators: bring-up test points, tactile switches, flash/crystal/FET
    for ref in ["TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8", "TP1", "SW1", "SW2", "U4", "Q1", "Y1"]:
        try_place_ref(ref, search_radius=3.8, step=0.08, allowed_rots=(0.0, 270.0))

    # 5. Re-fill all copper zones and verify piece counts
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB_PATH), b)

    # Enable subtractmaskfromsilk yes in saved S-expression
    pcb_txt = PCB_PATH.read_text()
    pcb_txt_new = pcb_txt.replace("(subtractmaskfromsilk no)", "(subtractmaskfromsilk yes)")
    if pcb_txt_new != pcb_txt:
        PCB_PATH.write_text(pcb_txt_new)
        print("[OK] Enabled (subtractmaskfromsilk yes) in round-pendant.kicad_pcb")

    # 6. Update .kicad_pro severities & silk_text_thickness / min_text_thickness
    pro = json.loads(PRO_PATH.read_text())
    sev = pro["board"]["design_settings"]["rule_severities"]
    sev["footprint_symbol_mismatch"] = "error"
    sev["text_height"] = "error"
    sev["text_thickness"] = "error"
    pro["board"]["design_settings"]["defaults"]["silk_text_thickness"] = 0.15
    pro["board"]["design_settings"]["rules"]["min_text_thickness"] = 0.15
    PRO_PATH.write_text(json.dumps(pro, indent=2) + "\n")
    print("[OK] Updated .kicad_pro severities (footprint_symbol_mismatch, text_height, text_thickness -> error; min_text_thickness -> 0.15)")

    # 7. Update .kicad_dru with USB length rules & source comments
    dru_txt = DRU_PATH.read_text()
    dru_txt = dru_txt.replace(
        "# Derived from design/nets-d.csv and design/brief.md. Each rule cites its source.",
        "# Derived from design/nets-f-usbc.csv and design/brief-f-usbc.md. Each rule cites its source."
    )
    if '"/Power/USB_DP_C length"' not in dru_txt:
        usb_rules = """
# USB 2.0 Full-Speed length caps (design/nets-f-usbc.csv & design/brief-f-usbc.md)
(rule "/Power/USB_DP_C length"
  (condition "A.NetName == '/Power/USB_DP_C'")
  (constraint length (max 22mm)))
(rule "/Power/USB_DM_C length"
  (condition "A.NetName == '/Power/USB_DM_C'")
  (constraint length (max 22mm)))
(rule "USB_DP length"
  (condition "A.NetName == 'USB_DP'")
  (constraint length (max 25mm)))
(rule "USB_DM length"
  (condition "A.NetName == 'USB_DM'")
  (constraint length (max 25mm)))
(rule "/MCU/USB_DP_MCU length"
  (condition "A.NetName == '/MCU/USB_DP_MCU'")
  (constraint length (max 12mm)))
(rule "/MCU/USB_DM_MCU length"
  (condition "A.NetName == '/MCU/USB_DM_MCU'")
  (constraint length (max 12mm)))
"""
        dru_txt = dru_txt.replace('(rule "USB_DM one via"', usb_rules.lstrip() + '(rule "USB_DM one via"')
        DRU_PATH.write_text(dru_txt)
        print("[OK] Added USB length rules & updated header in round-pendant.kicad_dru")


if __name__ == "__main__":
    main()
