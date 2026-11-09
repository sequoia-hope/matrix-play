#!/usr/bin/env python3
"""add_silk_labels.py — Fast, 3D-occlusion-aware, via-clean B.SilkS pass for f-usbc."""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from shapely.geometry import Polygon
import pcbnew

PCB_PATH = "hw/round-pendant/f-usbc/round-pendant.kicad_pcb"
um = pcbnew.ToMM
mm = lambda v: pcbnew.FromMM(float(v))
KEEP_ALIVE: list = []


def text_poly(item: pcbnew.PCB_TEXT) -> pcbnew.SHAPE_POLY_SET:
    out = pcbnew.SHAPE_POLY_SET()
    item.TransformTextToPolySet(out, item.GetLayer(), mm(0.02), pcbnew.ERROR_OUTSIDE)
    return out


def make_poly_set(pts_mm: list[tuple[float, float]]) -> pcbnew.SHAPE_POLY_SET:
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in pts_mm:
        ps.Append(mm(x), mm(y))
    return ps


def nearest_part(center: pcbnew.VECTOR2I, court: dict[str, pcbnew.SHAPE_POLY_SET | None]) -> str | None:
    best_r, best_d = None, float("inf")
    for r, c in court.items():
        if c is None:
            continue
        d = c.SquaredDistance(center)
        if d < best_d:
            best_r, best_d = r, d
    return best_r


def main() -> int:
    b = pcbnew.LoadBoard(PCB_PATH)
    F_SILK = b.GetLayerID("F.SilkS")
    B_SILK = b.GetLayerID("B.SilkS")
    B_CU = b.GetLayerID("B.Cu")
    B_MASK = b.GetLayerID("B.Mask")
    B_CRTYD = b.GetLayerID("B.CrtYd")
    B_FAB = b.GetLayerID("B.Fab")

    # 0. Clip F.SilkS Voronoi segments back 0.175 mm (centerline r=0.500 mm -> ink edge 0.425 mm,
    #    0.100 mm clear of Ø0.650 mm hole wall) around J1's two through-board NPTH holes!
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union
    j1_fp = next(f for f in b.GetFootprints() if f.GetReference() == "J1")
    npth_keepouts = unary_union([
        Point(um(p.GetPosition().x), um(p.GetPosition().y)).buffer(0.500, 32)
        for p in j1_fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
    ])
    clipped_fsilk = 0
    for d in list(b.GetDrawings()):
        if d.GetLayer() == F_SILK and isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            a = (um(d.GetStart().x), um(d.GetStart().y))
            c = (um(d.GetEnd().x), um(d.GetEnd().y))
            if a == c:
                continue
            ls = LineString([a, c])
            if ls.intersects(npth_keepouts):
                diff = ls.difference(npth_keepouts)
                w_nm = d.GetWidth()
                KEEP_ALIVE.append(d)
                b.Remove(d)
                clipped_fsilk += 1
                parts = list(diff.geoms) if hasattr(diff, "geoms") else ([diff] if not diff.is_empty else [])
                for seg in parts:
                    if seg.length >= 0.12:
                        coords = list(seg.coords)
                        ns = pcbnew.PCB_SHAPE(b)
                        ns.SetShape(pcbnew.SHAPE_T_SEGMENT)
                        ns.SetLayer(F_SILK)
                        ns.SetStart(pcbnew.VECTOR2I(mm(coords[0][0]), mm(coords[0][1])))
                        ns.SetEnd(pcbnew.VECTOR2I(mm(coords[-1][0]), mm(coords[-1][1])))
                        ns.SetWidth(w_nm)
                        b.Add(ns)
                        KEEP_ALIVE.append(ns)
    if clipped_fsilk:
        print(f"  Clipped {clipped_fsilk} F.SilkS Voronoi segments clear of J1 Ø0.65 mm NPTH holes")

    # Remove ONLY board-level B.SilkS PCB_TEXT items, plus any stale PCB_SHAPE dots near moved U7/U8 or hitting vias
    vias = [v for v in b.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
    via_Gap = mm(0.11)
    via_list = [(um(v.GetPosition().x), um(v.GetPosition().y), v.GetPosition(), v.GetWidth(pcbnew.F_Cu) // 2 + via_Gap) for v in vias]

    for d in list(b.GetDrawings()):
        if d.GetLayer() != B_SILK:
            continue
        if isinstance(d, pcbnew.PCB_TEXT):
            KEEP_ALIVE.append(d)
            b.Remove(d)
        elif isinstance(d, pcbnew.PCB_SHAPE):
            c = d.GetBoundingBox().GetCenter()
            cx, cy = um(c.x), um(c.y)
            # Remove stale dots from Board F's old U7 (102.3,109.4) / U8 (106.1,112.6) region or via hits
            if (cx > 95.5 and cy > 108.0) or any(
                abs(vx - cx) < 0.6 and abs(vy - cy) < 0.6 and d.HitTest( pcbnew.VECTOR2I(vp), vr)
                for vx, vy, vp, vr in via_list
            ):
                KEEP_ALIVE.append(d)
                b.Remove(d)

    fps = {f.GetReference(): f for f in b.GetFootprints() if f.GetReference() and not f.GetReference().startswith("#")}

    court: dict[str, pcbnew.SHAPE_POLY_SET | None] = {}
    body_boxes: list[tuple[float, float, float, float, object]] = []

    def add_body_shape(sh):
        bb = sh.BBox()
        body_boxes.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom()), sh))

    for ref, fp in fps.items():
        fp.BuildCourtyardCaches()
        if fp.IsFlipped():
            c = fp.GetCourtyard(B_CRTYD)
            court[ref] = c if c.OutlineCount() else None
            if c.OutlineCount():
                add_body_shape(c)
            for gi in fp.GraphicalItems():
                if gi.GetLayer() == B_CRTYD and gi.GetClass() != "PCB_TEXT":
                    add_body_shape(gi.GetEffectiveShape(B_CRTYD))

    # Explicit 3D solid body keepouts for J1 (TYPE-C-31-M-22 metal shell) and BT1 housing
    # J1 origin = (107.787, 110.926), outward unit vector = (+0.4059, +0.9139), side = (-0.9139, +0.4059)
    jx, jy = 107.787, 110.926
    ux, uy = 0.40594, 0.91390
    sx, sy = -0.91390, 0.40594
    j1_3d_pts = [
        (jx + u * ux + s * sx, jy + u * uy + s * sy)
        for u, s in ((-2.65, -4.85), (5.90, -4.85), (5.90, 4.85), (-2.65, 4.85))
    ]
    add_body_shape(make_poly_set(j1_3d_pts))
    # BT1 3D housing around (100.0, 117.1)
    add_body_shape(make_poly_set([(97.20, 115.45), (102.80, 115.45), (102.80, 118.80), (97.20, 118.80)]))

    pad_boxes: list[tuple[float, float, float, float, object]] = []
    holes: list[tuple[float, float, object, int]] = []
    for fp in fps.values():
        for p in fp.Pads():
            if p.IsOnLayer(B_MASK) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                sh = p.GetEffectiveShape(B_CU)
                bb = sh.BBox()
                pad_boxes.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom()), sh))
            if p.HasHole() and not p.IsOnLayer(B_MASK):
                pos = p.GetPosition()
                holes.append((um(pos.x), um(pos.y), pos, p.GetDrillSizeX() // 2 + via_Gap))

    silk_boxes: list[tuple[float, float, float, float, object]] = []

    def add_silk_shape(sh):
        bb = sh.BBox()
        silk_boxes.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom()), sh))

    # 1. Verify / fix B.SilkS pin-1 marks for ALL B.Cu U* and Q* parts
    board_marks = [d for d in b.GetDrawings() if d.GetLayer() == B_SILK and isinstance(d, pcbnew.PCB_SHAPE)]
    for d in board_marks:
        add_silk_shape(d.GetEffectiveShape(B_SILK))

    for ref, fp in sorted(fps.items()):
        if not fp.IsFlipped():
            continue
        # Remove any footprint B.SilkS graphical item that hits a via
        for gi in list(fp.GraphicalItems()):
            if gi.GetLayer() == B_SILK and gi.GetClass() != "PCB_TEXT":
                bb = gi.GetBoundingBox()
                gx0, gy0, gx1, gy1 = um(bb.GetLeft()) - 0.3, um(bb.GetTop()) - 0.3, um(bb.GetRight()) + 0.3, um(bb.GetBottom()) + 0.3
                if any(gx0 <= vx <= gx1 and gy0 <= vy <= gy1 and gi.HitTest(pcbnew.VECTOR2I(vp), vr) for vx, vy, vp, vr in via_list):
                    KEEP_ALIVE.append(gi)
                    fp.Remove(gi)
                else:
                    add_silk_shape(gi.GetEffectiveShape(B_SILK))

        if not (ref.startswith("U") or ref.startswith("Q")):
            continue
        pads = {q.GetNumber(): q for q in fp.Pads()}
        p1_key = "1" if "1" in pads else ("A1" if "A1" in pads else None)
        if p1_key is None or len(pads) < 2:
            continue
        p1 = pads[p1_key]
        p1_pos = p1.GetPosition()
        half = max(p1.GetBoundingBox().GetWidth(), p1.GetBoundingBox().GetHeight()) / 2
        rest = [q.GetPosition() for n, q in pads.items() if n != p1_key and q.GetPosition() != p1_pos]
        reach1 = mm(1.2)

        marks = [gi for gi in fp.GraphicalItems() if gi.GetLayer() == B_SILK and gi.GetClass() != "PCB_TEXT"]
        marks += [d for d in b.GetDrawings() if d.GetLayer() == B_SILK and isinstance(d, pcbnew.PCB_SHAPE)]
        ok_mark = False
        for m in marks:
            c = m.GetBoundingBox().GetCenter()
            d1 = math.dist((c.x, c.y), (p1_pos.x, p1_pos.y))
            if d1 <= half + reach1 and all(d1 <= math.dist((c.x, c.y), (o.x, o.y)) for o in rest):
                ok_mark = True
                break
        if ok_mark:
            continue

        # Place a clean via-free, pad-free B.SilkS dot beside pad 1
        ax, ay = um(p1_pos.x), um(p1_pos.y)
        placed_dot = False
        for ri in range(3, 28):
            r = ri * 0.05
            for ai in range(36):
                ang = 2 * math.pi * ai / 36
                cx, cy = round(ax + r * math.cos(ang), 3), round(ay + r * math.sin(ang), 3)
                cvec = pcbnew.VECTOR2I(mm(cx), mm(cy))
                d1 = math.dist((cvec.x, cvec.y), (p1_pos.x, p1_pos.y))
                if d1 > half + reach1 or not all(d1 <= math.dist((cvec.x, cvec.y), (o.x, o.y)) for o in rest):
                    continue
                dot = pcbnew.PCB_SHAPE(b)
                dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                dot.SetLayer(B_SILK)
                dot.SetCenter(cvec)
                dot.SetEnd(pcbnew.VECTOR2I(mm(cx + 0.09), mm(cy)))
                dot.SetWidth(mm(0.15))
                dot.SetFilled(True)
                ds = dot.GetEffectiveShape(B_SILK)
                if any(
                    bx0 - 0.35 <= cx <= bx1 + 0.35 and by0 - 0.35 <= cy <= by1 + 0.35 and ds.Collide(psh, mm(0.16))
                    for bx0, by0, bx1, by1, psh in pad_boxes
                ):
                    continue
                if any(abs(vx - cx) < 0.5 and abs(vy - cy) < 0.5 and dot.HitTest(pcbnew.VECTOR2I(vp), vr) for vx, vy, vp, vr in via_list):
                    continue
                b.Add(dot)
                KEEP_ALIVE.append(dot)
                add_silk_shape(ds)
                print(f"  Placed B.SilkS pin-1 dot for {ref} at ({cx:.3f}, {cy:.3f})")
                placed_dot = True
                break
            if placed_dot:
                break

    def valid_text_spot(txt: pcbnew.PCB_TEXT, extra_pred=None) -> tuple[bool, pcbnew.SHAPE_POLY_SET | None]:
        bb = txt.GetBoundingBox()
        x0, y0 = um(bb.GetLeft()), um(bb.GetTop())
        x1, y1 = um(bb.GetRight()), um(bb.GetBottom())
        if any(math.hypot(px - 100.0, py - 100.0) > 18.65 for px in (x0, x1) for py in (y0, y1)):
            return False, None
        tp = text_poly(txt)
        for bx0, by0, bx1, by1, bsh in body_boxes:
            if not (x1 + 0.05 < bx0 or x0 - 0.05 > bx1 or y1 + 0.05 < by0 or y0 - 0.05 > by1):
                if tp.Collide(bsh, mm(0.03)):
                    return False, None
        for bx0, by0, bx1, by1, psh in pad_boxes:
            if not (x1 + 0.20 < bx0 or x0 - 0.20 > bx1 or y1 + 0.20 < by0 or y0 - 0.20 > by1):
                if tp.Collide(psh, mm(0.16)):
                    return False, None
        for vx, vy, vp, vr in via_list:
            if x0 - 0.35 <= vx <= x1 + 0.35 and y0 - 0.35 <= vy <= y1 + 0.35:
                if tp.Collide(pcbnew.VECTOR2I(vp), vr):
                    return False, None
        for hx, hy, hp, hr in holes:
            if x0 - 0.6 <= hx <= x1 + 0.6 and y0 - 0.6 <= hy <= y1 + 0.6:
                if tp.Collide(pcbnew.VECTOR2I(hp), hr):
                    return False, None
        for bx0, by0, bx1, by1, ssh in silk_boxes:
            if not (x1 + 0.20 < bx0 or x0 - 0.20 > bx1 or y1 + 0.20 < by0 or y0 - 0.20 > by1):
                if tp.Collide(ssh, mm(0.16)):
                    return False, None
        if extra_pred is not None and not extra_pred(txt, tp):
            return False, None
        return True, tp

    def place_board_label(text: str, anchor_xy: tuple[float, float], max_r=6.5, step=0.20, angles=(0.0, 90.0), extra_pred=None):
        txt = pcbnew.PCB_TEXT(b)
        txt.SetLayer(B_SILK)
        txt.SetText(text)
        txt.SetTextSize(pcbnew.VECTOR2I(mm(0.80), mm(0.80)))
        txt.SetTextThickness(mm(0.15))
        txt.SetMirrored(True)
        ax, ay = anchor_xy
        nr = int(max_r / step)
        for ri in range(1, nr + 1):
            r = ri * step
            n_ang = max(16, int(2 * math.pi * r / step))
            for ai in range(n_ang):
                ang = 2 * math.pi * ai / n_ang
                cx = round(ax + r * math.cos(ang), 2)
                cy = round(ay + r * math.sin(ang), 2)
                for rot in angles:
                    txt.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
                    txt.SetTextAngleDegrees(rot)
                    ok, tp = valid_text_spot(txt, extra_pred)
                    if ok:
                        b.Add(txt)
                        KEEP_ALIVE.append(txt)
                        add_silk_shape(tp)
                        print(f"  Placed B.SilkS {text!r:16s} at ({cx:6.2f}, {cy:6.2f}) rot={rot:5.1f}°")
                        return True
        print(f"  NOTE: No clean B.SilkS pocket for {text!r} within {max_r} mm of ({ax:.2f}, {ay:.2f})")
        return False

    # 2. Connector & switch labels (strictly outside 3D housings!)
    j1_c = court["J1"]
    j1_bbox = j1_c.BBox()
    j1_bbox.Inflate(mm(6.0))
    place_board_label(
        "5V",
        (107.79, 110.93),
        max_r=7.2,
        step=0.18,
        angles=(0.0, 90.0, 23.95, -66.05),
        extra_pred=lambda t, tp: j1_bbox.Intersects(t.GetBoundingBox()) and nearest_part(pcbnew.VECTOR2I(t.GetBoundingBox().GetCenter()), court) == "J1",
    )

    bt1_pads = {p.GetNumber(): (um(p.GetPosition().x), um(p.GetPosition().y)) for p in fps["BT1"].Pads()}
    p_plus = bt1_pads["1"]   # (101.60, 117.10) VBAT (+)
    p_minus = bt1_pads["2"]  # ( 98.40, 117.10) BAT_N (-)
    place_board_label(
        "+",
        p_plus,
        max_r=4.2,
        step=0.15,
        angles=(0.0,),
        extra_pred=lambda t, tp: math.dist((um(t.GetPosition().x), um(t.GetPosition().y)), p_plus) + 0.80
        < math.dist((um(t.GetPosition().x), um(t.GetPosition().y)), p_minus),
    )
    place_board_label(
        "-",
        p_minus,
        max_r=4.2,
        step=0.15,
        angles=(0.0, 90.0),
        extra_pred=lambda t, tp: math.dist((um(t.GetPosition().x), um(t.GetPosition().y)), p_minus) + 0.80
        < math.dist((um(t.GetPosition().x), um(t.GetPosition().y)), p_plus),
    )

    sw1_pos = (um(fps["SW1"].GetPosition().x), um(fps["SW1"].GetPosition().y))
    sw2_pos = (um(fps["SW2"].GetPosition().x), um(fps["SW2"].GetPosition().y))
    place_board_label("USER", sw1_pos, max_r=4.8, step=0.20, angles=(0.0, 90.0))
    place_board_label("BOOT", sw2_pos, max_r=4.8, step=0.20, angles=(0.0, 90.0))

    # 3. Board identity search across B.Cu pockets (including tangent angles along rim)
    id_angles = tuple(float(a) for a in range(0, 180, 15))
    for id_text in ("rev FU", "2026-11", "round-pendant", "CERN-OHL-P-2.0"):
        place_board_label(id_text, (100.0, 100.0), max_r=17.8, step=0.25, angles=id_angles)

    # 4. Clean B.Cu footprint Reference() designators (strictly 0° or 90°)
    def ref_prio(r: str) -> tuple[int, str]:
        for idx, pfx in enumerate(("J", "BT", "SW", "U", "Q", "Y", "L", "TP", "R", "C")):
            if r.startswith(pfx):
                return (idx, r)
        return (99, r)

    shown_refs = 0
    for ref in sorted([r for r, fp in fps.items() if fp.IsFlipped() and not fp.IsBoardOnly()], key=ref_prio):
        fp = fps[ref]
        field = fp.Reference()
        field.SetLayer(B_SILK)
        field.SetTextSize(pcbnew.VECTOR2I(mm(0.80), mm(0.80)))
        field.SetTextThickness(mm(0.15))
        field.SetMirrored(True)

        mine = court[ref]
        fpos = (um(fp.GetPosition().x), um(fp.GetPosition().y))
        placed = False
        if mine is not None:
            for ri in range(2, 22):
                r = ri * 0.20
                n_ang = max(12, int(2 * math.pi * r / 0.22))
                for ai in range(n_ang):
                    ang = 2 * math.pi * ai / n_ang
                    cx = round(fpos[0] + r * math.cos(ang), 2)
                    cy = round(fpos[1] + r * math.sin(ang), 2)
                    for rot in (0.0, 90.0):
                        field.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
                        field.SetTextAngleDegrees(rot)

                        def assoc_ok(t, tp, mine=mine, ref=ref):
                            ctr = pcbnew.VECTOR2I(t.GetBoundingBox().GetCenter())
                            d_own = mine.SquaredDistance(ctr) ** 0.5
                            return not any(
                                r2 != ref and c2 is not None and (c2.SquaredDistance(ctr) ** 0.5 + mm(0.06) < d_own)
                                for r2, c2 in court.items()
                            )

                        ok, tp = valid_text_spot(field, assoc_ok)
                        if ok:
                            field.SetVisible(True)
                            add_silk_shape(tp)
                            shown_refs += 1
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
        if not placed:
            field.SetVisible(False)

    print(f"  Clean B.Cu Reference() designators shown: {shown_refs}")

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pro_path = Path(PCB_PATH).with_suffix(".kicad_pro")
    dru_path = Path(PCB_PATH).with_suffix(".kicad_dru")
    pro_bak = pro_path.read_bytes() if pro_path.exists() else None
    dru_bak = dru_path.read_bytes() if dru_path.exists() else None
    pcbnew.SaveBoard(PCB_PATH, b)
    if pro_bak is not None:
        pro_path.write_bytes(pro_bak)
    if dru_bak is not None:
        dru_path.write_bytes(dru_bak)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
