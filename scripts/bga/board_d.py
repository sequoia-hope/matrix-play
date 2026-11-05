#!/usr/bin/env python3
"""board_d.py -- 8-layer PCB builder for round-pendant Variant D (5x IS31FL3745-CLS4-TR BGA).

One stage per process (pcbnew requirement):
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py outline
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py stack
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py sync
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py place
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py copper
    PENDANT_VARIANT=d python3 scripts/bga/board_d.py copper2
    PENDANT_VARIANT=d python3 scripts/bga/make_nets_d.py
"""
import csv
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/bga"))

VARIANT = os.environ.get("PENDANT_VARIANT", "d")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
PCB = HW / "round-pendant.kicad_pcb"
SCH = HW / "round-pendant.kicad_sch"
REF_PCB = ROOT / "hw/round-pendant/c-solid-z10/round-pendant.kicad_pcb"
VENDOR_ZONES = ROOT / "scripts/crunch/placement/vendor_zones.json"
MAP_CSV = ROOT / "design/study/d/matrix_map.csv"

OX, OY = 100.0, 100.0

BGA_CENTERS = {
    "U1": (-11.85, 1.80, 0.0),
    "U2": (-3.50, 12.00, 0.0),
    "U10": (-10.85, -8.95, 0.0),
    "U11": (9.80, -9.10, 0.0),
    "U12": (9.90, 0.90, 0.0),
}

# Retained fixed placements copied verbatim from c-solid-z10 so RP2350, regulator, crystal, flash, charger, USB, buttons stay exact.
KEEP_FROM_REF = {
    "U3", "U4", "U5", "U6", "U7", "U8", "Q1", "SW1", "SW2", "J1", "BT1", "L1", "Y1",
    *(f"C{i}" for i in range(1, 25) if i != 15),
    "R3", "R4", "R5", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17",
}


def outline():
    import pcbnew

    HW.mkdir(parents=True, exist_ok=True)
    b = pcbnew.NewBoard(str(PCB))
    b.SetCopperLayerCount(8)
    tb = b.GetTitleBlock()
    tb.SetTitle("round-pendant")
    tb.SetRevision("D")
    tb.SetDate("2026-11-04")
    tb.SetCompany("CERN-OHL-P-2.0")
    tb.SetComment(0, "235 RGB LEDs, 5x IS31FL3745 WLCSP-36, 8-layer ENIG")
    mm = pcbnew.FromMM
    c = pcbnew.PCB_SHAPE(b)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.Edge_Cuts)
    c.SetWidth(mm(0.1))
    c.SetCenter(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    c.SetEnd(pcbnew.VECTOR2I(mm(OX + 19.0), mm(OY)))
    b.Add(c)
    b.Save(str(PCB))
    print("outline saved:", PCB)


def stack():
    """Write 1.0 mm 8-layer ENIG stackup (matching scripts/crunch/layers/mk8.py)."""
    t = PCB.read_text()
    top_stack = [
        ("F.SilkS", "Top Silk Screen", None),
        ("F.Paste", "Top Solder Paste", None),
        ("F.Mask", "Top Solder Mask", 0.01),
        ("F.Cu", "copper", 0.035),
    ]
    names = ["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
    kinds = ["prepreg", "core"] * 3 + ["prepreg"]
    th_map = {"prepreg": 0.0764, "core": 0.1700}

    def lay(n, k, th):
        return f'\t\t\t(layer "{n}" (type "{k}")' + (f" (thickness {th})" if th else "") + ")"

    s = ["\t\t(stackup"]
    for n, k, th in top_stack:
        s.append(lay(n, k, th))
    for i, (n, k) in enumerate(zip(names, kinds), 1):
        s.append(
            f'\t\t\t(layer "dielectric {i}" (type "{k}") (thickness {th_map[k]})'
            ' (material "FR4") (epsilon_r 4.1) (loss_tangent 0.02))'
        )
        s.append(lay(n, "copper", 0.035 if n == "B.Cu" else 0.0152))
    s += [
        lay("B.Mask", "Bottom Solder Mask", 0.01),
        lay("B.Paste", "Bottom Solder Paste", None),
        lay("B.SilkS", "Bottom Silk Screen", None),
        '\t\t\t(copper_finish "ENIG")',
        "\t\t\t(dielectric_constraints no)",
        "\t\t)",
    ]
    if "\t\t(stackup" in t:
        t, n = re.subn(r"\t\t\(stackup.*?\n\t\t\)\n", lambda _: "\n".join(s) + "\n", t, count=1, flags=re.S)
        assert n == 1
    else:
        t = t.replace("(setup\n", "(setup\n" + "\n".join(s) + "\n", 1)
    t = re.sub(r"\(general\n\t\t\(thickness [\d.]+\)", "(general\n\t\t(thickness 1.0)", t)
    PCB.write_text(t)
    print("stack written")


def sync():
    from kicad_write import update_pcb

    update_pcb(SCH, PCB, new_parts_at=(OX, OY))
    print("synced PCB from schematic")


def place():
    import pcbnew

    b = pcbnew.LoadBoard(str(PCB))
    ref_b = pcbnew.LoadBoard(str(REF_PCB))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    ref_fps = {f.GetReference(): f for f in ref_b.GetFootprints()}

    def set_bcu(ref: str, x: float, y: float, raw_orient: float):
        f = fps[ref]
        if f.GetLayer() == pcbnew.F_Cu:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        f.SetOrientationDegrees(float(raw_orient))

    # 1. Place all 235 top-side RGB LEDs from design/study/d/matrix_map.csv.
    with MAP_CSV.open() as fp:
        for r in csv.DictReader(fp):
            f = fps[r["ref"]]
            f.SetPosition(pcbnew.VECTOR2I(mm(OX + float(r["x_mm"])), mm(OY + float(r["y_mm"]))))
            f.SetOrientationDegrees(-float(r["angle_deg"]))
            f.Reference().SetVisible(False)
            f.Value().SetVisible(False)

    # 2. Copy exact retained back-side placements from c-solid-z10.
    for ref in KEEP_FROM_REF:
        rf = ref_fps[ref]
        p = rf.GetPosition()
        set_bcu(ref, um(p.x) - OX, um(p.y) - OY, rf.GetOrientationDegrees())

    # 3. Place the 5 WLCSP-36 drivers (all SetOrientationDegrees(0.0) on B.Cu: Row F North, Row A South).
    for ref, (cx, cy, orient) in BGA_CENTERS.items():
        set_bcu(ref, cx, cy, orient)

    # Verify U2.D4 is at (-3.25, 11.75), the single LED-overlapped core site, leaving C3/C4/D3 100% clear.
    d4_p = next(p for p in fps["U2"].Pads() if p.GetNumber() == "D4").GetPosition()
    assert abs((um(d4_p.x) - OX) - (-3.25)) < 0.01 and abs((um(d4_p.y) - OY) - 11.75) < 0.01, (
        um(d4_p.x) - OX,
        um(d4_p.y) - OY,
    )

    # 4. Place each BGA's passives tangentially off Row F (North: RSET, VDD 100n+1u) and Row A (South: PVCC 100n+1u),
    # keeping Columns 1 & 6 (CS1..18) 100% unobstructed, and orienting North caps at 180 deg (pad 2 GND West = F4,
    # pad 1 VSYS East = F5) and South caps at 0 deg (pad 1 VSYS West = A3) for zero-crossing straight straps!
    # U1 (-11.85, 1.80)
    set_bcu("R30", -12.85, -0.80, 180.0)
    set_bcu("C33", -10.85, -0.80, 180.0)
    set_bcu("C34", -10.85, -1.80, 180.0)
    set_bcu("C32", -11.85, 4.40, 0.0)
    set_bcu("C31", -11.85, 5.40, 0.0)
    set_bcu("C30", -14.40, 4.80, 90.0)  # 22u 0603 bulk near U1.A3

    # U2 (-3.50, 12.00) -- compact North row at y=9.60 (between U4 bottom=8.78 and U2 top=10.36, West of R4 left=-1.78)
    set_bcu("C43", -6.80, 9.60, 0.0)
    set_bcu("R33", -4.80, 9.60, 180.0)  # R33.1 at -4.29 aligns directly above U2.F3 (-3.75)!
    set_bcu("C44", -2.80, 9.60, 180.0)
    set_bcu("C42", -4.40, 14.50, 180.0)  # cx=-4.40 rot=180 puts pad 1 VSYS at -3.92 right below U2.A3 (-3.75)
    set_bcu("C41", -2.40, 14.50, 180.0)
    set_bcu("C40", -6.25, 11.80, 90.0)  # 22u 0603 bulk near U2.A3

    # U10 (-10.85, -8.95)
    set_bcu("R50", -11.85, -11.55, 180.0)
    set_bcu("C53", -9.85, -11.55, 180.0)
    set_bcu("C54", -9.85, -12.55, 180.0)
    set_bcu("C52", -10.85, -6.35, 0.0)
    set_bcu("C51", -10.85, -5.35, 0.0)

    # U11 (9.80, -9.10)
    set_bcu("R60", 8.80, -11.70, 180.0)
    set_bcu("C63", 10.80, -11.70, 180.0)
    set_bcu("C64", 9.80, -12.75, 180.0)
    set_bcu("C62", 9.80, -6.50, 0.0)
    set_bcu("C61", 9.80, -5.50, 0.0)

    # U12 (9.90, 0.90)
    set_bcu("R70", 8.90, -1.70, 180.0)
    set_bcu("C73", 10.90, -1.70, 180.0)
    set_bcu("C74", 10.90, -2.70, 180.0)
    set_bcu("C72", 9.90, 3.50, 0.0)
    set_bcu("C71", 9.90, 4.50, 0.0)

    # 5. Relocated U9 (LIS2DW12) + passives in North-Center (+3V3 column), I2C0 & LED_SDB passives, CC/CHG pull-ups, TPs.
    set_bcu("U9", 4.40, -13.80, 180.0)  # VDD(9), VDD_IO(10) face South/North? Check with Decouples!
    # Check U9 pins 9 & 10 actual positions to place C25, C26, C27 right beside them!
    p9 = next(p for p in fps["U9"].Pads() if p.GetNumber() == "9").GetPosition()
    p9x, p9y = um(p9.x) - OX, um(p9.y) - OY
    dy_cap = -1.8 if p9y < -13.8 else 1.8
    set_bcu("C25", 2.60, -13.80 + dy_cap, 180.0)
    set_bcu("C26", 4.40, -13.80 + dy_cap, 180.0)
    set_bcu("C27", 6.20, -13.80 + dy_cap, 180.0)
    set_bcu("R20", 3.40, -11.40, 180.0)
    set_bcu("R19", 5.40, -11.40, 180.0)

    # I2C0 pull-ups (R21, R22 on +3V3) + LED_SDB pull-down/cap (R31, C35 to GND) W/NW of U3
    set_bcu("R21", -6.20, -9.80, 180.0)
    set_bcu("R22", -6.20, -11.20, 180.0)
    set_bcu("R31", -8.40, -3.40, 180.0)
    set_bcu("C35", -8.40, -2.00, 180.0)

    # USB CC1/CC2 5.1k resistors right beside J1.1/2
    set_bcu("R1", -6.20, 15.40, 180.0)
    set_bcu("R2", -8.30, 15.40, 180.0)

    # Charger PGOOD/CHG pull-ups (on +3V3 column near U3/U5) + SW1 resistor R18
    set_bcu("R6", 5.80, -9.40, 180.0)
    set_bcu("R7", 5.80, -8.20, 180.0)
    set_bcu("R18", 13.40, -10.80, 180.0)

    # Test points in open pockets
    for ref, tx, ty in (
        ("TP1", 7.40, 4.30),     # VSYS near C2/U5
        ("TP2", 5.80, -6.80),    # +3V3 inside +3V3 column
        ("TP3", 8.20, 9.00),     # VBAT near BT1/U5
        ("TP4", 6.20, -4.80),    # +1V1
        ("TP5", -14.20, -2.00),  # RUN
        ("TP8", -14.20, -0.40),  # GND
        ("TP6", 6.90, -13.80),   # SWCLK
        ("TP7", 6.90, -12.20),   # SWDIO
    ):
        set_bcu(ref, tx, ty, 180.0)

    # Legalize movable small passives/TPs if any courtyard touches, keeping all ICs and BGA core decouplers fixed.
    def cbox(f):
        q = f.GetCourtyard(pcbnew.B_CrtYd).BBox() if f.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() else f.GetBoundingBox(False, False)
        return [um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY]

    leg_list = [
        "C30", "C40", "C25", "C26", "C27", "R19", "R20",
        "R21", "R22", "R31", "C35", "R1", "R2", "R6", "R7", "R18",
        "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8",
    ]
    margin = 0.05
    boxes = {r: cbox(f) for r, f in fps.items() if not r.startswith("D") and r not in leg_list}
    for r in leg_list:
        f = fps[r]
        q = cbox(f)
        x0, y0 = um(f.GetPosition().x), um(f.GetPosition().y)
        best = None
        for ring in range(0, 140):
            rad = ring * 0.1
            steps = max(1, 12 * ring)
            for k in range(steps):
                a = 2 * math.pi * k / steps
                dx, dy = rad * math.cos(a), rad * math.sin(a)
                bb = [q[0] + dx, q[1] + dy, q[2] + dx, q[3] + dy]
                if max(math.hypot(u, v) for u in (bb[0], bb[2]) for v in (bb[1], bb[3])) > 18.6:
                    continue
                # Also keep >=1.2 mm away from BGA centers so legalized parts never intrude into BGA escape channels!
                if any(
                    not (bb[2] <= bx - 2.3 or bx + 2.3 <= bb[0] or bb[3] <= by - 2.3 or by + 2.3 <= bb[1])
                    for bx, by, _ in BGA_CENTERS.values()
                ) and r not in ("C30", "C40"):
                    continue
                if all(bb[2] + margin <= c[0] or c[2] + margin <= bb[0] or bb[3] + margin <= c[1] or c[3] + margin <= bb[1] for c in boxes.values()):
                    best = (dx, dy, bb, rad)
                    break
            if best:
                break
        if not best:
            raise SystemExit(f"legalize failed for {r}")
        dx, dy, bb, rad = best
        if rad > 0:
            f.SetPosition(pcbnew.VECTOR2I(mm(x0 + dx), mm(y0 + dy)))
            print(f"  legalize {r}: nudged {rad:.2f} mm to ({x0 + dx - OX:.2f}, {y0 + dy - OY:.2f})")
        boxes[r] = bb

    bcu_names = sorted(boxes.keys())
    for i, r1 in enumerate(bcu_names):
        a = boxes[r1]
        for r2 in bcu_names[i + 1 :]:
            if r1 in KEEP_FROM_REF and r2 in KEEP_FROM_REF:
                continue
            c = boxes[r2]
            if not (a[2] <= c[0] + 0.02 or c[2] <= a[0] + 0.02 or a[3] <= c[1] + 0.02 or c[3] <= a[1] + 0.02):
                raise SystemExit(f"B.Cu courtyard overlap: {r1} {a} vs {r2} {c}")

    pcbnew.SaveBoard(str(PCB), b)
    print("placed all Variant D footprints (0 B.Cu courtyard overlaps)")


def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    n = vx * vx + vy * vy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / n))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def copper():
    """Solid EPs on U3/U5, locked LED anode vias, thermal vias, 8-layer planes, RP2350 zones, BGA internal addr straps."""
    import pcbnew

    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    F_CU, B_CU = lid["F.Cu"], lid["B.Cu"]

    # 1. Enforce solid exposed pads on U3 (pad 61, 3.4x3.4 mm) and U5 (pad 17, 1.7x1.7 mm), keeping paste pads.
    EP = {"U3": "61", "U5": "17"}
    ep_boxes = {}
    for ref, num in EP.items():
        f = fps[ref]
        old = [p for p in f.Pads() if p.GetNumber() == num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        boxes = [p.GetBoundingBox() for p in old]
        x0, x1 = min(um(q.GetLeft()) for q in boxes), max(um(q.GetRight()) for q in boxes)
        y0, y1 = min(um(q.GetTop()) for q in boxes), max(um(q.GetBottom()) for q in boxes)
        net = old[0].GetNetCode()
        for p in list(f.Pads()):
            if p.GetNumber() == num and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                f.Remove(p)
        pd = pcbnew.PAD(f)
        pd.SetShape(pcbnew.PAD_SHAPE_RECT)
        pd.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        ls = pcbnew.LSET()
        ls.AddLayer(B_CU)
        ls.AddLayer(pcbnew.B_Mask)
        pd.SetLayerSet(ls)
        pd.SetSize(pcbnew.VECTOR2I(mm(x1 - x0), mm(y1 - y0)))
        pd.SetNumber(num)
        f.Add(pd)
        pd.SetPosition(pcbnew.VECTOR2I(mm((x0 + x1) / 2), mm((y0 + y1) / 2)))
        pd.SetOrientationDegrees(0)
        pd.SetNetCode(net)
        ep_boxes[ref] = (x0, y0, x1, y1, net)

    # 2. Pre-strap internal BGA ADDR1 (D4) and ADDR2 (E4) on B.Cu with zero escape vias!
    #    U1 (GND/GND): D4-E4-F4
    #    U2 (GND/SDA): D4-D3, E4-F4
    #    U10 (SCL/SCL): D4-E4-E3
    #    U11 (SCL/SDA): D4-D3, E4-E3
    #    U12 (VSYS/VSYS): D4-E4-F5
    addr_bridges = {
        "U1": [("D4", "E4"), ("E4", "F4")],
        "U2": [("D4", "D3"), ("E4", "F4")],
        "U10": [("D4", "E4"), ("E4", "E3")],
        "U11": [("D4", "D3"), ("E4", "E3")],
        "U12": [("D4", "E4"), ("E4", "F5")],
    }
    bga_stubs = []
    for ref, pairs in addr_bridges.items():
        pads_by_num = {p.GetNumber(): p for p in fps[ref].Pads()}
        for p1_n, p2_n in pairs:
            p1, p2 = pads_by_num[p1_n], pads_by_num[p2_n]
            assert p1.GetNetCode() == p2.GetNetCode(), f"{ref} {p1_n}/{p2_n} net mismatch"
            w_br = 0.20 if p1.GetNetname() == "VSYS" else 0.10
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(p1.GetPosition())
            t.SetEnd(p2.GetPosition())
            t.SetWidth(mm(w_br))
            t.SetLayer(B_CU)
            t.SetNetCode(p1.GetNetCode())
            t.SetLocked(True)
            b.Add(t)
            c1, c2 = p1.GetPosition(), p2.GetPosition()
            bga_stubs.append((um(c1.x), um(c1.y), um(c2.x), um(c2.y)))

    # 2a. Pre-strap A3 (VSYS -> South 100nF.1), F4 (GND -> North 100nF.2), F5 (VSYS -> North 100nF.1),
    #     and F3 (RSET -> RSET_resistor.1) with exact 90+45 deg B.Cu straps so all 20 BGA power/ground/RSET balls
    #     join their local passives directly without consuming escape vias or crossing!
    def add_90_45_strap(p_start, p_end, w_mm, net_code):
        x0, y0 = um(p_start.x), um(p_start.y)
        x1, y1 = um(p_end.x), um(p_end.y)
        dx, dy = x1 - x0, y1 - y0
        assert abs(dy) >= abs(dx) - 1e-6, f"expected mostly-vertical strap: ({x0},{y0})->({x1},{y1})"
        ym = y1 - math.copysign(abs(dx), dy)
        pm = pcbnew.VECTOR2I(mm(x0), mm(ym))
        for va, vb in ((p_start, pm), (pm, p_end)):
            if va.x == vb.x and va.y == vb.y:
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(va)
            t.SetEnd(vb)
            t.SetWidth(mm(w_mm))
            t.SetLayer(B_CU)
            t.SetNetCode(net_code)
            t.SetLocked(True)
            b.Add(t)
            bga_stubs.append((um(va.x), um(va.y), um(vb.x), um(vb.y)))

    for uref, c_vdd, c_pvcc, r_set in (
        ("U1", "C33", "C32", "R30"),
        ("U2", "C44", "C42", "R33"),
        ("U10", "C53", "C52", "R50"),
        ("U11", "C63", "C62", "R60"),
        ("U12", "C73", "C72", "R70"),
    ):
        upads = {p.GetNumber(): p for p in fps[uref].Pads()}
        vpads = {p.GetNumber(): p for p in fps[c_vdd].Pads()}
        ppads = {p.GetNumber(): p for p in fps[c_pvcc].Pads()}
        rpads = {p.GetNumber(): p for p in fps[r_set].Pads()}
        for b_num, c_pad, w_s in (("A3", ppads["1"], 0.20), ("F4", vpads["2"], 0.20), ("F5", vpads["1"], 0.20), ("F3", rpads["1"], 0.10)):
            bp = upads[b_num]
            assert bp.GetNetCode() == c_pad.GetNetCode(), f"{uref}.{b_num} net mismatch"
            add_90_45_strap(bp.GetPosition(), c_pad.GetPosition(), w_s, bp.GetNetCode())

    # 2a-iii. Pre-route USB_DM (R14.1 -> U7.6) and USB_DP (R15.1 -> U7.4) on B.Cu with 0 vias (exact 0/45/90 deg,
    #         0.15 mm width, >=0.16 mm gap, >=0.165 mm pad clearance) so DIFF_HS satisfies max 1 via deterministically!
    usb_stubs = []
    for net_name, pts_rel in (
        (
            "USB_DM",
            [(-1.500, 0.110), (-1.500, 1.530), (-1.250, 1.780), (-0.150, 1.780), (0.030, 1.960), (0.030, 8.130), (0.340, 8.440), (0.850, 8.440), (1.2725, 8.8625), (1.450, 8.8625)],
        ),
        (
            "USB_DP",
            [(-2.500, 0.110), (-2.500, 1.885), (-2.295, 2.090), (-0.380, 2.090), (-0.280, 2.190), (-0.280, 8.490), (-0.010, 8.760), (0.280, 8.760), (0.550, 9.030), (0.550, 9.700), (0.7875, 9.9375), (1.450, 9.9375)],
        ),
    ):
        nc = b.FindNet(net_name).GetNetCode()
        for (ax, ay), (bx, by) in zip(pts_rel, pts_rel[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(OX + ax), mm(OY + ay)))
            t.SetEnd(pcbnew.VECTOR2I(mm(OX + bx), mm(OY + by)))
            t.SetWidth(mm(0.15))
            t.SetLayer(B_CU)
            t.SetNetCode(nc)
            t.SetLocked(True)
            b.Add(t)
            usb_stubs.append((OX + ax, OY + ay, OX + bx, OY + by))

    # 3. Place one locked anode via per LED (D1..D235), keeping U3/U5 solid EPs, BGA core+escape, and L1/reg clear.
    VIA_R, CL, STUB = 0.125, 0.09, 0.06
    HOLE = max(VIA_R + CL, 0.075 + 0.20)  # 0.275 mm

    obst = []
    holes = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if ref.startswith("D"):
            continue
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH):
                c = p.GetPosition()
                holes.append((um(c.x), um(c.y), um(p.GetDrillSizeX()) / 2))
            elif p.IsOnLayer(B_CU):
                bb = p.GetBoundingBox()
                obst.append((um(bb.GetLeft()), um(bb.GetTop()), um(bb.GetRight()), um(bb.GetBottom())))

    leds = {f.GetReference(): f for f in b.GetFootprints() if f.GetReference().startswith("D")}
    tops = []
    for ref, f in leds.items():
        a = math.radians(-f.GetOrientationDegrees())
        ca, sa = math.cos(a), math.sin(a)
        for p in f.Pads():
            c = p.GetPosition()
            tops.append((um(c.x), um(c.y), ca, sa, ref))

    def top_dist(x, y, skip=None):
        best = 9.0
        for px, py, c, s_, _ in tops:
            if abs(px - x) > 1.0 or abs(py - y) > 1.0 or (skip and abs(px - skip[0]) < 1e-3 and abs(py - skip[1]) < 1e-3):
                continue
            dx, dy = x - px, y - py
            u, v = abs(c * dx + s_ * dy) - 0.225, abs(-s_ * dx + c * dy) - 0.225
            best = min(best, math.hypot(max(u, 0.0), max(v, 0.0)))
        return best

    u3_p = fps["U3"].GetPosition()
    ux, uy = um(u3_p.x), um(u3_p.y)
    l1_p = fps["L1"].GetPosition()
    lx, ly = um(l1_p.x), um(l1_p.y)
    bga_abs = [(OX + cx, OY + cy) for cx, cy, _ in BGA_CENTERS.values()]

    def back_free(x, y):
        if math.hypot(x - OX, y - OY) > 18.6:
            return False
        for a, c, e, g in obst:
            dx = max(a - x, 0.0, x - e)
            dy = max(c - y, 0.0, y - g)
            if dx * dx + dy * dy < HOLE * HOLE:
                return False
        for hx, hy, hr in holes:
            if math.hypot(x - hx, y - hy) < hr + 0.075 + 0.20:
                return False
        for sx0, sy0, sx1, sy1 in bga_stubs:
            if seg_dist(x, y, sx0, sy0, sx1, sy1) < HOLE + 0.105:
                return False
        for ux0, uy0, ux1, uy1 in usb_stubs:
            if seg_dist(x, y, ux0, uy0, ux1, uy1) < max(HOLE + 0.075, VIA_R + 0.15 + 0.075) + 0.005:
                return False
        # Keep LED anode vias completely out of every WLCSP-36 body + escape collar (+-2.05 mm).
        for bx, by in bga_abs:
            if abs(x - bx) < 2.05 and abs(y - by) < 2.05:
                return False
        m = max(abs(x - ux), abs(y - uy))
        if 1.7 - VIA_R - CL < m < 2.2 + VIA_R + CL:
            return False  # U3 1V1 ring
        if abs(x - lx) < 1.3 + VIA_R + CL and abs(y - ly) < 1.1 + VIA_R + CL:
            return False  # L1 keepout
        if OX - 0.9 < x < OX + 0.1 and OY - 3.3 < y < OY - 0.9:
            return False
        if OX + 1.2 < x < OX + 3.0 and OY - 2.9 < y < OY + 1.5:
            return False  # reg_box
        return True

    def fan_free(x, y):
        # Tier-1 preference: leave U3 fanout ring, U3-to-flash corridor, U4-to-U7 USB corridor, and a 2.50 mm ring around each BGA free when a short stub can step aside.
        if 3.0 < max(abs(x - ux), abs(y - uy)) < 5.3:
            return False
        if any(max(abs(x - bx), abs(y - by)) < 2.50 for bx, by in bga_abs):
            return False
        if OX - 6.5 < x < OX + 1.6 and OY + 8.1 < y < OY + 10.5:
            return False
        return not (OX - 5.2 < x < OX + 1.8 and OY - 3.3 < y < OY + 3.0)

    placed = []
    stubs = []
    v_sep_val = max(VIA_R + STUB + CL, 0.075 + 0.20 + STUB)

    # 2b. Place locked 0.25/0.15 mm vias-in-pad on ALL F.Cu-legal core + inner-ring balls of each WLCSP-36
    #     (never outer-ring balls, so outer-ring 0.30 mm gaps stay 100% open for remaining inner-ring B.Cu escapes!).
    INNER_AND_CORE = {"C3", "C4", "D3", "B2", "B3", "B4", "B5", "C2", "D2", "E2", "C5", "D5", "E5", "E3"}
    core_via_cnt = 0
    for uref in BGA_CENTERS:
        for p in fps[uref].Pads():
            if p.GetNumber() in INNER_AND_CORE:
                cp = p.GetPosition()
                vx, vy = um(cp.x), um(cp.y)
                # Must clear top F.Cu LEDs (>=0.276 mm) AND foreign B.Cu bga_stubs (>=0.276 + w/2)
                if top_dist(vx, vy) < HOLE + 0.001:
                    continue
                if any(
                    seg_dist(vx, vy, sx0, sy0, sx1, sy1) < 0.38
                    for sx0, sy0, sx1, sy1 in bga_stubs
                    if not (abs(vx - sx0) < 1e-3 and abs(vy - sy0) < 1e-3) and not (abs(vx - sx1) < 1e-3 and abs(vy - sy1) < 1e-3)
                ):
                    continue
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(cp)
                v.SetWidth(mm(0.25))
                v.SetDrill(mm(0.15))
                v.SetLayerPair(F_CU, B_CU)
                v.SetNetCode(p.GetNetCode())
                v.SetLocked(True)
                b.Add(v)
                placed.append((vx, vy))
                core_via_cnt += 1
    print(f"WLCSP-36 core+inner vias-in-pad placed: {core_via_cnt}")

    def crosses(t, u):
        o = lambda a, c, e, g, h, i: (e - a) * (i - c) - (g - c) * (h - a)
        return o(*t, u[0], u[1]) * o(*t, u[2], u[3]) < 0 and o(*u, t[0], t[1]) * o(*u, t[2], t[3]) < 0

    def clear_via(x, y):
        return all(math.hypot(x - a, y - c) >= 0.41 for a, c in placed) and all(
            seg_dist(x, y, *t) >= v_sep_val for t in stubs
        )

    def stub_ok(x0, y0, x, y):
        n = max(2, int(math.hypot(x - x0, y - y0) / 0.04))
        for i in range(1, n + 1):
            px, py = x0 + (x - x0) * i / n, y0 + (y - y0) * i / n
            if top_dist(px, py, skip=(x0, y0)) < STUB + CL:
                return False
        for a, c in placed:
            if seg_dist(a, c, x0, y0, x, y) < v_sep_val:
                return False
        return all(
            min(seg_dist(t[0], t[1], x0, y0, x, y), seg_dist(t[2], t[3], x0, y0, x, y)) >= 2 * STUB + CL
            and not crosses(t, (x0, y0, x, y))
            for t in stubs
        )

    ring_radii = (0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.1, 1.25, 1.4, 1.6, 1.8, 2.1, 2.4, 2.8, 3.2, 3.6)
    rings = [(r, 2 * math.pi * k / 48) for r in ring_radii for k in range(48)]
    stat = {"in_pad": 0, "stub": 0}
    blocked = []
    lens = []

    # Place constrained LEDs (over U3/U5/L1/BGAs) FIRST so unconstrained neighbors never box in their escape stub!
    def led_priority(ref_name: str):
        p = leds[ref_name].GetPosition()
        lx0, ly0 = um(p.x), um(p.y)
        in_hard = not back_free(lx0, ly0) or not fan_free(lx0, ly0)
        return (0 if in_hard else 1, math.hypot(lx0 - ux, ly0 - uy), int(ref_name[1:]))

    for ref in sorted(leds, key=led_priority):
        f = leds[ref]
        base = f.GetOrientationDegrees()
        best = None
        for tier in (True, False):
            for k in range(4):
                f.SetOrientationDegrees(base + 90 * k)
                pad = next(p for p in f.Pads() if p.GetNumber() == "3")
                c = pad.GetPosition()
                x0, y0 = um(c.x), um(c.y)
                if (not tier or fan_free(x0, y0)) and back_free(x0, y0) and clear_via(x0, y0):
                    best = (0.0, k, x0, y0, x0, y0)
                    break
                for r, a in rings:
                    if best and r >= best[0]:
                        break
                    x, y = x0 + r * math.cos(a), y0 + r * math.sin(a)
                    if (not tier or fan_free(x, y)) and back_free(x, y) and clear_via(x, y) and top_dist(x, y) >= HOLE and stub_ok(x0, y0, x, y):
                        best = (r, k, x0, y0, x, y)
                        break
            if best:
                break
        if not best:
            f.SetOrientationDegrees(base)
            blocked.append(ref)
            continue
        r, k, x0, y0, x, y = best
        f.SetOrientationDegrees(base + 90 * k)
        pad = next(p for p in f.Pads() if p.GetNumber() == "3")
        net = pad.GetNetCode()
        small = max(abs(x - ux), abs(y - uy)) < 2.95
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(0.20 if small else 0.25))
        v.SetDrill(mm(0.10 if small else 0.15))
        v.SetLayerPair(F_CU, B_CU)
        v.SetNetCode(net)
        v.SetLocked(True)
        b.Add(v)
        placed.append((x, y))
        if r:
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
            t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
            t.SetWidth(mm(2 * STUB))
            t.SetLayer(F_CU)
            t.SetNetCode(net)
            t.SetLocked(True)
            b.Add(t)
            stubs.append((x0, y0, x, y))
            stat["stub"] += 1
            lens.append(r)
        else:
            stat["in_pad"] += 1

    print(f"anode vias: {stat}, max_stub={max(lens or [0]):.2f} mm, blocked={blocked}")
    assert not blocked, f"Blocked LED anodes: {blocked}"

    # 4. Assert zero foreign vias inside U3/U5 solid EPs, then place GND thermal vias inside U3 (9) & U5 (up to 4).
    gnd_code = b.FindNet("GND").GetNetCode()
    th_counts = {"U3": 9, "U5": 4}
    th_got = {}
    for ref, (x0, y0, x1, y1, _) in ep_boxes.items():
        foreign = [(a, c) for a, c in placed if x0 <= a <= x1 and y0 <= c <= y1]
        assert not foreign, f"Foreign via inside {ref} solid EP: {foreign}"
        cands = []
        xv = x0 + 0.15
        while xv < x1 - 0.10:
            yv = y0 + 0.15
            while yv < y1 - 0.10:
                cands.append((xv, yv))
                yv += 0.10
            xv += 0.10
        cx_ep, cy_ep = (x0 + x1) / 2, (y0 + y1) / 2
        cands.sort(key=lambda q: math.hypot(q[0] - cx_ep, q[1] - cy_ep))
        got = []
        for q in cands:
            if len(got) >= th_counts[ref]:
                break
            if (
                top_dist(*q) >= HOLE
                and all(math.hypot(q[0] - a, q[1] - c) >= 0.41 for a, c in placed)
                and all(seg_dist(q[0], q[1], *t) >= VIA_R + STUB + CL for t in stubs)
                and all(math.hypot(q[0] - a, q[1] - c) >= 0.75 for a, c in got)
            ):
                got.append(q)
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(q[0]), mm(q[1])))
                v.SetWidth(mm(0.25))
                v.SetDrill(mm(0.15))
                v.SetLayerPair(F_CU, B_CU)
                v.SetNetCode(gnd_code)
                v.SetLocked(True)
                b.Add(v)
                placed.append(q)
        th_got[ref] = len(got)
    print("solid EP thermal vias:", th_got)

    # 5. Add 8-layer planes (GND on In2.Cu, VSYS + central 3V3 island on In5.Cu) + RP2350 zones & regulator copper.
    def poly(pts):
        p = pcbnew.SHAPE_POLY_SET()
        p.NewOutline()
        for px, py in pts:
            p.Append(mm(OX + px), mm(OY + py))
        p.thisown = False
        return p

    def add_zone(name, layer, net, pts, prio, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.1, clear=0.09):
        z = pcbnew.ZONE(b)
        z.SetZoneName(name)
        z.SetLayer(layer)
        z.SetNet(b.FindNet(net))
        z.SetAssignedPriority(prio)
        z.SetPadConnection(connect)
        z.SetMinThickness(mm(minw))
        z.SetThermalReliefGap(mm(0.2))
        z.SetThermalReliefSpokeWidth(mm(0.2))
        z.SetLocalClearance(mm(clear))
        z.SetOutline(poly(pts))
        b.Add(z)
        return z

    def add_area(name, layer, pts, tracks=False, pour=False):
        k = pcbnew.ZONE(b)
        k.SetIsRuleArea(True)
        k.SetZoneName(name)
        k.SetLayer(layer)
        k.SetDoNotAllowCopperPour(pour)
        k.SetDoNotAllowTracks(tracks)
        k.SetDoNotAllowVias(False)
        k.SetDoNotAllowPads(False)
        k.SetDoNotAllowFootprints(False)
        k.SetOutline(poly(pts))
        b.Add(k)
        return k

    circle = [(18.8 * math.cos(2 * math.pi * k / 96), 18.8 * math.sin(2 * math.pi * k / 96)) for k in range(96)]
    add_zone("plane GND", lid["In2.Cu"], "GND", circle, 0, clear=0.2)
    add_zone("plane VSYS", lid["In5.Cu"], "VSYS", circle, 0, clear=0.2)

    # Central +3V3 column on In5.Cu: reaches the North r=18.8 edge between x=1.5 and x=7.1 so plane VSYS is a
    # simply-connected C-shaped horseshoe (1 piece, ZERO interior donut holes — ultraroute treats zone filled_polygons
    # as hole-free outer rings!) while covering U9+caps+R19/20, U3+caps+R6/7+R21/22+TP2, U6.OUT+C4, U4+C22, and U5.EN1,
    # and leaving ALL 5 BGAs + ALL 22 BGA VSYS caps + U5.OUT + C2 on the continuous outer VSYS plane!
    r_pl = 18.95
    a_n0 = math.atan2(-math.sqrt(r_pl * r_pl - 1.5 * 1.5), 1.5)
    a_n1 = math.atan2(-math.sqrt(r_pl * r_pl - 7.1 * 7.1), 7.1)
    north_arc = [(r_pl * math.cos(a_n0 + (a_n1 - a_n0) * k / 16), r_pl * math.sin(a_n0 + (a_n1 - a_n0) * k / 16)) for k in range(17)]
    island_3v3 = (
        [(-7.6, -14.2), (1.5, -14.2)]
        + north_arc
        + [
            (7.1, -3.0),
            (4.75, -3.0),
            (4.75, 5.0),
            (2.7, 5.0),
            (2.7, 8.6),
            (-6.9, 8.6),
            (-6.9, 1.4),
            (-5.75, 1.4),   # notch around U6.IN (-6.5, 0.1) & C3 (-6.3, -1.6) so they stay over VSYS!
            (-5.75, -2.5),
            (-7.6, -2.5),
        ]
    )
    add_zone("plane 3V3", lid["In5.Cu"], "+3V3", island_3v3, 1, clear=0.2)

    ux_rel, uy_rel = ux - OX, uy - OY
    sq = lambda h: [(ux_rel - h, uy_rel - h), (ux_rel + h, uy_rel - h), (ux_rel + h, uy_rel + h), (ux_rel - h, uy_rel + h)]
    add_zone("RP2350 band", B_CU, "+3V3", sq(3.5), 1, minw=0.1, clear=0.09)
    add_zone("RP2350 ring", B_CU, "+1V1", sq(2.2), 3, connect=pcbnew.ZONE_CONNECTION_FULL, minw=0.2, clear=0.09)

    # LX cutouts under switch node on In5.Cu and In6.Cu (In2.Cu GND stays unbroken per u3fix.py).
    lxpads = [p for p in fps["L1"].Pads() if p.GetNetname().endswith("VREG_LX")] + [
        p for p in fps["U3"].Pads() if p.GetNetname().endswith("VREG_LX")
    ]
    lxbbs = [p.GetBoundingBox() for p in lxpads]
    lx0 = min(um(q.GetLeft()) for q in lxbbs) - OX - 0.3
    lx1 = max(um(q.GetRight()) for q in lxbbs) - OX + 0.3
    ly0 = min(um(q.GetTop()) for q in lxbbs) - OY - 0.3
    ly1 = max(um(q.GetBottom()) for q in lxbbs) - OY + 0.3
    lx_box = [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)]
    add_area("LX no plane", lid["In5.Cu"], lx_box, tracks=False, pour=True)
    add_area("LX no copper In6", lid["In6.Cu"], lx_box, tracks=True, pour=True)

    # U3 / regulator named rule areas referenced by round-pendant.kicad_dru.
    add_area("U3 ring", B_CU, sq(2.9), tracks=False, pour=False)
    add_area(
        "U3 ring vias",
        B_CU,
        [
            (ux_rel - 2.3, uy_rel - 2.3),
            (ux_rel + 2.3, uy_rel - 2.3),
            (ux_rel + 2.3, uy_rel + 2.3),
            (ux_rel - 2.3, uy_rel + 2.3),
            (ux_rel - 2.3, uy_rel),
            (ux_rel - 1.6, uy_rel),
            (ux_rel - 1.6, uy_rel + 1.6),
            (ux_rel + 1.6, uy_rel + 1.6),
            (ux_rel + 1.6, uy_rel - 1.6),
            (ux_rel - 1.6, uy_rel - 1.6),
            (ux_rel - 1.6, uy_rel - 0.002),
            (ux_rel - 2.3, uy_rel - 0.002),
        ],
    )
    add_area("reg corner", B_CU, [(ux_rel + 0.95, uy_rel + 3.0), (ux_rel + 3.45, uy_rel + 3.0), (ux_rel + 3.45, uy_rel + 8.1), (ux_rel + 0.95, uy_rel + 8.1)])
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

    # DVDD fingers + DVDD & IOVDD cap fingers + LDO fingers + vendor regulator zones (from u3fix.py, CAPS3V3=1).
    for p in fps["U3"].Pads():
        if p.GetNumber() in ("6", "23", "39", "50"):
            c = p.GetPosition()
            px, py = um(c.x) - OX - ux_rel, um(c.y) - OY - uy_rel
            if abs(px) > abs(py):
                s = 1 if px > 0 else -1
                pts = [(ux_rel + s * 2.1, uy_rel + py - 0.1), (ux_rel + s * 3.5, uy_rel + py - 0.1), (ux_rel + s * 3.5, uy_rel + py + 0.1), (ux_rel + s * 2.1, uy_rel + py + 0.1)]
            else:
                s = 1 if py > 0 else -1
                pts = [(ux_rel + px - 0.1, uy_rel + s * 2.1), (ux_rel + px + 0.1, uy_rel + s * 2.1), (ux_rel + px + 0.1, uy_rel + s * 3.5), (ux_rel + px - 0.1, uy_rel + s * 3.5)]
            add_zone(f"DVDD finger {p.GetNumber()}", B_CU, "+1V1", pts, 2, minw=0.1)

    for pin, cap, net_n, prefix in (
        ("6", "C20", "+1V1", "DVDD"),
        ("23", "C19", "+1V1", "DVDD"),
        ("39", "C21", "+1V1", "DVDD"),
        ("1", "C8", "+3V3", "IOVDD"),
        ("11", "C9", "+3V3", "IOVDD"),
        ("20", "C10", "+3V3", "IOVDD"),
        ("30", "C11", "+3V3", "IOVDD"),
        ("38", "C12", "+3V3", "IOVDD"),
        ("44", "C14", "+3V3", "IOVDD"),
        ("54", "C13", "+3V3", "IOVDD"),
    ):
        a = next(p for p in fps["U3"].Pads() if p.GetNumber() == pin).GetPosition()
        c_ = next(p for p in fps[cap].Pads() if p.GetNetname() == net_n).GetPosition()
        ax, ay, cx_, cy_ = um(a.x) - OX, um(a.y) - OY, um(c_.x) - OX, um(c_.y) - OY
        if abs(ax - ux_rel) > abs(ay - uy_rel):
            ox_, oy_ = ux_rel + (1 if ax > ux_rel else -1) * 4.15, ay
            add_zone(f"{prefix} out {pin}", B_CU, net_n, [(ax, ay - 0.1), (ox_, ay - 0.1), (ox_, ay + 0.1), (ax, ay + 0.1)], 9, minw=0.1)
        else:
            ox_, oy_ = ax, uy_rel + (1 if ay > uy_rel else -1) * 4.15
            add_zone(f"{prefix} out {pin}", B_CU, net_n, [(ax - 0.1, ay), (ax - 0.1, oy_), (ax + 0.1, oy_), (ax + 0.1, ay)], 9, minw=0.1)
        d_ = math.hypot(cx_ - ox_, cy_ - oy_)
        nx, ny = -(cy_ - oy_) / d_ * 0.1, (cx_ - ox_) / d_ * 0.1
        add_zone(f"{prefix} cap {pin}", B_CU, net_n, [(ox_ + nx, oy_ + ny), (cx_ + nx, cy_ + ny), (cx_ - nx, cy_ - ny), (ox_ - nx, oy_ - ny)], 10, minw=0.1)

    for pa, pc, net_, nm in (("1", "1", "+3V3", "LDO out"), ("2", "2", "GND", "LDO gnd")):
        a_ = next(p for p in fps["U6"].Pads() if p.GetNumber() == pa).GetPosition()
        c_ = next(p for p in fps["C4"].Pads() if p.GetNumber() == pc).GetPosition()
        ax, ay, cx_, cy_ = um(a_.x) - OX, um(a_.y) - OY, um(c_.x) - OX, um(c_.y) - OY
        d_ = math.hypot(cx_ - ax, cy_ - ay)
        nx, ny = -(cy_ - ay) / d_ * 0.1, (cx_ - ax) / d_ * 0.1
        add_zone(nm, B_CU, net_, [(ax + nx, ay + ny), (cx_ + nx, cy_ + ny), (cx_ - nx, cy_ - ny), (ax - nx, ay - ny)], 9, minw=0.1)

    vzones = json.loads(VENDOR_ZONES.read_text())
    for q in vzones:
        if q["prio"] <= 3:
            continue
        net = {"/VREG_LX": "/MCU/VREG_LX"}.get(q["net"], q["net"])
        add_zone(f"vendor {net}", B_CU, net, [(ux_rel + x, uy_rel - y) for x, y in q["pts"]], q["prio"], minw=min(q["minw"], 0.1), clear=0.12)

    add_zone(
        "FB finger",
        B_CU,
        "+1V1",
        [(ux_rel + x, uy_rel - y) for x, y in [(1.1, -3.35), (1.3, -3.35), (1.3, -3.9), (1.1, -4.05), (1.1, -5.0), (0.98, -5.0), (0.98, -3.95), (1.1, -3.85)]],
        8,
        minw=0.09,
    )

    # PGND 2 vias + CFILT GND via
    all_pads = [
        (um(q.GetLeft()), um(q.GetTop()), um(q.GetRight()), um(q.GetBottom()), p.GetNetname())
        for f in b.GetFootprints()
        if not f.GetReference().startswith("D")
        for p in f.Pads()
        for q in [p.GetBoundingBox()]
    ]

    def site_free_abs(xa, ya, net_name, r_req=0.275, sep=0.41):
        if top_dist(xa, ya) < r_req:
            return False
        for a, e, g, h, n in all_pads:
            if n != net_name and math.hypot(max(a - xa, 0.0, xa - g), max(e - ya, 0.0, ya - h)) < r_req:
                return False
        if any(math.hypot(xa - a, ya - e) < sep for a, e in placed):
            return False
        if any(seg_dist(xa, ya, *t) < r_req + 0.06 for t in stubs + bga_stubs):
            return False
        return True

    gz = [q for q in vzones if q["prio"] == 4][0]["pts"]

    def in_poly(px, py, poly_pts):
        c = False
        for i in range(len(poly_pts)):
            a, e = poly_pts[i], poly_pts[i - 1]
            if (a[1] > py) != (e[1] > py) and px < (e[0] - a[0]) * (py - a[1]) / (e[1] - a[1]) + a[0]:
                c = not c
        return c

    pg_sites = []
    for i in range(90):
        for j in range(80):
            fx, fy = 2.3 + i * 0.0125, -5.8 + j * 0.0375
            if in_poly(fx, fy, gz):
                xa, ya = OX + ux_rel + fx, OY + uy_rel - fy
                if site_free_abs(xa, ya, "GND"):
                    pg_sites.append((math.hypot(fx - 3.1, fy + 5.2), xa, ya))
    pg_sites.sort()
    pg_pair = None
    for s_, xa, ya in pg_sites:
        for t_, xb, yb in pg_sites:
            if 0.41 <= math.hypot(xa - xb, ya - yb) <= 0.80 and t_ >= s_:
                pg_pair = ((xa, ya), (xb, yb))
                break
        if pg_pair:
            break
    print("PGND vias:", [(round(x - OX, 2), round(y - OY, 2)) for x, y in (pg_pair or [])])
    for xa, ya in pg_pair or []:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(xa), mm(ya)))
        v.SetWidth(mm(0.25))
        v.SetDrill(mm(0.15))
        v.SetLayerPair(F_CU, B_CU)
        v.SetNetCode(gnd_code)
        v.SetLocked(True)
        b.Add(v)
        placed.append((xa, ya))

    c17_gnd = next(p for p in fps["C17"].Pads() if p.GetNetname() == "GND").GetPosition()
    c17x, c17y = um(c17_gnd.x), um(c17_gnd.y)
    best_cf = None
    for i in range(-20, 21):
        for j in range(-20, 21):
            xa, ya = c17x + i * 0.05, c17y + j * 0.05
            d = math.hypot(i * 0.05, j * 0.05)
            if d < 1.2 and site_free_abs(xa, ya, "GND") and (best_cf is None or d < best_cf[0]):
                best_cf = (d, xa, ya)
    if best_cf:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(best_cf[1]), mm(best_cf[2])))
        v.SetWidth(mm(0.25))
        v.SetDrill(mm(0.15))
        v.SetLayerPair(F_CU, B_CU)
        v.SetNetCode(gnd_code)
        v.SetLocked(True)
        b.Add(v)
        placed.append((best_cf[1], best_cf[2]))
        print(f"CFILT via: ({best_cf[1] - OX:.2f}, {best_cf[2] - OY:.2f})")

    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    print("copper stage 1 saved")


def copper2():
    """Second copper pass (fresh process after reload): U3 +3V3 band vias + parallel power vias (U5, BT1, C4, C13)."""
    import pcbnew

    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    um = pcbnew.ToMM
    lid = {b.GetLayerName(l): l for l in range(64) if b.GetLayerName(l).endswith(".Cu")}
    F_CU, B_CU = lid["F.Cu"], lid["B.Cu"]
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    leds = []
    for f in b.GetFootprints():
        if f.GetReference().startswith("D"):
            a = math.radians(-f.GetOrientationDegrees())
            ca, sa = math.cos(a), math.sin(a)
            for p in f.Pads():
                c = p.GetPosition()
                leds.append((um(c.x) - OX, um(c.y) - OY, ca, sa, p.GetNetname()))
    pads = [
        (um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY, p.GetNetname())
        for f in b.GetFootprints()
        if not f.GetReference().startswith("D")
        for p in f.Pads()
        for q in [p.GetBoundingBox()]
    ]
    vias = [(um(t.GetPosition().x) - OX, um(t.GetPosition().y) - OY, t.GetNetname()) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    stubs = [
        (um(t.GetStart().x) - OX, um(t.GetStart().y) - OY, um(t.GetEnd().x) - OX, um(t.GetEnd().y) - OY, t.GetNetname(), t.GetLayerName(), um(t.GetWidth()))
        for t in b.GetTracks()
        if not isinstance(t, pcbnew.PCB_VIA)
    ]
    keepclear = [
        (um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY)
        for z in b.Zones()
        if z.GetZoneName().startswith("DVDD")
        for q in [z.GetBoundingBox()]
    ]
    u3_pos = fps["U3"].GetPosition()
    ux3, uy3 = um(u3_pos.x) - OX, um(u3_pos.y) - OY

    def pd_led(x, y, L):
        du = abs(L[2] * (x - L[0]) + L[3] * (y - L[1])) - 0.225
        dv = abs(-L[3] * (x - L[0]) + L[2] * (y - L[1])) - 0.225
        return math.hypot(max(du, 0.0), max(dv, 0.0))

    def boxd(x, y, a, e, g, h):
        return math.hypot(max(a - x, 0.0, x - g), max(e - y, 0.0, y - h))

    def band_free(x, y):
        if max(abs(x - ux3), abs(y - uy3)) < 2.43:
            return False
        if any(boxd(x, y, *kc) < 0.32 for kc in keepclear):
            return False
        if any(abs(L[0] - x) < 1.2 and abs(L[1] - y) < 1.2 and pd_led(x, y, L) < 0.25 for L in leds):
            return False
        if any(n != "+3V3" and boxd(x, y, a, e, g, h) < 0.25 for a, e, g, h, n in pads):
            return False
        if any(math.hypot(x - a, y - e) < 0.37 for a, e, _ in vias):
            return False
        if any(seg_dist(x, y, a, e, g, h) < 0.31 for a, e, g, h, _, _, _ in stubs):
            return False
        return True

    # 1. U3 +3V3 band pieces without a plane via get a 0.2/0.1 via (u3fix2.py).
    v3_code = b.FindNet("+3V3").GetNetCode()
    added_band = 0
    for z in b.Zones():
        if z.GetZoneName() == "RP2350 band":
            ps = z.GetFilledPolysList(B_CU)
            for i in range(ps.OutlineCount()):
                ol = pcbnew.SHAPE_POLY_SET()
                ol.NewOutline()
                o = ps.Outline(i)
                for k in range(o.PointCount()):
                    ol.Append(o.CPoint(k))
                if ol.Area() / 1e12 < 0.05:
                    continue
                has = any(t.GetNetCode() == v3_code and ol.Contains(t.GetPosition()) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA))
                if has:
                    continue
                q = ol.BBox()
                X0, Y0, X1, Y1 = um(q.GetLeft()) - OX, um(q.GetTop()) - OY, um(q.GetRight()) - OX, um(q.GetBottom()) - OY
                done = False
                for kx in range(int((X1 - X0) / 0.05) + 1):
                    if done:
                        break
                    for ky in range(int((Y1 - Y0) / 0.05) + 1):
                        x, y = X0 + kx * 0.05, Y0 + ky * 0.05
                        if ol.Contains(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))) and band_free(x, y):
                            v = pcbnew.PCB_VIA(b)
                            v.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
                            v.SetWidth(mm(0.20))
                            v.SetDrill(mm(0.10))
                            v.SetLayerPair(F_CU, B_CU)
                            v.SetNetCode(v3_code)
                            v.SetLocked(True)
                            b.Add(v)
                            vias.append((x, y, "+3V3"))
                            added_band += 1
                            done = True
                            break
    print("U3 band +3V3 vias added:", added_band)

    # 2. Power via reservations (U5 OUT VSYS, U5 BAT & BT1 VBAT linked on In4/In6, C4/C13 +3V3 & GND).
    def site_ok(x, y, net):
        if any(abs(bx - x) < 2.05 and abs(by - y) < 2.05 for bx, by, _ in BGA_CENTERS.values()):
            return False
        for L in leds:
            if abs(L[0] - x) < 1.2 and abs(L[1] - y) < 1.2 and L[4] != net and pd_led(x, y, L) < 0.275:
                return False
        if any(n != net and boxd(x, y, a, e, g, h) < 0.275 for a, e, g, h, n in pads):
            return False
        if any(math.hypot(x - a, y - e) < (0.41 if n != net else 0.36) for a, e, n in vias):
            return False
        return not any(n != net and seg_dist(x, y, a, e, g, h) < 0.276 + w / 2 and lay in ("F.Cu", "B.Cu") for a, e, g, h, n, lay, w in stubs)

    def bpath_ok(x0, y0, x, y, net, w=0.3):
        k = max(2, int(math.hypot(x - x0, y - y0) / 0.03))
        for i in range(k + 1):
            px, py = x0 + (x - x0) * i / k, y0 + (y - y0) * i / k
            if any(n != net and boxd(px, py, a, e, g, h) < 0.095 + w / 2 for a, e, g, h, n in pads):
                return False
            if any(n != net and math.hypot(px - a, py - e) < max(0.15 + 0.095, 0.075 + 0.205) + w / 2 for a, e, n in vias):
                return False
            if any(
                n != net and lay == "B.Cu" and seg_dist(px, py, a, e, g, h) < (0.155 if "USB_" in n else 0.095) + (w + sw) / 2
                for a, e, g, h, n, lay, sw in stubs
            ):
                return False
        return True

    def add_track(x0, y0, x, y, net, lay, w=0.3):
        dx, dy = x - x0, y - y0
        if abs(dx) > 1e-6 and abs(dy) > 1e-6 and abs(abs(dx) - abs(dy)) > 1e-6:
            if abs(dy) > abs(dx):
                xm, ym = x0, y - math.copysign(abs(dx), dy)
            else:
                xm, ym = x - math.copysign(abs(dy), dx), y0
            add_track(x0, y0, xm, ym, net, lay, w)
            add_track(xm, ym, x, y, net, lay, w)
            return
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(mm(OX + x0), mm(OY + y0)))
        t.SetEnd(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        t.SetWidth(mm(w))
        t.SetLayer(lay)
        t.SetNetCode(b.FindNet(net).GetNetCode())
        t.SetLocked(True)
        b.Add(t)
        stubs.append((x0, y0, x, y, net, b.GetLayerName(lay), w))

    def reserve(net, srcs, want, reach, link, w_tr=0.3):
        got = []
        cands = []
        for x0, y0 in srcs:
            for i in range(-60, 61):
                for j in range(-60, 61):
                    if i != 0 and j != 0 and abs(i) != abs(j):
                        continue
                    x, y = x0 + i * 0.04, y0 + j * 0.04
                    d = math.hypot(i * 0.04, j * 0.04)
                    if 0.1 < d <= reach:
                        cands.append((d, x, y, x0, y0))
        cands.sort()
        for d, x, y, x0, y0 in cands:
            if len(got) >= want:
                break
            if any(math.hypot(x - p[0], y - p[1]) < 0.42 for p in got) or not site_ok(x, y, net) or not bpath_ok(x0, y0, x, y, net, w_tr):
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
            v.SetWidth(mm(0.30))
            v.SetDrill(mm(0.15))
            v.SetLayerPair(F_CU, B_CU)
            v.SetNetCode(b.FindNet(net).GetNetCode())
            v.SetLocked(True)
            b.Add(v)
            add_track(x0, y0, x, y, net, B_CU, w_tr)
            vias.append((x, y, net))
            got.append((x, y))
        if link:
            for lay_n in ("In4.Cu", "In6.Cu"):
                for p, q in zip(got, got[1:]):
                    add_track(p[0], p[1], q[0], q[1], net, lid[lay_n], w_tr)
        print(f"  reserve {net}: {len(got)}/{want}")
        return got

    pos = lambda r, n: next((um(p.GetPosition().x) - OX, um(p.GetPosition().y) - OY) for p in fps[r].Pads() if p.GetNumber() == n)
    reserve("+3V3", [pos("U3", "54"), pos("U3", "53")], 1, 1.8, False, 0.2)
    reserve("+3V3", [pos("C4", "1")], 1, 1.8, False, 0.2)
    reserve("+3V3", [pos("C13", "1")], 1, 1.8, False, 0.2)
    reserve("GND", [pos("C4", "2")], 1, 1.8, False, 0.2)
    reserve("GND", [pos("C13", "2")], 1, 1.8, False, 0.2)
    reserve("VSYS", [pos("U5", "11"), pos("U5", "10")], 3, 2.4, False, 0.3)
    reserve("VBAT", [pos("U5", "3"), pos("U5", "2")], 3, 2.4, True, 0.3)
    reserve("VBAT", [pos("BT1", "1")], 3, 2.4, True, 0.3)

    # Reserve VSYS and GND plane vias right beside each BGA's North (VDD) and South (PVCC) decouplers.
    for c_vdd, c_pvcc in (("C33", "C32"), ("C44", "C42"), ("C53", "C52"), ("C63", "C62"), ("C73", "C72")):
        reserve("VSYS", [pos(c_vdd, "1")], 1, 1.8, False, 0.2)
        reserve("GND", [pos(c_vdd, "2")], 1, 1.8, False, 0.2)
        reserve("VSYS", [pos(c_pvcc, "1")], 1, 1.8, False, 0.2)
        reserve("GND", [pos(c_pvcc, "2")], 1, 1.8, False, 0.2)
    reserve("VSYS", [pos("C43", "1")], 1, 1.8, False, 0.2)
    reserve("GND", [pos("C43", "2")], 1, 1.8, False, 0.2)

    # Bridge U3 +1V1 'FB finger' to 'vendor +1V1' on In6.Cu across D235's anode via (fbfix3.py).
    filler.Fill(b.Zones())
    fb_z = next(z for z in b.Zones() if z.GetZoneName() == "FB finger")
    co_z = next(z for z in b.Zones() if z.GetZoneName() == "vendor +1V1")
    fb_ps = fb_z.GetFilledPolysList(B_CU)
    co_ps = co_z.GetFilledPolysList(B_CU)
    s_fb = [
        (x / 100, y / 100)
        for x in range(-70, 5, 4)
        for y in range(-330, -170, 4)
        if fb_ps.Contains(pcbnew.VECTOR2I(mm(OX + x / 100), mm(OY + y / 100))) and site_ok(x / 100, y / 100, "+1V1")
    ]
    s_co = [
        (x / 100, y / 100)
        for x in range(-110, 30, 4)
        for y in range(-150, 150, 4)
        if co_ps.Contains(pcbnew.VECTOR2I(mm(OX + x / 100), mm(OY + y / 100))) and site_ok(x / 100, y / 100, "+1V1")
    ]
    best_fb = None
    for a_pt in s_fb:
        for c_pt in s_co:
            d_fb = math.dist(a_pt, c_pt)
            if d_fb < 0.41 or (best_fb and d_fb >= best_fb[0]):
                continue
            # Check straight In6.Cu path clear of foreign vias
            if all(
                n == "+1V1" or seg_dist(vx, vy, a_pt[0], a_pt[1], c_pt[0], c_pt[1]) >= 0.125 + 0.09 + 0.125
                for vx, vy, n in vias
            ):
                best_fb = (d_fb, a_pt, c_pt)
    assert best_fb, "Failed to find +1V1 FB finger -> vendor +1V1 bridge"
    _, a_pt, c_pt = best_fb
    v11_code = b.FindNet("+1V1").GetNetCode()
    for qx, qy in (a_pt, c_pt):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(OX + qx), mm(OY + qy)))
        v.SetWidth(mm(0.25))
        v.SetDrill(mm(0.15))
        v.SetLayerPair(F_CU, B_CU)
        v.SetNetCode(v11_code)
        v.SetLocked(True)
        b.Add(v)
        vias.append((qx, qy, "+1V1"))
    add_track(a_pt[0], a_pt[1], c_pt[0], c_pt[1], "+1V1", lid["In6.Cu"], 0.25)
    print(f"  bridged +1V1 FB finger {a_pt} -> vendor +1V1 {c_pt} on In6.Cu")

    filler.Fill(b.Zones())
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for l in z.GetLayerSet().Seq():
                if b.GetLayerName(l) in ("In2.Cu", "In5.Cu"):
                    ps = z.GetFilledPolysList(l)
                    print(f"  zone {z.GetZoneName():<12} ({b.GetLayerName(l)}): pieces={ps.OutlineCount()}, area={ps.Area() / 1e12:.1f} mm^2")
    pcbnew.SaveBoard(str(PCB), b)
    print("copper stage 2 saved")


if __name__ == "__main__":
    {"outline": outline, "stack": stack, "sync": sync, "place": place, "copper": copper, "copper2": copper2}[sys.argv[1]]()
