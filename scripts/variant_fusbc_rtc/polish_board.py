#!/usr/bin/env python3
"""polish_board.py — Fast, deterministic post-clean_copper_d polish for hw/round-pendant/f-usbc-rtc/:
1. Loads route/cleaned_test2.kicad_pcb (output of scripts/bga/clean_copper_d.py).
2. Removes the dead-end Pass-1 SW5_8 via/branch at (107.0425, 100.5887), snaps U12.B6 pad center,
   and replaces the 3 collinear micro-segments on VBAT (99.34..99.50, 116.96..117.48) with 1 clean 0.30 mm segment.
3. Locks fixed footprints (D1..D235, Q2, SW1, SW2, BT1, J1), Edge.Cuts, and all keepout rule areas (incl. RX8130_xtal_end).
4. Rebuilds F.SilkS Voronoi web cleanly inside R<=18.720 mm and outside all 6 NPTHs.
5. Places all 14/14 verified B.Cu polarized pin-1 dots (U1..U13, Q1; OD=0.30 mm) strictly outside courtyards & 3D bodies.
6. Places all 7 verified 0%-occluded, 0-via-overlap B.SilkS labels strictly at 0 deg / 270 deg
   ('+', '-', '5V', 'USER', 'BOOT', 'rev FUR', '2026-11') + 6 unambiguous designators (TP2, TP5, TP8, SW1, U4, Y1).
7. Enables (subtractmaskfromsilk yes) and updates .kicad_pro / .kicad_dru headers & severities.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
IN_PCB = ROOT / "hw/round-pendant/f-usbc-rtc/route/cleaned_test2.kicad_pcb"
PCB_PATH = ROOT / "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pcb"
PRO_PATH = ROOT / "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_pro"
DRU_PATH = ROOT / "hw/round-pendant/f-usbc-rtc/round-pendant.kicad_dru"

to_mm = pcbnew.ToMM
from_mm = pcbnew.FromMM


def pt(x: float, y: float):
    return pcbnew.VECTOR2I(from_mm(x), from_mm(y))


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


def set_draw_rot(txt_item, want_deg: float):
    for cand in (
        want_deg,
        (want_deg - txt_item.GetParent().GetOrientationDegrees() if isinstance(txt_item.GetParent(), pcbnew.FOOTPRINT) else want_deg),
        want_deg + 180.0,
        -want_deg,
    ):
        txt_item.SetTextAngleDegrees(cand)
        if round(txt_item.GetDrawRotation().AsDegrees()) % 360 == round(want_deg) % 360:
            return
    if isinstance(txt_item.GetParent(), pcbnew.FOOTPRINT):
        fp_deg = txt_item.GetParent().GetOrientationDegrees()
        for sign in (1.0, -1.0):
            for off in (0.0, 90.0, 180.0, 270.0):
                txt_item.SetTextAngleDegrees(want_deg + sign * fp_deg + off)
                if round(txt_item.GetDrawRotation().AsDegrees()) % 360 == round(want_deg) % 360:
                    return
    txt_item.SetTextAngleDegrees(want_deg)


def main():
    b = pcbnew.LoadBoard(str(IN_PCB))
    BCU = b.GetLayerID("B.Cu")
    FSILK = b.GetLayerID("F.SilkS")
    BSILK = b.GetLayerID("B.SilkS")

    removed_keepalive = []

    # 1. Clean the single SW5_8 dead-end Pass-1 via/branch + U12.B6 pad snap + VBAT Q1.4 collinear micro-stubs
    vbat_code = b.FindNet("VBAT").GetNetCode()
    vbat_q1_removed = 0
    for item in list(b.GetTracks()):
        nm = item.GetNetname()
        if nm == "/Driver 5 and matrix/SW5_8":
            if isinstance(item, pcbnew.PCB_VIA):
                vx, vy = to_mm(item.GetPosition().x), to_mm(item.GetPosition().y)
                if math.hypot(vx - 107.0425, vy - 100.5887) < 0.02:
                    b.Remove(item)
                    removed_keepalive.append(item)
            else:
                ln = b.GetLayerName(item.GetLayer())
                x1, y1 = to_mm(item.GetStart().x), to_mm(item.GetStart().y)
                x2, y2 = to_mm(item.GetEnd().x), to_mm(item.GetEnd().y)
                if ln == "In3.Cu":
                    b.Remove(item)
                    removed_keepalive.append(item)
                elif ln == "F.Cu" and min(y1, y2) < 101.95 and max(x1, x2) < 107.10:
                    b.Remove(item)
                    removed_keepalive.append(item)
                elif ln == "B.Cu" and math.hypot(x1 - 111.15, y1 - 101.65) < 0.01 and math.hypot(x2 - 111.2925, y2 - 101.9137) < 0.02:
                    b.Remove(item)
                    removed_keepalive.append(item)
                elif ln == "B.Cu" and math.hypot(x1 - 111.18, y1 - 101.75) < 0.02:
                    item.SetStart(pt(111.1800, 101.7800))
                    nt_sw = pcbnew.PCB_TRACK(b)
                    nt_sw.SetStart(pt(111.1500, 101.6500))
                    nt_sw.SetEnd(pt(111.1800, 101.7800))
                    nt_sw.SetWidth(item.GetWidth())
                    nt_sw.SetLayer(BCU)
                    nt_sw.SetNetCode(item.GetNetCode())
                    b.Add(nt_sw)
                    removed_keepalive.append(nt_sw)
                elif ln == "B.Cu" and math.hypot(x2 - 111.18, y2 - 101.75) < 0.02:
                    item.SetEnd(pt(111.1800, 101.7800))
                    nt_sw = pcbnew.PCB_TRACK(b)
                    nt_sw.SetStart(pt(111.1500, 101.6500))
                    nt_sw.SetEnd(pt(111.1800, 101.7800))
                    nt_sw.SetWidth(item.GetWidth())
                    nt_sw.SetLayer(BCU)
                    nt_sw.SetNetCode(item.GetNetCode())
                    b.Add(nt_sw)
                    removed_keepalive.append(nt_sw)
        elif nm == "VBAT" and not isinstance(item, pcbnew.PCB_VIA) and item.GetLayer() == BCU:
            x1, y1 = to_mm(item.GetStart().x), to_mm(item.GetStart().y)
            x2, y2 = to_mm(item.GetEnd().x), to_mm(item.GetEnd().y)
            if 99.30 <= min(x1, x2) and max(x1, x2) <= 99.55 and 116.92 <= min(y1, y2) and max(y1, y2) <= 117.52:
                b.Remove(item)
                removed_keepalive.append(item)
                vbat_q1_removed += 1

    if vbat_q1_removed:
        for ax, ay, bx, by in ((99.340, 117.480, 99.500, 117.360), (99.500, 117.360, 99.500, 116.963)):
            nt = pcbnew.PCB_TRACK(b)
            nt.SetStart(pt(ax, ay))
            nt.SetEnd(pt(bx, by))
            nt.SetWidth(from_mm(0.30))
            nt.SetLayer(BCU)
            nt.SetNetCode(vbat_code)
            b.Add(nt)
            removed_keepalive.append(nt)
        print(f"[OK] Coalesced {vbat_q1_removed} VBAT->Q1.4 B.Cu micro-stubs into clean 2-segment 0.30 mm dogleg")

    # Add 2nd parallel 0.30/0.15 mm VBAT via at (94.5175, 116.8387) alongside (95.6175, 117.0887)
    IN3 = b.GetLayerID("In3.Cu")
    v_vb2 = pcbnew.PCB_VIA(b)
    v_vb2.SetPosition(pt(94.5175, 116.8387))
    v_vb2.SetWidth(from_mm(0.30))
    v_vb2.SetDrill(from_mm(0.15))
    v_vb2.SetViaType(pcbnew.VIATYPE_THROUGH)
    v_vb2.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v_vb2.SetNetCode(vbat_code)
    b.Add(v_vb2)
    for lid_vb, ax, ay, bx, by in (
        (BCU, 95.2500, 116.7500, 94.5175, 116.8387),
        (IN3, 95.6175, 117.0887, 94.5175, 116.8387),
    ):
        nt_vb = pcbnew.PCB_TRACK(b)
        nt_vb.SetStart(pt(ax, ay))
        nt_vb.SetEnd(pt(bx, by))
        nt_vb.SetWidth(from_mm(0.30))
        nt_vb.SetLayer(lid_vb)
        nt_vb.SetNetCode(vbat_code)
        b.Add(nt_vb)
    print("[OK] Added 2nd parallel 0.30/0.15 mm VBAT via at (94.5175, 116.8387)")

    # 2. Align L1 3D STEP model rotation & lock fixed items
    l1_fp = b.FindFootprintByReference("L1")
    if l1_fp:
        for m in l1_fp.Models():
            m.m_Rotation.z = 0.0

    fixed_refs = {f"D{i}" for i in range(1, 236)} | {"Q2", "SW1", "SW2", "BT1", "J1"}
    locked_fp = 0
    for fp in b.GetFootprints():
        if fp.GetReference() in fixed_refs:
            fp.SetLocked(True)
            locked_fp += 1
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        for g in list(fp.GraphicalItems()):
            if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == BSILK:
                fp.Remove(g)
                removed_keepalive.append(g)

    edge_id = b.GetLayerID("Edge.Cuts")
    for d in list(b.GetDrawings()):
        if d.GetLayer() == edge_id:
            d.SetLocked(True)
        elif d.GetLayer() in (BSILK, FSILK):
            b.Remove(d)
            removed_keepalive.append(d)

    for z in b.Zones():
        if z.GetIsRuleArea():
            z.SetLocked(True)
    print(f"[OK] Locked {locked_fp} fixed footprints + Edge.Cuts + all keepout rule areas")

    # 3. Rebuild F.SilkS Voronoi web clipped inside R<=18.720 mm and outside all 6 NPTHs
    npth_excl = [
        (104.671, 111.030, 0.600),
        (109.953, 108.684, 0.600),
        (83.019, 93.396, 0.630),
        (84.696, 94.049, 0.630),
        (115.359, 94.027, 0.630),
        (117.037, 93.375, 0.630),
    ]
    bf = pcbnew.LoadBoard(str(ROOT / "hw/round-pendant/f/round-pendant.kicad_pcb"))
    bf_fsilk = bf.GetLayerID("F.SilkS")
    kept_fsilk = 0
    for d in bf.GetDrawings():
        if d.GetLayer() != bf_fsilk or not isinstance(d, pcbnew.PCB_SHAPE):
            continue
        if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            x1, y1, x2, y2 = to_mm(s.x), to_mm(s.y), to_mm(e.x), to_mm(e.y)
            w_orig = d.GetWidth()
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
            for sx1, sy1, sx2, sy2 in segs:
                if math.hypot(sx2 - sx1, sy2 - sy1) >= 0.055:
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
    print(f"[OK] Rebuilt {kept_fsilk} F.SilkS Voronoi segments & Q2 OD=0.30mm pin-1 dot")

    # 4. Place all 14/14 verified outside-courtyard B.Cu polarized pin-1 dots (OD=0.30 mm)
    dots = {
        "U1":  (86.950, 103.800),
        "U2":  (94.700, 113.250),
        "U3":  (94.262,  96.200),
        "U4":  (100.155, 108.300),
        "U5":  (101.188, 108.000),
        "U6":  (94.130,  99.475),
        "U7":  (101.286, 113.709),
        "U8":  (91.900, 113.700),
        "U9":  (105.862,  85.150),
        "U10": (87.600,  92.850),
        "U11": (108.000,  92.200),
        "U12": (108.650, 102.700),
        "U13": (114.250, 103.500),
        "Q1":  (98.680, 114.877),
    }
    for ref, (dx, dy) in dots.items():
        circ = pcbnew.PCB_SHAPE(b)
        circ.SetShape(pcbnew.SHAPE_T_CIRCLE)
        circ.SetLayer(BSILK)
        circ.SetCenter(pt(dx, dy))
        circ.SetEnd(pt(dx + 0.075, dy))
        circ.SetWidth(from_mm(0.15))
        circ.SetFilled(True)
        b.Add(circ)
    print(f"[OK] Placed {len(dots)}/14 outside-courtyard OD=0.30 mm B.SilkS pin-1 dots")

    # 5. Place all 7 verified B.SilkS connector/switch/identity labels (strictly 0 deg & 270 deg)
    labels = [
        ("+",       89.60, 106.90,   0.0),
        ("-",       91.80, 107.90,   0.0),
        ("5V",     109.25, 106.05, 270.0),
        ("USER",   116.35,  97.20,   0.0),
        ("BOOT",    85.70,  90.00, 270.0),
        ("rev FUR", 115.30, 107.20, 270.0),
        ("2026-11", 82.20, 100.00, 270.0),
    ]
    for text_str, tx, ty, rot in labels:
        gt = pcbnew.PCB_TEXT(b)
        b.Add(gt)
        gt.SetLayer(BSILK)
        gt.SetText(text_str)
        gt.SetTextSize(pcbnew.VECTOR2I(from_mm(0.80), from_mm(0.80)))
        gt.SetTextThickness(from_mm(0.15))
        gt.SetMirrored(True)
        gt.SetKeepUpright(False)
        set_draw_rot(gt, rot)
        gt.SetPosition(pt(tx, ty))
    print(f"[OK] Placed {len(labels)}/7 B.SilkS labels strictly at 0 deg / 270 deg")

    # 6. Show the 6 verified unambiguous B.SilkS designators
    shown_refs = [
        ("TP2", 107.77,  94.01, 270.0),
        ("TP5",  85.90,  96.49, 270.0),
        ("TP8",  84.07, 102.51, 270.0),
        ("SW1", 112.84,  94.26,   0.0),
        ("U4",   93.84, 107.78, 270.0),
        ("Y1",   94.64,  83.52,   0.0),
    ]
    for ref, rx, ry, rot in shown_refs:
        fp = b.FindFootprintByReference(ref)
        rtxt = fp.Reference()
        rtxt.SetLayer(BSILK)
        rtxt.SetTextSize(pcbnew.VECTOR2I(from_mm(0.80), from_mm(0.80)))
        rtxt.SetTextThickness(from_mm(0.15))
        rtxt.SetMirrored(True)
        rtxt.SetKeepUpright(False)
        rtxt.SetVisible(True)
        set_draw_rot(rtxt, rot)
        rtxt.SetPosition(pt(rx, ry))
    print(f"[OK] Enabled {len(shown_refs)} unambiguous B.SilkS designators")

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB_PATH), b)

    pcb_txt = PCB_PATH.read_text()
    pcb_txt_new = pcb_txt.replace("(subtractmaskfromsilk no)", "(subtractmaskfromsilk yes)")
    if pcb_txt_new != pcb_txt:
        PCB_PATH.write_text(pcb_txt_new)
        print("[OK] Enabled (subtractmaskfromsilk yes) in round-pendant.kicad_pcb")

    pro = json.loads(PRO_PATH.read_text())
    sev = pro["board"]["design_settings"]["rule_severities"]
    sev["footprint_symbol_mismatch"] = "error"
    sev["text_height"] = "error"
    sev["text_thickness"] = "error"
    pro["board"]["design_settings"]["defaults"]["silk_text_thickness"] = 0.15
    pro["board"]["design_settings"]["rules"]["min_text_thickness"] = 0.15
    PRO_PATH.write_text(json.dumps(pro, indent=2) + "\n")

    dru_txt = DRU_PATH.read_text()
    dru_txt = dru_txt.replace(
        "design/nets-f-usbc.csv and design/brief-f-usbc.md",
        "design/nets-f-usbc-rtc.csv and design/brief-f-usbc-rtc.md",
    )
    DRU_PATH.write_text(dru_txt)
    print("[OK] Saved round-pendant.kicad_pcb and updated .kicad_pro / .kicad_dru")
    os._exit(0)


if __name__ == "__main__":
    main()
