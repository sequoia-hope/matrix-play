#!/usr/bin/env python3
"""pcb_gen.py -- 8-layer 1.0 mm ENIG PCB generator for hw/dense-square/<variant>/dense-square.kicad_pcb.

One pcbnew stage per process (always restores .kicad_pro and calls os._exit(0)):
    python3 scripts/dense_square/pcb_gen.py <variant> outline
    python3 scripts/dense_square/pcb_gen.py <variant> stack
    python3 scripts/dense_square/pcb_gen.py <variant> sync
    python3 scripts/dense_square/pcb_gen.py <variant> place
    python3 scripts/dense_square/pcb_gen.py <variant> zones
    python3 scripts/dense_square/pcb_gen.py <variant> models
    python3 scripts/dense_square/pcb_gen.py <variant> post_silk
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/dense_square"))

from config import (  # noqa: E402
    ARRAY_CX,
    ARRAY_CY,
    ARRAY_H,
    ARRAY_W,
    CORNER_R,
    HALF_H,
    HALF_W,
    OX,
    OY,
    SOUTH_BAY_Y_MIN,
    VARIANTS,
    VariantSpec,
    build_led_cells,
)

REF_PCB = ROOT / "hw/round-pendant/d/round-pendant.kicad_pcb"
VENDOR_ZONES = ROOT / "scripts/crunch/placement/vendor_zones.json"

# Proven RP2350 + regulator + crystal + flash + charger + LDO macro translated into B.Cu South bay:
# At (MACRO_DX=+1.40, MACRO_DY=+14.20), Y1 pads sit at y in [-1.85..+0.65] (south of the y=-2.50 LED array!)
# and C1 pads sit at y <= +24.45 (0.55 mm north of y=+25.00 Edge.Cuts). U7, U8, C6, R8 sit on F.Cu South.
MACRO_DX = 1.40
MACRO_DY = 14.20
MACRO_REFS_BCU = {
    "U3", "U4", "U5", "U6", "L1", "Y1",
    *(f"C{i}" for i in range(1, 25) if i not in (6, 7, 15)),
    "R3", "R4", "R5", "R6", "R7", "R13", "R14", "R15", "R16", "R17",
}


def rect_vertices(inset: float = 0.0):
    xw = -HALF_W + inset
    xe = HALF_W - inset
    yn = -HALF_H + inset
    ys = HALF_H - inset
    return [(xw, yn), (xe, yn), (xe, ys), (xw, ys)]


def inside_board(x: float, y: float, margin: float = 0.0) -> bool:
    if abs(x) > HALF_W - margin or abs(y) > HALF_H - margin:
        return False
    # Check rounded corners of radius CORNER_R
    rc = max(0.0, CORNER_R - margin)
    cx = HALF_W - CORNER_R
    cy = HALF_H - CORNER_R
    if abs(x) > cx and abs(y) > cy:
        if math.hypot(abs(x) - cx, abs(y) - cy) > rc:
            return False
    return True


def stage_outline(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "dense-square.kicad_pcb"
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.NewBoard(str(pcb_path))
    b.SetCopperLayerCount(8)
    tb = b.GetTitleBlock()
    tb.SetTitle(f"dense-square ({spec.name})")
    tb.SetRevision(spec.title_rev)
    tb.SetDate("2026-11-06")
    tb.SetCompany("CERN-OHL-P-2.0")
    tb.SetComment(0, spec.summary)

    mm = pcbnew.FromMM
    r = CORNER_R
    w, h = HALF_W, HALF_H
    # 4 straight segments + 4 quarter-circle corner arcs (25.00 x 50.00 mm, R=1.50 mm)
    segs = [
        ((-w + r, -h), (w - r, -h)),  # North
        ((w, -h + r), (w, h - r)),    # East
        ((w - r, h), (-w + r, h)),    # South
        ((-w, h - r), (-w, -h + r)),  # West
    ]
    s2 = r / math.sqrt(2.0)
    arcs = [
        ((w - r, -h), (w - r + s2, -h + r - s2), (w, -h + r)),      # NE
        ((w, h - r), (w - r + s2, h - r + s2), (w - r, h)),         # SE
        ((-w + r, h), (-w + r - s2, h - r + s2), (-w, h - r)),      # SW
        ((-w, -h + r), (-w + r - s2, -h + r - s2), (-w + r, -h)),   # NW
    ]
    for p0, p1 in segs:
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.10))
        seg.SetStart(pcbnew.VECTOR2I(mm(OX + p0[0]), mm(OY + p0[1])))
        seg.SetEnd(pcbnew.VECTOR2I(mm(OX + p1[0]), mm(OY + p1[1])))
        b.Add(seg)

    for p1, pm, p2 in arcs:
        arc = pcbnew.PCB_SHAPE(b)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetLayer(pcbnew.Edge_Cuts)
        arc.SetWidth(mm(0.10))
        arc.SetArcGeometry(
            pcbnew.VECTOR2I(mm(OX + p1[0]), mm(OY + p1[1])),
            pcbnew.VECTOR2I(mm(OX + pm[0]), mm(OY + pm[1])),
            pcbnew.VECTOR2I(mm(OX + p2[0]), mm(OY + p2[1])),
        )
        b.Add(arc)

    # 20.00 x 20.00 mm LED array reference window on F.Fab
    ax0, ax1 = ARRAY_CX - ARRAY_W / 2, ARRAY_CX + ARRAY_W / 2
    ay0, ay1 = ARRAY_CY - ARRAY_H / 2, ARRAY_CY + ARRAY_H / 2
    arr_pts = [(ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1), (ax0, ay0)]
    for a, c in zip(arr_pts, arr_pts[1:]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.F_Fab)
        s.SetWidth(mm(0.08))
        s.SetStart(pcbnew.VECTOR2I(mm(OX + a[0]), mm(OY + a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(OX + c[0]), mm(OY + c[1])))
        b.Add(s)

    # 20.00 x 35.00 mm 802035 prismatic LiPo cell outline on B.Fab
    cell_pts = [(-10.0, -23.0), (10.0, -23.0), (10.0, 12.0), (-10.0, 12.0), (-10.0, -23.0)]
    for a, c in zip(cell_pts, cell_pts[1:]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.B_Fab)
        s.SetWidth(mm(0.08))
        s.SetStart(pcbnew.VECTOR2I(mm(OX + a[0]), mm(OY + a[1])))
        s.SetEnd(pcbnew.VECTOR2I(mm(OX + c[0]), mm(OY + c[1])))
        b.Add(s)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"outline saved (25x50 mm, 8L): {pcb_path}", flush=True)
    os._exit(0)


def stage_stack(spec: VariantSpec):
    """Write JLCPCB 8-layer 1.0 mm ENIG stackup + front/back via tenting (matching round-pendant/e)."""
    pcb_path = spec.hw_dir / "dense-square.kicad_pcb"
    t = pcb_path.read_text()

    def lay(n, k, th=None):
        return f'\t\t\t(layer "{n}" (type "{k}")' + (f" (thickness {th})" if th else "") + ")"

    def diel(idx, kind, th):
        return f'\t\t\t(layer "dielectric {idx}" (type "{kind}") (thickness {th}) (material "FR4") (epsilon_r 4.1) (loss_tangent 0.02))'

    s = [
        "\t\t(stackup",
        lay("F.SilkS", "Top Silk Screen"),
        lay("F.Paste", "Top Solder Paste"),
        lay("F.Mask", "Top Solder Mask", 0.01),
        lay("F.Cu", "copper", 0.035),
        diel(1, "prepreg", 0.0764),
        lay("In1.Cu", "copper", 0.0152),
        diel(2, "core", 0.17),
        lay("In2.Cu", "copper", 0.0152),
        diel(3, "prepreg", 0.0764),
        lay("In3.Cu", "copper", 0.0152),
        diel(4, "core", 0.17),
        lay("In4.Cu", "copper", 0.0152),
        diel(5, "prepreg", 0.0764),
        lay("In5.Cu", "copper", 0.0152),
        diel(6, "core", 0.17),
        lay("In6.Cu", "copper", 0.0152),
        diel(7, "prepreg", 0.0764),
        lay("B.Cu", "copper", 0.035),
        lay("B.Mask", "Bottom Solder Mask", 0.01),
        lay("B.Paste", "Bottom Solder Paste"),
        lay("B.SilkS", "Bottom Silk Screen"),
        '\t\t\t(copper_finish "ENIG")',
        "\t\t\t(dielectric_constraints no)",
        "\t\t)",
    ]
    if "\t\t(stackup" in t:
        t, n = re.subn(r"\t\t\(stackup.*?\n\t\t\)\n", lambda _: "\n".join(s) + "\n", t, count=1, flags=re.S)
        assert n == 1
    else:
        t = t.replace("(setup\n", "(setup\n" + "\n".join(s) + "\n", 1)
    if "(tenting front back)" not in t:
        t = t.replace("\t\t(pcbplotparams\n", "\t\t(tenting front back)\n\t\t(pcbplotparams\n", 1)
    t = re.sub(r"\(general\n\t\t\(thickness [\d.]+\)", "(general\n\t\t(thickness 1)", t)
    pcb_path.write_text(t)
    print(f"8-layer 1.0 mm ENIG stack + via tenting written: {pcb_path}")


def stage_sync(spec: VariantSpec):
    from kicad_write import update_pcb

    hw = spec.hw_dir
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()
    update_pcb(hw / "dense-square.kicad_sch", hw / "dense-square.kicad_pcb", new_parts_at=(OX, OY))
    pro_path.write_bytes(pro_bytes)
    print(f"synced PCB from schematic: {spec.name}", flush=True)
    os._exit(0)


def stage_place(spec: VariantSpec):
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "dense-square.kicad_pcb"
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    ref_b = pcbnew.LoadBoard(str(REF_PCB))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    ref_fps = {f.GetReference(): f for f in ref_b.GetFootprints()}

    def set_fcu(ref: str, x: float, y: float, deg: float, hide_ref: bool = True):
        f = fps[ref]
        if f.GetLayer() != pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(float(deg))
        if hide_ref:
            f.Reference().SetVisible(False)
        f.Value().SetVisible(False)

    def set_bcu(ref: str, x: float, y: float, deg: float):
        f = fps[ref]
        if f.GetLayer() == pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(float(deg))
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)

    # ------------------------------------------------------------------
    # 1. North 20.0 x 20.0 mm window: ONLY the ultra-dense MHPA0808RGBDT LED matrix!
    # ------------------------------------------------------------------
    cells = build_led_cells(spec)
    for c in cells:
        set_fcu(c["ref"], c["x_mm"], c["y_mm"], 0.0, hide_ref=True)

    # ------------------------------------------------------------------
    # 2. F.Cu South Electronics Bay (y in [-2.00, +25.00])
    # ------------------------------------------------------------------
    # Q2 ambient light sensor + R43 + C70 in front South-North bezel gap (y = -0.80, south of LED array!)
    set_fcu("Q2", 0.00, -0.80, 0.0)
    set_fcu("R43", -2.10, -0.80, 90.0)
    set_fcu("C70", 2.10, -0.80, 90.0)

    # 4x AW20198QNR QFN-40 drivers on F.Cu South outer lanes (x = +-8.90, y = +2.40 / +11.35, rot = 0 deg)
    # Placed 100% outside U3 + decoupler B.Cu envelope (|x| <= 6.45), with driver passives tucked in
    # the B.Cu-clear inter-driver (y = 5.65..8.15) and south-driver (y = 14.60..16.05) bands!
    fcu_fixed = {c["ref"] for c in cells} | {"Q2", "R43", "C70"}
    for drv in spec.drivers:
        dx0, dy0, drot = drv.fcu_pos
        set_fcu(drv.uref, dx0, dy0, drot)
        fcu_fixed.add(drv.uref)

        c_pvcc_1u = f"C{drv.cap_base}"
        c_pvcc_100n = f"C{drv.cap_base + 1}"
        c_vcc_100n = f"C{drv.cap_base + 2}"
        c_vcc_1u = f"C{drv.cap_base + 3}"
        sgn = -1.0 if dx0 < 0 else 1.0  # -1 for West (U1, U2), +1 for East (U11, U10)

        if dy0 < 6.0:
            # North-row drivers (U1 at -8.90, U11 at +8.90, y = 2.40, courtyard y_max = 5.245):
            # Place passives horizontally (0 deg) in y = 5.85..7.25, keeping |x| >= 6.55 clear of B.Cu!
            set_fcu(c_pvcc_100n, sgn * 11.15, 5.85, 0.0)
            set_fcu(c_pvcc_1u,   sgn * 8.95,  5.85, 0.0)
            set_fcu(c_vcc_100n,  sgn * 6.80,  5.85, 0.0)
            set_fcu(c_vcc_1u,    sgn * 8.05,  7.05, 0.0)
            set_fcu(drv.rset_ref, sgn * 5.95, 7.05, 0.0)
            if drv.bulk_ref:
                set_fcu(drv.bulk_ref, sgn * 10.75, 7.25, 0.0)
                fcu_fixed.add(drv.bulk_ref)
        else:
            # South-row drivers (U2 at -8.90, U10 at +8.90, y = 11.60, courtyard y = [8.755..14.445]):
            # ISET (pin 29 at dy0 - 1.40) sits just north at y = 8.15; VCC/PVCC decouplers sit just south at y = 15.05..16.40!
            set_fcu(drv.rset_ref, sgn * 6.80, 8.15, 0.0)
            set_fcu(c_pvcc_100n, sgn * 11.15, 15.05, 0.0)
            set_fcu(c_pvcc_1u,   sgn * 8.95,  15.05, 0.0)
            set_fcu(c_vcc_100n,  sgn * 6.80,  15.05, 0.0)
            set_fcu(c_vcc_1u,    sgn * 7.40,  16.25, 0.0)
            if drv.bulk_ref:
                set_fcu(drv.bulk_ref, sgn * 10.55, 16.40, 0.0)
                fcu_fixed.add(drv.bulk_ref)
        fcu_fixed.update({c_pvcc_1u, c_pvcc_100n, c_vcc_100n, c_vcc_1u, drv.rset_ref})

    # Peg-less side tactile switches on East & West edges (+-12.50 mm) in South bay
    set_fcu("SW1", 10.85, 19.00, -90.0)
    sw1_p1 = [um(p.GetPosition().x) - OX for p in fps["SW1"].Pads() if p.GetNumber() == "1"][0]
    sw1_p2 = [um(p.GetPosition().x) - OX for p in fps["SW1"].Pads() if p.GetNumber() == "2"][0]
    if sw1_p2 < sw1_p1:
        set_fcu("SW1", 10.85, 19.00, 90.0)
    set_fcu("R18", 4.20, 16.20, 0.0)
    fcu_fixed.add("SW1")

    set_fcu("SW2", -10.85, 20.40, 90.0)
    sw2_p1 = [um(p.GetPosition().x) - OX for p in fps["SW2"].Pads() if p.GetNumber() == "1"][0]
    sw2_p2 = [um(p.GetPosition().x) - OX for p in fps["SW2"].Pads() if p.GetNumber() == "2"][0]
    if sw2_p2 > sw2_p1:
        set_fcu("SW2", -10.85, 20.40, -90.0)
    fcu_fixed.add("SW2")

    # USB wire pads (J1), CC pull-downs (R1, R2), ESD (U7), Battery pads (BT1), & cell protection (U8, R8, C6) on F.Cu South
    set_fcu("J1", -1.50, 23.10, 0.0)
    fcu_fixed.add("J1")
    j1_p1 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "1").GetPosition()
    j1_p2 = next(p for p in fps["J1"].Pads() if p.GetNumber() == "2").GetPosition()
    set_fcu("R1", um(j1_p1.x) - OX, 20.60, 90.0)
    set_fcu("R2", um(j1_p2.x) - OX, 20.60, 90.0)
    set_fcu("U7", -1.50, 18.20, 0.0)
    fcu_fixed.add("U7")

    set_fcu("BT1", 6.40, 23.35, 0.0)
    set_fcu("U8", 8.10, 20.40, 0.0)
    set_fcu("R8", 8.10, 17.80, 0.0)
    set_fcu("C6", 10.10, 22.80, 0.0)
    fcu_fixed.update({"BT1", "U8"})

    # ------------------------------------------------------------------
    # 3. B.Cu South Electronics Bay (y in [-2.00, +25.00])
    # ------------------------------------------------------------------
    for ref in MACRO_REFS_BCU:
        rf = ref_fps[ref]
        rp = rf.GetPosition()
        set_bcu(ref, (um(rp.x) - OX) + MACRO_DX, (um(rp.y) - OY) + MACRO_DY, rf.GetOrientationDegrees())

    # Tuck PGOOD/CHG 100k pull-ups R6, R7 near U5 north-east (away from U10/U2)
    set_bcu("R6", 5.80, 16.90, 90.0)
    set_bcu("R7", 7.00, 16.90, 90.0)

    # U9 (LIS2DW12) + C25..27 + R19..20 on B.Cu South-West (pushed south to y=20.60 so y=14..17 stays empty under U2 caps!)
    set_bcu("U9", -8.20, 20.60, 180.0)
    p9 = next(p for p in fps["U9"].Pads() if p.GetNumber() == "9").GetPosition()
    dy_u9 = -2.45 if (um(p9.y) - OY) < 20.60 else 2.45
    set_bcu("C25", -9.60, 20.60 + dy_u9, 90.0)
    set_bcu("C26", -8.20, 20.60 + dy_u9, 90.0)
    set_bcu("C27", -6.80, 20.60 + dy_u9, 90.0)
    set_bcu("R19", -9.10, 20.60 - dy_u9, 90.0)
    set_bcu("R20", -7.50, 20.60 - dy_u9, 90.0)

    # Q1 (NTZD3155C VBAT_SENSE) + R9..R12 + C7 on B.Cu South-East
    set_bcu("Q1", 10.60, 21.00, 180.0)
    set_bcu("R9", 10.60, 19.00, 180.0)
    set_bcu("R10", 10.60, 17.70, 180.0)
    set_bcu("R11", 10.60, 22.80, 180.0)
    set_bcu("R12", 10.60, 23.95, 180.0)
    set_bcu("C7", 8.30, 16.90, 90.0)

    # I2C0 pull-ups (R21, R22) & LED_SDB (R31, C35) on B.Cu strictly inside x in [-5.8, +5.8] (clear of U1/U11!)
    set_bcu("R21", -5.10, 2.20, 180.0)
    set_bcu("R22", -5.10, 3.50, 180.0)
    set_bcu("R31", -5.10, 4.80, 180.0)
    set_bcu("C35", -5.10, 0.90, 180.0)

    # Test points in open B.Cu pockets strictly clear of F.Cu QFN pads!
    tp_targets = [
        ("TP1", 5.80, 15.20),    # VSYS
        ("TP2", -5.60, 19.50),   # +3V3
        ("TP3", 2.20, 18.80),    # VBAT
        ("TP4", -2.20, 15.60),   # +1V1
        ("TP5", -5.10, -0.60),   # RUN
        ("TP8", -5.40, 17.80),   # GND
        ("TP6", 3.60, -0.60),    # SWCLK
        ("TP7", 5.20, -0.60),    # SWDIO
    ]
    for tref, tx, ty in tp_targets:
        set_bcu(tref, tx, ty, 180.0)

    # ------------------------------------------------------------------
    # 4. Legalize movable South passives/TPs on F.Cu and B.Cu & verify 0 overlaps
    # ------------------------------------------------------------------
    def cbox(f, crtyd_layer):
        cy = f.GetCourtyard(crtyd_layer)
        q = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False)
        return [um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY]

    fcu_movable = ["R1", "R2", "R8", "C6", "R18"]
    fcu_boxes = {
        r: cbox(f, pcbnew.F_CrtYd)
        for r, f in fps.items()
        if f.GetLayer() == pcbnew.F_Cu and r not in fcu_movable
    }
    for r in fcu_movable:
        f = fps[r]
        q = cbox(f, pcbnew.F_CrtYd)
        x0, y0 = um(f.GetPosition().x) - OX, um(f.GetPosition().y) - OY
        best = None
        for ring in range(0, 120):
            rad = ring * 0.10
            steps = max(1, 16 * ring)
            for k in range(steps):
                a = 2.0 * math.pi * k / steps
                dx, dy = rad * math.cos(a), rad * math.sin(a)
                bb = [q[0] + dx, q[1] + dy, q[2] + dx, q[3] + dy]
                if bb[1] < SOUTH_BAY_Y_MIN or not all(inside_board(u, v, 0.30) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])):
                    continue
                if all(
                    bb[2] + 0.06 <= c[0] or c[2] + 0.06 <= bb[0] or bb[3] + 0.06 <= c[1] or c[3] + 0.06 <= bb[1]
                    for c in fcu_boxes.values()
                ):
                    best = (dx, dy, bb, rad)
                    break
            if best:
                break
        if not best:
            raise SystemExit(f"[{spec.name}] F.Cu legalize failed for {r}")
        dx, dy, bb, rad = best
        if rad > 0:
            f.SetPosition(pcbnew.VECTOR2I(mm(OX + x0 + dx), mm(OY + y0 + dy)))
            print(f"  legalized F.Cu {r}: +{rad:.2f} mm -> ({x0 + dx:.2f}, {y0 + dy:.2f})")
        fcu_boxes[r] = bb

    bcu_movable = [
        "R6", "R7", "Q1", "R9", "R10", "R11", "R12", "C7",
        "R19", "R20", "R21", "R22", "R31", "C35",
        "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8",
    ]
    bcu_boxes = {
        r: cbox(f, pcbnew.B_CrtYd)
        for r, f in fps.items()
        if f.GetLayer() == pcbnew.B_Cu and r not in bcu_movable
    }
    for r in bcu_movable:
        f = fps[r]
        q = cbox(f, pcbnew.B_CrtYd)
        x0, y0 = um(f.GetPosition().x) - OX, um(f.GetPosition().y) - OY
        best = None
        for ring in range(0, 160):
            rad = ring * 0.10
            steps = max(1, 16 * ring)
            for k in range(steps):
                a = 2.0 * math.pi * k / steps
                dx, dy = rad * math.cos(a), rad * math.sin(a)
                bb = [q[0] + dx, q[1] + dy, q[2] + dx, q[3] + dy]
                if bb[1] < SOUTH_BAY_Y_MIN or not all(inside_board(u, v, 0.30) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])):
                    continue
                if all(
                    bb[2] + 0.06 <= c[0] or c[2] + 0.06 <= bb[0] or bb[3] + 0.06 <= c[1] or c[3] + 0.06 <= bb[1]
                    for c in bcu_boxes.values()
                ):
                    best = (dx, dy, bb, rad)
                    break
            if best:
                break
        if not best:
            raise SystemExit(f"[{spec.name}] B.Cu legalize failed for {r}")
        dx, dy, bb, rad = best
        if rad > 0:
            f.SetPosition(pcbnew.VECTOR2I(mm(OX + x0 + dx), mm(OY + y0 + dy)))
            print(f"  legalized B.Cu {r}: +{rad:.2f} mm -> ({x0 + dx:.2f}, {y0 + dy:.2f})")
        bcu_boxes[r] = bb

    # Verify 0 F.Cu courtyard overlaps across ALL F.Cu parts (including D1..DN!)
    fcu_names = sorted(fcu_boxes.keys())
    for i, r1 in enumerate(fcu_names):
        a = fcu_boxes[r1]
        for r2 in fcu_names[i + 1:]:
            c = fcu_boxes[r2]
            if not (a[2] <= c[0] + 0.02 or c[2] <= a[0] + 0.02 or a[3] <= c[1] + 0.02 or c[3] <= a[1] + 0.02):
                raise SystemExit(f"[{spec.name}] F.Cu courtyard overlap: {r1} {a} vs {r2} {c}")

    # Verify 0 B.Cu courtyard overlaps across all non-macro pairs
    bcu_names = sorted(bcu_boxes.keys())
    for i, r1 in enumerate(bcu_names):
        a = bcu_boxes[r1]
        for r2 in bcu_names[i + 1:]:
            if r1 in MACRO_REFS_BCU and r2 in MACRO_REFS_BCU:
                continue
            c = bcu_boxes[r2]
            if not (a[2] <= c[0] + 0.02 or c[2] <= a[0] + 0.02 or a[3] <= c[1] + 0.02 or c[3] <= a[1] + 0.02):
                raise SystemExit(f"[{spec.name}] B.Cu courtyard overlap: {r1} {a} vs {r2} {c}")

    # Strict architectural check: ZERO non-LED pads north of SOUTH_BAY_Y_MIN (-2.00 mm)!
    for r, f in fps.items():
        if re.fullmatch(r"D\d+", r):
            continue
        for p in f.Pads():
            py_top = um(p.GetBoundingBox().GetTop()) - OY
            if py_top < SOUTH_BAY_Y_MIN - 0.05:
                raise SystemExit(f"[{spec.name}] Non-LED pad {r}.{p.GetNumber()} intrudes north of South bay: y_top={py_top:.2f} mm")

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"placed {len(fps)} footprints on {spec.name} (0 courtyard overlaps, 0 parts under LED array)", flush=True)
    os._exit(0)


def stage_zones(spec: VariantSpec):
    """Add In2.Cu unbroken GND plane, RP2350 reference zones, solid EP GND thermal vias, and keepout rule areas."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "dense-square.kicad_pcb"
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu") and b.IsLayerEnabled(l)}
    F_CU, IN2_CU, IN6_CU, B_CU = lid["F.Cu"], lid["In2.Cu"], lid["In6.Cu"], lid["B.Cu"]

    # 1. Ensure U5 pad 17 is solid B.Cu copper without paste-split fragments
    u5 = fps["U5"]
    old17 = [p for p in u5.Pads() if p.GetNumber() == "17" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    if len(old17) > 1:
        boxes = [p.GetBoundingBox() for p in old17]
        x0, x1 = min(um(q.GetLeft()) for q in boxes), max(um(q.GetRight()) for q in boxes)
        y0, y1 = min(um(q.GetTop()) for q in boxes), max(um(q.GetBottom()) for q in boxes)
        net17 = old17[0].GetNetCode()
        keep_alive = []
        for p in list(u5.Pads()):
            if p.GetNumber() == "17" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                u5.Remove(p)
                keep_alive.append(p)
        pd = pcbnew.PAD(u5)
        pd.SetShape(pcbnew.PAD_SHAPE_RECT)
        pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        ls = pcbnew.LSET()
        ls.AddLayer(B_CU)
        ls.AddLayer(pcbnew.B_Mask)
        pd.SetLayerSet(ls)
        pd.SetSize(pcbnew.VECTOR2I(mm(x1 - x0), mm(y1 - y0)))
        pd.SetNumber("17")
        u5.Add(pd)
        pd.SetPosition(pcbnew.VECTOR2I(mm((x0 + x1) / 2), mm((y0 + y1) / 2)))
        pd.SetOrientationDegrees(0)
        pd.SetNetCode(net17)

    fcu_pads = [
        (um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom()), p.GetNetname())
        for f in b.GetFootprints()
        if f.GetLayer() == pcbnew.F_Cu
        for p in f.Pads()
        if p.IsOnLayer(F_CU)
        for q in [p.GetBoundingBox()]
    ]
    bcu_pads = [
        (um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom()), p.GetNetname())
        for f in b.GetFootprints()
        if f.GetLayer() == pcbnew.B_Cu
        for p in f.Pads()
        if p.IsOnLayer(B_CU)
        for q in [p.GetBoundingBox()]
    ]

    def both_sides_clear(xa: float, ya: float, req_r: float = 0.285) -> bool:
        # 0.15 mm drill (r=0.075) + 0.20 mm hole_clearance = 0.275 mm minimum to any non-GND pad on F.Cu or B.Cu!
        for a, e, g, h, n in fcu_pads:
            if n != "GND" and math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < req_r:
                return False
        for a, e, g, h, n in bcu_pads:
            if n != "GND" and math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < req_r:
                return False
        return True

    def poly_rel(pts):
        p = pcbnew.SHAPE_POLY_SET()
        p.NewOutline()
        for px, py in pts:
            p.Append(mm(OX + px), mm(OY + py))
        p.thisown = False
        return p

    def add_zone(name, layer, net, pts, prio, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.10, clear=0.10):
        z = pcbnew.ZONE(b)
        z.SetZoneName(name)
        z.SetLayer(layer)
        z.SetNet(b.FindNet(net))
        z.SetAssignedPriority(prio)
        z.SetPadConnection(connect)
        z.SetMinThickness(mm(minw))
        z.SetThermalReliefGap(mm(0.20))
        z.SetThermalReliefSpokeWidth(mm(0.20))
        z.SetLocalClearance(mm(clear))
        z.SetOutline(poly_rel(pts))
        b.Add(z)
        return z

    def add_area(name, layer, pts, tracks=False, pour=False, vias=False):
        k = pcbnew.ZONE(b)
        k.SetIsRuleArea(True)
        k.SetZoneName(name)
        k.SetLayer(layer)
        k.SetDoNotAllowCopperPour(pour)
        k.SetDoNotAllowTracks(tracks)
        k.SetDoNotAllowVias(vias)
        k.SetDoNotAllowPads(False)
        k.SetDoNotAllowFootprints(False)
        k.SetOutline(poly_rel(pts))
        b.Add(k)
        return k

    # 2. Place collision-checked 0.30/0.15 mm GND thermal vias inside U3.61, U5.17 (B.Cu), and AW20198.41 (F.Cu) solid EPs
    gnd_code = b.FindNet("GND").GetNetCode()
    placed_vias = []
    ep_specs = [("U3", "61", 5, B_CU), ("U5", "17", 2, B_CU)] + [(drv.uref, "41", 5, F_CU) for drv in spec.drivers]
    th_summary = {}
    for sref, pad_num, want_n, ep_layer in ep_specs:
        ep_pad = next(p for p in fps[sref].Pads() if p.GetNumber() == pad_num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD)
        bb = ep_pad.GetBoundingBox()
        x0, y0, x1, y1 = um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())
        rx0, ry0, rx1, ry1 = x0 - OX - 0.05, y0 - OY - 0.05, x1 - OX + 0.05, y1 - OY + 0.05
        add_area(f"{sref} solid EP", ep_layer, [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)])

        cands = []
        xv = x0 + 0.30
        while xv <= x1 - 0.30 + 1e-6:
            yv = y0 + 0.30
            while yv <= y1 - 0.30 + 1e-6:
                cands.append((round(xv, 3), round(yv, 3)))
                yv += 0.15
            xv += 0.15
        cx_ep, cy_ep = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        cands.sort(key=lambda q: (min(abs(q[0] - cx_ep), abs(q[1] - cy_ep)), math.hypot(q[0] - cx_ep, q[1] - cy_ep)))
        got = []
        for qx, qy in cands:
            if len(got) >= want_n:
                break
            if both_sides_clear(qx, qy) and all(math.hypot(qx - ax, qy - ay) >= 0.70 for ax, ay in got):
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(qx), mm(qy)))
                v.SetWidth(mm(0.30))
                v.SetDrill(mm(0.15))
                v.SetLayerPair(F_CU, B_CU)
                v.SetNetCode(gnd_code)
                v.SetLocked(True)
                b.Add(v)
                got.append((qx, qy))
                placed_vias.append((qx, qy))
        th_summary[sref] = len(got)
    print(f"[{spec.name}] solid EP GND thermal vias: {th_summary}")

    # 3. Unbroken In2.Cu (L3) solid GND plane across the entire 25 x 50 mm rectangle (0.28 mm edge pullback),
    #    leaving F.Cu, In1, In3, In4, In5, In6, B.Cu (7 routing layers!) 100% open under the 20x20 mm LED array!
    gnd_pts = rect_vertices(inset=0.28)
    add_zone("plane GND", IN2_CU, "GND", gnd_pts, 0, minw=0.12, clear=0.14)

    # Cutout on In6.Cu (directly adjacent to B.Cu VREG_LX switch node) per chips/rp2350.md §6.3.8.1
    lxpads = [p for p in fps["L1"].Pads() if p.GetNetname().endswith("VREG_LX")] + [
        p for p in fps["U3"].Pads() if p.GetNetname().endswith("VREG_LX")
    ]
    lxbbs = [p.GetBoundingBox() for p in lxpads]
    lx0 = min(um(q.GetLeft()) for q in lxbbs) - OX - 0.25
    lx1 = max(um(q.GetRight()) for q in lxbbs) - OX + 0.25
    ly0 = min(um(q.GetTop()) for q in lxbbs) - OY - 0.25
    ly1 = max(um(q.GetBottom()) for q in lxbbs) - OY + 0.25
    add_area("LX cutout L7", IN6_CU, [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)], tracks=True, pour=True)

    # 4. RP2350 unbroken B.Cu power rings + vendor regulator zones
    u3_pos = fps["U3"].GetPosition()
    ux_rel, uy_rel = um(u3_pos.x) - OX, um(u3_pos.y) - OY
    sq = lambda h: [(ux_rel - h, uy_rel - h), (ux_rel + h, uy_rel - h), (ux_rel + h, uy_rel + h), (ux_rel - h, uy_rel + h)]
    add_zone("RP2350 band", B_CU, "+3V3", sq(3.12), 1, minw=0.10, clear=0.09)
    add_zone("RP2350 ring", B_CU, "+1V1", sq(2.32), 3, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.20, clear=0.09)

    v11_code = b.FindNet("+1V1").GetNetCode()
    ring_vias = 0
    for rx, ry in ((0.45, 2.06), (-0.45, -2.06), (-2.06, -0.45), (2.06, 0.45), (0.0, 2.06), (0.0, -2.06)):
        xa, ya = OX + ux_rel + rx, OY + uy_rel + ry
        if both_sides_clear(xa, ya) and all(math.hypot(xa - ax, ya - ay) >= 0.60 for ax, ay in placed_vias):
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(xa), mm(ya)))
            v.SetWidth(mm(0.28))
            v.SetDrill(mm(0.15))
            v.SetLayerPair(F_CU, B_CU)
            v.SetNetCode(v11_code)
            v.SetLocked(True)
            b.Add(v)
            placed_vias.append((xa, ya))
            ring_vias += 1
            if ring_vias >= 3:
                break
    print(f"[{spec.name}] RP2350 +1V1 ring vias placed: {ring_vias}")

    add_area("U3 ring", B_CU, sq(2.85))
    add_area(
        "U3 ring vias",
        B_CU,
        [
            (ux_rel - 2.32, uy_rel - 2.32),
            (ux_rel + 2.32, uy_rel - 2.32),
            (ux_rel + 2.32, uy_rel + 2.32),
            (ux_rel - 2.32, uy_rel + 2.32),
            (ux_rel - 2.32, uy_rel),
            (ux_rel - 1.75, uy_rel),
            (ux_rel - 1.75, uy_rel + 1.75),
            (ux_rel + 1.75, uy_rel + 1.75),
            (ux_rel + 1.75, uy_rel - 1.75),
            (ux_rel - 1.75, uy_rel - 1.75),
            (ux_rel - 1.75, uy_rel - 0.002),
            (ux_rel - 2.32, uy_rel - 0.002),
        ],
    )
    add_area("reg corner", B_CU, [(ux_rel + 1.05, uy_rel + 3.0), (ux_rel + 3.65, uy_rel + 3.0), (ux_rel + 3.65, uy_rel + 8.35), (ux_rel + 1.05, uy_rel + 8.35)])
    l1_cy = fps["L1"].GetCourtyard(B_CU).BBox()
    add_area(
        "L1 window",
        B_CU,
        [
            (um(l1_cy.GetLeft()) - OX, um(l1_cy.GetTop()) - OY),
            (um(l1_cy.GetRight()) - OX, um(l1_cy.GetTop()) - OY),
            (um(l1_cy.GetRight()) - OX, um(l1_cy.GetBottom()) - OY),
            (um(l1_cy.GetLeft()) - OX, um(l1_cy.GetBottom()) - OY),
        ],
    )

    v33_code = b.FindNet("+3V3").GetNetCode()
    for pin, cap in (("1", "C8"), ("11", "C9"), ("20", "C10"), ("30", "C11"), ("38", "C12"), ("44", "C14"), ("54", "C13")):
        a = next(p for p in fps["U3"].Pads() if p.GetNumber() == pin).GetPosition()
        c_ = next(p for p in fps[cap].Pads() if p.GetNetname() == "+3V3").GetPosition()
        ax, ay, cx_, cy_ = um(a.x), um(a.y), um(c_.x), um(c_.y)
        ux_a, uy_a = OX + ux_rel, OY + uy_rel
        if abs(ax - ux_a) > abs(ay - uy_a):
            ox_, oy_ = ux_a + (1 if ax > ux_a else -1) * 4.15, ay
        else:
            ox_, oy_ = ax, uy_a + (1 if ay > uy_a else -1) * 4.15
        for (p0x, p0y), (p1x, p1y) in (((ax, ay), (ox_, oy_)), ((ox_, oy_), (cx_, cy_))):
            if math.hypot(p1x - p0x, p1y - p0y) > 1e-4:
                tr = pcbnew.PCB_TRACK(b)
                tr.SetStart(pcbnew.VECTOR2I(mm(p0x), mm(p0y)))
                tr.SetEnd(pcbnew.VECTOR2I(mm(p1x), mm(p1y)))
                tr.SetWidth(mm(0.20))
                tr.SetLayer(B_CU)
                tr.SetNetCode(v33_code)
                tr.SetLocked(True)
                b.Add(tr)

    p50_pos = next(p for p in fps["U3"].Pads() if p.GetNumber() == "50").GetPosition()
    ux_a, uy_a = OX + ux_rel, OY + uy_rel
    fb_segs = [
        ((um(p50_pos.x), um(p50_pos.y)), (ux_a + 1.20, uy_a + 3.90), 0.20),
        ((ux_a + 1.20, uy_a + 3.90), (ux_a + 1.04, uy_a + 4.06), 0.12),
        ((ux_a + 1.04, uy_a + 4.06), (ux_a + 1.04, uy_a + 5.20), 0.12),
    ]
    for (p0x, p0y), (p1x, p1y), w_fb in fb_segs:
        tr = pcbnew.PCB_TRACK(b)
        tr.SetStart(pcbnew.VECTOR2I(mm(p0x), mm(p0y)))
        tr.SetEnd(pcbnew.VECTOR2I(mm(p1x), mm(p1y)))
        tr.SetWidth(mm(w_fb))
        tr.SetLayer(B_CU)
        tr.SetNetCode(v11_code)
        tr.SetLocked(True)
        b.Add(tr)

    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    bcu_pad_polys = []
    for f in b.GetFootprints():
        if f.GetLayer() == pcbnew.B_Cu:
            for p in f.Pads():
                if p.IsOnLayer(B_CU):
                    o_p = p.GetEffectivePolygon(B_CU).Outline(0)
                    poly_p = Polygon([(um(o_p.CPoint(i).x) - OX, um(o_p.CPoint(i).y) - OY) for i in range(o_p.PointCount())])
                    if poly_p.is_valid and not poly_p.is_empty:
                        bcu_pad_polys.append((p.GetNetname(), poly_p))

    vzones = json.loads(VENDOR_ZONES.read_text())
    for q in vzones:
        if q["prio"] <= 3:
            continue
        net = {"/VREG_LX": "/MCU/VREG_LX"}.get(q["net"], q["net"])
        raw_poly = Polygon([(ux_rel + x, uy_rel - y) for x, y in q["pts"]]).buffer(0)
        for pnet, ppoly in bcu_pad_polys:
            if pnet != net:
                raw_poly = raw_poly.difference(ppoly.buffer(0.18, 8))
        if hasattr(raw_poly, "geoms"):
            raw_poly = max(raw_poly.geoms, key=lambda g: g.area)
        z_pts = [(round(x, 4), round(y, 4)) for x, y in list(raw_poly.exterior.coords)[:-1]]
        add_zone(f"vendor {net}", B_CU, net, z_pts, q["prio"], minw=0.10, clear=0.11)
        add_area(f"vendor {net} area", B_CU, z_pts)

    b.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    vgnd_polys = []
    for z in b.Zones():
        if z.GetZoneName() == "vendor GND":
            ps = z.GetFilledPolysList(B_CU)
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k)
                pts = [(um(o.CPoint(i).x), um(o.CPoint(i).y)) for i in range(o.PointCount())]
                if len(pts) >= 3:
                    vgnd_polys.append(Polygon(pts).buffer(0))
    vgnd_core = unary_union(vgnd_polys).buffer(-0.12) if vgnd_polys else Polygon()

    pg_placed = 0
    if not vgnd_core.is_empty:
        bx0, by0, bx1, by1 = vgnd_core.bounds
        xv = bx0
        while xv <= bx1 + 1e-6 and pg_placed < 2:
            yv = by0
            while yv <= by1 + 1e-6 and pg_placed < 2:
                if vgnd_core.contains(Point(xv, yv)) and both_sides_clear(xv, yv) and all(
                    math.hypot(xv - ax, yv - ay) >= 0.60 for ax, ay in placed_vias
                ):
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(mm(round(xv, 3)), mm(round(yv, 3))))
                    v.SetWidth(mm(0.28))
                    v.SetDrill(mm(0.15))
                    v.SetLayerPair(F_CU, B_CU)
                    v.SetNetCode(gnd_code)
                    v.SetLocked(True)
                    b.Add(v)
                    placed_vias.append((round(xv, 3), round(yv, 3)))
                    pg_placed += 1
                yv += 0.05
            xv += 0.05
    print(f"[{spec.name}] PGND vias placed: {pg_placed}")

    b.BuildConnectivity()
    filler.Fill(b.Zones())
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for l in z.GetLayerSet().Seq():
                ps = z.GetFilledPolysList(l)
                if z.GetZoneName() in ("plane GND", "RP2350 band", "RP2350 ring"):
                    print(f"  zone {z.GetZoneName():<14} ({b.GetLayerName(l)}): pieces={ps.OutlineCount()}, area={ps.Area()/1e12:.1f} mm^2")

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"zones saved: {pcb_path}", flush=True)
    os._exit(0)


def stage_models(spec: VariantSpec):
    """Attach 3D STEP models to all custom footprints for pcbview."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "dense-square.kicad_pcb"
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    base = "${KIPRJMOD}/../../../3dmodels/"
    model_map = {
        "LED_MHPA0808RGBDT": (base + "LED-ARRAY-SMD_4P-L0.80-W0.80-H0.6-BR_MHPA0808RGBDT.step", 0, 0.0),
        "LED_XL-1010RGB": (base + "XL-1010RGB-YG.step", 0, 0.0),
        "SENSOR_ALS-PT19": (base + "SENSORS-SMD_L1.7-W0.8-H0.6.step", 0, 0.0),
        "AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm": (
            "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-40-1EP_5x5mm_P0.4mm_EP3.5x3.5mm.step",
            0,
            0.0,
        ),
        "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias": (base + "QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", 0, 0.0),
        "L_pol_2016": (base + "IND-SMD_L2.0-W1.6_AOTA-B201610S3R3-101-T.step", 180, 0.0),
        "SW_Panasonic_EVQP7J": (base + "SW-SMD_EVQP7C01P-L3.6-W3.5-H1.4-P3.6-LS4.7.step", 0, 0.0),
        "XySemi_DFN-6_1.8x1.4mm": (base + "DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step", 0, 0.56),
        "Texas_X2SON-4_1x1mm_P0.65mm": (base + "X2SON-4_L1.0-W1.0-H0.4-P0.65-TL-EPSLDPRT.step", 270, 0.0),
    }

    b = pcbnew.LoadBoard(str(pcb_path))
    n = 0
    for f in b.GetFootprints():
        name = str(f.GetFPID().GetUniStringLibItemName())
        if name in model_map:
            fn, rot, zoff = model_map[name]
            ms = f.Models()
            ms.clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = fn
            m.m_Rotation = pcbnew.VECTOR3D(0, 0, rot)
            m.m_Show = True
            m.m_Offset = pcbnew.VECTOR3D(0, 0, zoff)
            ms.push_back(m)
            n += 1

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"[{spec.name}] 3D models set on {n} footprints", flush=True)
    os._exit(0)


def stage_post_silk(spec: VariantSpec):
    """Add crisp 20x20 mm front array frame, connector labels, pin-1 dots, and designators clear of pads & vias."""
    import pcbnew

    hw = spec.hw_dir
    pcb_path = hw / "dense-square.kicad_pcb"
    pro_path = hw / "dense-square.kicad_pro"
    pro_bytes = pro_path.read_bytes()

    b = pcbnew.LoadBoard(str(pcb_path))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}

    keep_alive = []
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Remove(d)
            keep_alive.append(d)
    for f in b.GetFootprints():
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        for gi in list(f.GraphicalItems()):
            if gi.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                f.Remove(gi)
                keep_alive.append(gi)

    # Collect pad mask openings + component 3D body outlines + via drill holes so silk never touches pads, bodies, or drills!
    vias_xy = [(um(v.GetPosition().x) - OX, um(v.GetPosition().y) - OY, um(v.GetDrillValue()) / 2 + 0.09)
               for v in b.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]

    fmask_obs = [(-10.15, -22.65, 10.15, -2.35)]  # Never place text inside the 20x20 mm LED window
    bmask_obs = []
    for f in b.GetFootprints():
        side_f = f.GetLayer() == pcbnew.F_Cu
        pboxes = []
        for p in f.Pads():
            bb = p.GetBoundingBox()
            box = (um(bb.GetLeft()) - OX - 0.18, um(bb.GetTop()) - OY - 0.18, um(bb.GetRight()) - OX + 0.18, um(bb.GetBottom()) - OY + 0.18)
            if p.IsOnLayer(pcbnew.F_Mask):
                fmask_obs.append(box)
                if side_f:
                    pboxes.append(bb)
            if p.IsOnLayer(pcbnew.B_Mask):
                bmask_obs.append(box)
                if not side_f:
                    pboxes.append(bb)
        # Also block component body interior (from Courtyard shrunk by 0.22 mm) so designators are never hidden under 3D bodies
        ref = f.GetReference()
        if not ref.startswith("D") and ref not in ("J1", "BT1") and not ref.startswith("TP"):
            cy_layer = pcbnew.F_CrtYd if side_f else pcbnew.B_CrtYd
            cy = f.GetCourtyard(cy_layer).BBox()
            if cy.GetWidth() > 0 and cy.GetHeight() > 0:
                cbox = (um(cy.GetLeft()) - OX + 0.20, um(cy.GetTop()) - OY + 0.20, um(cy.GetRight()) - OX - 0.20, um(cy.GetBottom()) - OY - 0.20)
                if cbox[2] > cbox[0] and cbox[3] > cbox[1]:
                    (fmask_obs if side_f else bmask_obs).append(cbox)

    def box_free(bx0, by0, bx1, by1, obs_list) -> bool:
        if not all(inside_board(u, v, 0.42) for u in (bx0, bx1) for v in (by0, by1)):
            return False
        if not all(bx1 <= a or g <= bx0 or by1 <= e or h <= by0 for a, e, g, h in obs_list):
            return False
        for vx, vy, vr in vias_xy:
            if math.hypot(max(bx0 - vx, 0.0, vx - bx1), max(by0 - vy, 0.0, vy - by1)) < vr:
                return False
        return True

    # Draw crisp 20.4 x 20.4 mm F.SilkS corner brackets framing the 20 x 20 mm LED matrix window
    bx_l, bx_r = -10.30, 10.30
    by_t, by_b = -22.80, -2.20
    tick = 1.60
    brackets = [
        ((bx_l, by_t), (bx_l + tick, by_t)),
        ((bx_l, by_t), (bx_l, by_t + tick)),
        ((bx_r - tick, by_t), (bx_r, by_t)),
        ((bx_r, by_t), (bx_r, by_t + tick)),
        ((bx_l, by_b - tick), (bx_l, by_b)),
        ((bx_l, by_b), (bx_l + tick, by_b)),
        ((bx_r, by_b - tick), (bx_r, by_b)),
        ((bx_r - tick, by_b), (bx_r, by_b)),
    ]
    seg_cnt = 0
    for (x0, y0), (x1, y1) in brackets:
        if box_free(min(x0, x1) - 0.10, min(y0, y1) - 0.10, max(x0, x1) + 0.10, max(y0, y1) + 0.10, fmask_obs):
            s = pcbnew.PCB_SHAPE(b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.F_SilkS)
            s.SetWidth(mm(0.15))
            s.SetStart(pcbnew.VECTOR2I(mm(OX + x0), mm(OY + y0)))
            s.SetEnd(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
            b.Add(s)
            fmask_obs.append((min(x0, x1) - 0.15, min(y0, y1) - 0.15, max(x0, x1) + 0.15, max(y0, y1) + 0.15))
            seg_cnt += 1

    def add_silk_label(txt: str, tx: float, ty: float, side: str, deg: float = 0.0, sz: float = 0.85) -> bool:
        obs = fmask_obs if side == "F" else bmask_obs
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(sz), mm(sz)))
        t.SetTextThickness(mm(0.15))
        t.SetMirrored(side == "B")
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetPosition(pcbnew.VECTOR2I(mm(OX + tx), mm(OY + ty)))
        t.SetTextAngleDegrees(deg)
        bb = t.GetBoundingBox()
        bx0, by0, bx1, by1 = um(bb.GetLeft()) - OX, um(bb.GetTop()) - OY, um(bb.GetRight()) - OX, um(bb.GetBottom()) - OY
        if box_free(bx0, by0, bx1, by1, obs):
            b.Add(t)
            obs.append((bx0 - 0.22, by0 - 0.22, bx1 + 0.22, by1 + 0.22))
            return True
        return False

    def find_and_add_label(txt: str, cx: float, cy: float, side: str, degs=(0.0,), sz: float = 0.80, max_r: float = 2.6, step: float = 0.25) -> bool:
        cands = [(0.0, 0.0)]
        r_cur = step
        while r_cur <= max_r + 1e-6:
            for k in range(16):
                th = 2.0 * math.pi * k / 16.0
                cands.append((round(r_cur * math.cos(th), 3), round(r_cur * math.sin(th), 3)))
            r_cur += step
        for dx, dy in cands:
            for deg in degs:
                if add_silk_label(txt, cx + dx, cy + dy, side, deg, sz):
                    return True
        return False

    # North header on F.SilkS + South connector polarity/rating labels + B.SilkS identity
    find_and_add_label(f"20x20mm {spec.cols}x{spec.rows} 0808", 0.0, -23.55, "F", (0.0,), 0.80, max_r=1.2, step=0.15)
    find_and_add_label("J1 USB 5V", -0.30, 20.95, "F", (0.0,), 0.80, max_r=1.8, step=0.20)
    if "BT1" in fps:
        for p in fps["BT1"].Pads():
            px_b, py_b = um(p.GetPosition().x) - OX, um(p.GetPosition().y) - OY
            pol = "-" if p.GetNetname() == "GND" else "+"
            cx_try = px_b - 1.15 if pol == "-" else px_b
            cy_try = py_b - 1.15 if pol == "-" else py_b - 1.85
            find_and_add_label(pol, cx_try, cy_try, "F", (0.0,), 0.85, max_r=1.3, step=0.15)
    find_and_add_label(f"dense-square ({spec.name}) Rev {spec.title_rev}", 0.0, -23.55, "B", (0.0,), 0.80, max_r=1.4, step=0.20)
    find_and_add_label("CERN-OHL-P-2.0", 0.0, 23.75, "B", (0.0,), 0.80, max_r=1.6, step=0.20)

    # Pin-1 dots on all ICs & Q1/Q2 (clear of mask openings & vias)
    ic_refs = ["U3", "U1", "U2", "U10", "U11", "U4", "U5", "U6", "U7", "U8", "U9", "Q1", "Q2"]
    p1_dots = 0
    for r in ic_refs:
        if r not in fps:
            continue
        f = fps[r]
        side = "F" if f.GetLayer() == pcbnew.F_Cu else "B"
        obs = fmask_obs if side == "F" else bmask_obs
        p1 = next((p for p in f.Pads() if p.GetNumber() in ("1", "A1")), None)
        if p1 is None:
            continue
        px0, py0 = um(p1.GetPosition().x) - OX, um(p1.GetPosition().y) - OY
        fcx, fcy = um(f.GetPosition().x) - OX, um(f.GetPosition().y) - OY
        vx, vy = px0 - fcx, py0 - fcy
        vlen = math.hypot(vx, vy) or 1.0
        for dist_out in (0.55, 0.72, 0.90, 1.10, 1.30):
            dx_d, dy_d = px0 + (vx / vlen) * dist_out, py0 + (vy / vlen) * dist_out
            if box_free(dx_d - 0.15, dy_d - 0.15, dx_d + 0.15, dy_d + 0.15, obs):
                dot = pcbnew.PCB_SHAPE(b)
                dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
                dot.SetFilled(True)
                dot.SetLayer(pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS)
                dot.SetWidth(mm(0.05))
                dot.SetCenter(pcbnew.VECTOR2I(mm(OX + dx_d), mm(OY + dy_d)))
                dot.SetEnd(pcbnew.VECTOR2I(mm(OX + dx_d + 0.13), mm(OY + dy_d)))
                b.Add(dot)
                obs.append((dx_d - 0.17, dy_d - 0.17, dx_d + 0.17, dy_d + 0.17))
                p1_dots += 1
                break

    major_refs = [
        "U1", "U2", "U10", "U11", "U3", "U4", "U5", "U6", "U7", "U8", "U9",
        "L1", "Y1", "SW1", "SW2", "Q1", "Q2",
        "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8",
    ]
    des_placed = 0
    for r in major_refs:
        if r not in fps:
            continue
        f = fps[r]
        side = "F" if f.GetLayer() == pcbnew.F_Cu else "B"
        pboxes = [p.GetBoundingBox() for p in f.Pads()]
        if not pboxes:
            continue
        fx0 = min(um(bb.GetLeft()) - OX for bb in pboxes)
        fy0 = min(um(bb.GetTop()) - OY for bb in pboxes)
        fx1 = max(um(bb.GetRight()) - OX for bb in pboxes)
        fy1 = max(um(bb.GetBottom()) - OY for bb in pboxes)
        fcx, fcy = (fx0 + fx1) / 2.0, (fy0 + fy1) / 2.0
        placed_this = False
        for extra in (0.65, 0.95, 1.25, 1.60, 1.95):
            ring_pts = [
                (fcx, fy0 - extra, 0.0),
                (fcx, fy1 + extra, 0.0),
                (fx0 - extra - 0.25, fcy, 0.0),
                (fx1 + extra + 0.25, fcy, 0.0),
                (fx0 - extra, fcy, 90.0 if side == "F" else 0.0),
                (fx1 + extra, fcy, 90.0 if side == "F" else 0.0),
            ]
            for tx, ty, deg in ring_pts:
                if add_silk_label(r, tx, ty, side, deg, 0.80):
                    des_placed += 1
                    placed_this = True
                    break
            if placed_this:
                break

    for tr in b.GetTracks():
        tr.SetLocked(False)

    pcbnew.SaveBoard(str(pcb_path), b)
    pro_path.write_bytes(pro_bytes)
    print(f"[{spec.name}] post_silk saved ({seg_cnt} brackets, {des_placed} designators, {p1_dots} pin1 dots, 0 locked copper)", flush=True)
    os._exit(0)


if __name__ == "__main__":
    spec_arg = VARIANTS[sys.argv[1]]
    stage_arg = sys.argv[2]
    {
        "outline": stage_outline,
        "stack": stage_stack,
        "sync": stage_sync,
        "place": stage_place,
        "zones": stage_zones,
        "models": stage_models,
        "post_silk": stage_post_silk,
    }[stage_arg](spec_arg)
