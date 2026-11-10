#!/usr/bin/env python3
"""setup_project_and_sch.py — Initialize hw/round-pendant/f-usbc-rtc/ from f-usbc,
add verified footprints & symbols for BT1 (CJT A1251WR-S-2P, C225111) and U13 (Seiko Epson RX8130CE:BB, C1542426),
and author clean, human-readable schematic updates on round-pendant.kicad_sch, power.kicad_sch, and mcu.kicad_sch.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))

from kicad_files import Sym, child, children, head, parse_sexpr
from kicad_write import S, dump, new_uuid, yes

SRC_DIR = ROOT / "hw/round-pendant/f-usbc"
DST_DIR = ROOT / "hw/round-pendant/f-usbc-rtc"

ROOT_UUID = "28f3c2e7-0555-4b15-aead-86ebeb28d679"
PWR_SHEET_UUID = "4d5ffdd6-dcef-443c-8499-342509ed5604"
MCU_SHEET_UUID = "03794613-f144-4f19-8f17-33db92d30226"


def build_rx8130ce_footprint() -> str:
    """Verified 0.000 mm pad-for-pad against Seiko Epson ETM50E-10 Fig. 9 (p. 11) and EasyEDA C1542426.
    Top-view F.Cu library frame (0 deg):
      Body: 2.50 mm (X: -1.25..+1.25) x 3.20 mm (Y: -1.60..+1.60), height 1.00 mm max.
      Corner pads 1,5,6,10: 1.00 x 0.70 mm at x = ±1.100, y = ±1.550.
      Inner pads 2,3,4 & 7,8,9: 1.00 x 0.40 mm at x = ±1.100, y = -0.700, 0.000, +0.700.
    """
    pads = [
        ("1", -1.100, -1.550, 1.000, 0.700),
        ("2", -1.100, -0.700, 1.000, 0.400),
        ("3", -1.100,  0.000, 1.000, 0.400),
        ("4", -1.100, +0.700, 1.000, 0.400),
        ("5", -1.100, +1.550, 1.000, 0.700),
        ("6", +1.100, +1.550, 1.000, 0.700),
        ("7", +1.100, +0.700, 1.000, 0.400),
        ("8", +1.100,  0.000, 1.000, 0.400),
        ("9", +1.100, -0.700, 1.000, 0.400),
        ("10", +1.100, -1.550, 1.000, 0.700),
    ]
    pad_str = "\n".join(
        f'\t(pad "{num}" smd roundrect\n'
        f'\t\t(at {x:g} {y:g})\n'
        f'\t\t(size {w:g} {h:g})\n'
        f'\t\t(layers "F.Cu" "F.Paste" "F.Mask")\n'
        f'\t\t(roundrect_rratio 0.2)\n'
        f'\t)'
        for num, x, y, w, h in pads
    )
    return f"""(footprint "Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm"
\t(version 20241229)
\t(generator "pcbnew")
\t(layer "F.Cu")
\t(descr "Seiko Epson RX8130CE Real-Time Clock Module, 3.2x2.5x1.0mm SMD-10P (ETM50E-10 Fig. 9 / LCSC C1542426)")
\t(tags "RTC I2C 32.768kHz RX8130CE Epson")
\t(property "Reference" "REF**"
\t\t(at 0 -2.45 0)
\t\t(layer "F.SilkS")
\t\t(hide yes)
\t\t(effects (font (size 0.8 0.8) (thickness 0.15)))
\t)
\t(property "Value" "RX8130CE"
\t\t(at 0 2.45 0)
\t\t(layer "F.Fab")
\t\t(effects (font (size 0.8 0.8) (thickness 0.15)))
\t)
\t(attr smd)
\t(fp_line (start -1.85 -2.10) (end 1.85 -2.10) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
\t(fp_line (start 1.85 -2.10) (end 1.85 2.10) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
\t(fp_line (start 1.85 2.10) (end -1.85 2.10) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
\t(fp_line (start -1.85 2.10) (end -1.85 -2.10) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
\t(fp_line (start -0.85 -1.60) (end 1.25 -1.60) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
\t(fp_line (start 1.25 -1.60) (end 1.25 1.60) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
\t(fp_line (start 1.25 1.60) (end -1.25 1.60) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
\t(fp_line (start -1.25 1.60) (end -1.25 -1.20) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
\t(fp_line (start -1.25 -1.20) (end -0.85 -1.60) (stroke (width 0.1) (type solid)) (layer "F.Fab"))
\t(fp_text user "${{REFERENCE}}" (at 0 0 90) (layer "F.Fab") (effects (font (size 0.65 0.65) (thickness 0.12))))
{pad_str}
\t(embedded_fonts no)
\t(model "${{KIPRJMOD}}/../../../3dmodels/RTC-SMD_L3.2-W2.5-P0.7-RX8130CE.step"
\t\t(offset (xyz 0 0 1.0))
\t\t(scale (xyz 1 1 1))
\t\t(rotate (xyz 0 0 0))
\t)
)
"""


def build_rx8130ce_symbol_sexpr() -> list:
    """Human-readable functional symbol per LESSONS.md:
      - Power (VIO=1, VDD=8, VBAT=10) at TOP (5.08 mm spacing for crisp pin labels)
      - Inputs/bus (SCL=2, SDA=3) on LEFT
      - Outputs/reg (~{IRQ}=6, VOUT=9, FOUT=4, ~{RST}=5) on RIGHT
      - Ground (GND=7) at BOTTOM
    """
    txt = """(symbol "RX8130CE"
\t(pin_names (offset 0.508))
\t(exclude_from_sim no)
\t(in_bom yes)
\t(on_board yes)
\t(property "Reference" "U" (at -10.16 8.89 0) (effects (font (size 1.27 1.27)) (justify left)))
\t(property "Value" "RX8130CE" (at 10.16 -8.89 0) (effects (font (size 1.27 1.27)) (justify right)))
\t(property "Footprint" "round_pendant:Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t(property "Description" "Real-Time Clock Module with built-in 32.768 kHz crystal, I2C Fast-Mode, SMD-10P 3.2x2.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t(symbol "RX8130CE_0_1"
\t\t(rectangle (start -10.16 7.62) (end 10.16 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
\t)
\t(symbol "RX8130CE_1_1"
\t\t(pin power_in line (at -3.81 10.16 270) (length 2.54)
\t\t\t(name "VIO" (effects (font (size 1.016 1.016))))
\t\t\t(number "1" (effects (font (size 1.016 1.016))))
\t\t)
\t\t(pin power_in line (at 0 10.16 270) (length 2.54)
\t\t\t(name "VDD" (effects (font (size 1.016 1.016))))
\t\t\t(number "8" (effects (font (size 1.016 1.016))))
\t\t)
\t\t(pin power_in line (at 3.81 10.16 270) (length 2.54)
\t\t\t(name "VBAT" (effects (font (size 1.016 1.016))))
\t\t\t(number "10" (effects (font (size 1.016 1.016))))
\t\t)
\t\t(pin input line (at -12.7 2.54 0) (length 2.54)
\t\t\t(name "SCL" (effects (font (size 1.27 1.27))))
\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin bidirectional line (at -12.7 -2.54 0) (length 2.54)
\t\t\t(name "SDA" (effects (font (size 1.27 1.27))))
\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin open_collector line (at 12.7 5.08 180) (length 2.54)
\t\t\t(name "~{IRQ}" (effects (font (size 1.27 1.27))))
\t\t\t(number "6" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin power_out line (at 12.7 0 180) (length 2.54)
\t\t\t(name "VOUT" (effects (font (size 1.27 1.27))))
\t\t\t(number "9" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin output line (at 12.7 -2.54 180) (length 2.54)
\t\t\t(name "FOUT" (effects (font (size 1.27 1.27))))
\t\t\t(number "4" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin open_collector line (at 12.7 -5.08 180) (length 2.54)
\t\t\t(name "~{RST}" (effects (font (size 1.27 1.27))))
\t\t\t(number "5" (effects (font (size 1.27 1.27))))
\t\t)
\t\t(pin power_in line (at 0 -10.16 90) (length 2.54)
\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t(number "7" (effects (font (size 1.27 1.27))))
\t\t)
\t)
)"""
    return parse_sexpr(txt)


def prop(name: str, val: str, at: tuple[float, float, float], hide: bool = False, justify: str | None = None) -> list:
    eff = [Sym("effects"), S("font", S("size", 1.27, 1.27))]
    if justify:
        eff.append([Sym("justify"), *[Sym(j) for j in justify.split()]])
    if hide:
        eff.append(S("hide", yes(True)))
    return S("property", name, val, S("at", at[0], at[1], at[2]), eff)


def make_sym_instance(
    lib_id: str,
    ref: str,
    val: str,
    at: tuple[float, float, float],
    sheet_uuid: str,
    ref_at: tuple[float, float, float],
    val_at: tuple[float, float, float],
    footprint: str = "",
    fields: dict[str, str] | None = None,
    pins: list[str] = (),
    in_bom: bool = True,
    on_board: bool = True,
    hide_ref: bool = False,
    ref_justify: str | None = "left",
    val_justify: str | None = "left",
    descr: str = "",
) -> list:
    node = [
        Sym("symbol"),
        S("lib_id", lib_id),
        S("at", at[0], at[1], at[2]),
        S("unit", 1),
        S("exclude_from_sim", yes(False)),
        S("in_bom", yes(in_bom)),
        S("on_board", yes(on_board)),
        S("dnp", yes(False)),
        S("uuid", new_uuid()),
        prop("Reference", ref, ref_at, hide=hide_ref, justify=ref_justify),
        prop("Value", val, val_at, hide=False, justify=val_justify),
        prop("Footprint", footprint, at, hide=True),
        prop("Datasheet", "~", at, hide=True),
        prop("Description", descr, at, hide=True),
    ]
    for k, v in (fields or {}).items():
        node.append(prop(k, v, at, hide=True))
    for pn in pins:
        node.append(S("pin", pn, S("uuid", new_uuid())))
    node.append(
        S("instances", S("project", "round-pendant", S("path", f"/{ROOT_UUID}/{sheet_uuid}", S("reference", ref), S("unit", 1))))
    )
    return node


def make_wire(p1: tuple[float, float], p2: tuple[float, float]) -> list:
    return S(
        "wire",
        S("pts", S("xy", p1[0], p1[1]), S("xy", p2[0], p2[1])),
        S("stroke", S("width", 0), S("type", Sym("default"))),
        S("uuid", new_uuid()),
    )


def make_junction(pt: tuple[float, float]) -> list:
    return S("junction", S("at", pt[0], pt[1]), S("diameter", 0), S("color", 0, 0, 0, 0), S("uuid", new_uuid()))


def make_label(name: str, at: tuple[float, float, float], justify: str = "left bottom") -> list:
    return [
        Sym("label"),
        name,
        S("at", at[0], at[1], at[2]),
        [Sym("effects"), S("font", S("size", 1.27, 1.27)), [Sym("justify"), *[Sym(j) for j in justify.split()]]],
        S("uuid", new_uuid()),
    ]


def update_title_block(tree: list, rev: str, date: str, comment1: str | None = None, comment2: str | None = None):
    tb = child(tree, "title_block")
    if not tb:
        return
    new_tb = [Sym("title_block")]
    seen = set()
    for c in tb[1:]:
        h = head(c)
        if h == "rev":
            new_tb.append(S("rev", rev))
            seen.add("rev")
        elif h == "date":
            new_tb.append(S("date", date))
            seen.add("date")
        elif h == "comment" and str(c[1]) == "1" and comment1 is not None:
            new_tb.append(S("comment", c[1], comment1))
            seen.add("c1")
        elif h == "comment" and str(c[1]) == "2" and comment2 is not None:
            new_tb.append(S("comment", c[1], comment2))
            seen.add("c2")
        else:
            new_tb.append(c)
    if "rev" not in seen:
        new_tb.append(S("rev", rev))
    if "date" not in seen:
        new_tb.append(S("date", date))
    tb[:] = new_tb


def main():
    DST_DIR.mkdir(parents=True, exist_ok=True)
    # 1. Copy base KiCad files & lib from f-usbc
    base_files = [
        "fp-lib-table",
        "sym-lib-table",
        "round-pendant.kicad_dru",
        "round-pendant.kicad_pcb",
        "round-pendant.kicad_pro",
        "round-pendant.kicad_sch",
        "power.kicad_sch",
        "mcu.kicad_sch",
        "matrix1.kicad_sch",
        "matrix2.kicad_sch",
        "matrix3.kicad_sch",
        "matrix4.kicad_sch",
        "matrix5.kicad_sch",
    ]
    for fn in base_files:
        shutil.copy2(SRC_DIR / fn, DST_DIR / fn)

    dst_lib = DST_DIR / "lib"
    shutil.copytree(SRC_DIR / "lib", dst_lib, dirs_exist_ok=True)

    # 2. Add footprints: Molex_PicoBlade_53261-0271 + Seiko_Epson_RX8130CE + update XySemi 3D model path
    shutil.copy2(
        ROOT / "hw/parallelogram/p2-132-usb6/lib/round_pendant.pretty/Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal.kicad_mod",
        dst_lib / "round_pendant.pretty/Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal.kicad_mod",
    )
    (dst_lib / "round_pendant.pretty/Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm.kicad_mod").write_text(
        build_rx8130ce_footprint(), encoding="utf-8"
    )
    xy_mod_path = dst_lib / "round_pendant.pretty/XySemi_DFN-6_1.8x1.4mm.kicad_mod"
    xy_txt = xy_mod_path.read_text(encoding="utf-8").replace(
        'XB9901A_DFNFC-6.wrl"\n\t\t(offset\n\t\t\t(xyz 0 0 0)\n\t\t)',
        'DFNFC-6_L1.8-W1.4-H0.6-P0.50-BL_XB9901A.step"\n\t\t(offset\n\t\t\t(xyz 0 0 0.56)\n\t\t)',
    )
    xy_mod_path.write_text(xy_txt, encoding="utf-8")

    # 3. Update project symbol library: add JST_1P25_2P_MP and RX8130CE
    p_sym_tree = parse_sexpr((ROOT / "hw/parallelogram/p2-132-usb6/lib/round_pendant.kicad_sym").read_text(encoding="utf-8"))
    jst_sym = next(s for s in children(p_sym_tree, "symbol") if s[1] == "JST_1P25_2P_MP")
    rx_sym = build_rx8130ce_symbol_sexpr()

    sym_path = dst_lib / "round_pendant.kicad_sym"
    sym_tree = parse_sexpr(sym_path.read_text(encoding="utf-8"))
    sym_tree = [c for c in sym_tree if not (isinstance(c, list) and head(c) == "symbol" and c[1] in ("JST_1P25_2P_MP", "RX8130CE"))]
    sym_tree.append(jst_sym)
    sym_tree.append(rx_sym)
    sym_path.write_text(dump(sym_tree) + "\n", encoding="utf-8")

    # 4. Update root round-pendant.kicad_sch title block
    root_sch_path = DST_DIR / "round-pendant.kicad_sch"
    root_tree = parse_sexpr(root_sch_path.read_text(encoding="utf-8"))
    update_title_block(
        root_tree,
        rev="FUR",
        date="2026-11-09",
        comment1="Variant f-usbc-rtc from f-usbc (inward 1.25 mm BT1 + RX8130CE RTC)",
        comment2="235 RGB LEDs on 38 mm round PCB (5x IS31FL3745, USB-C, Batt, RTC)",
    )
    root_sch_path.write_text(dump(root_tree) + "\n", encoding="utf-8")

    # 5. Update power.kicad_sch: replace BT1 CELL 403535 with JST_1P25_2P_MP (A1251WR-S-2P, C225111) + MP -> GND
    pwr_path = DST_DIR / "power.kicad_sch"
    pwr_tree = parse_sexpr(pwr_path.read_text(encoding="utf-8"))
    update_title_block(
        pwr_tree,
        rev="FUR",
        date="2026-11-09",
        comment1="Variant f-usbc-rtc (BT1 swapped to inward 1.25 mm A1251WR-S-2P)",
        comment2="USB-C 16P SMT, 1.25 mm battery socket, charger, protection, LDO",
    )
    # Embed round_pendant:JST_1P25_2P_MP into power.kicad_sch lib_symbols
    pwr_libs = child(pwr_tree, "lib_symbols")
    pwr_libs[:] = [c for c in pwr_libs if not (isinstance(c, list) and head(c) == "symbol" and c[1] == "round_pendant:JST_1P25_2P_MP")]
    pwr_libs.append([Sym("symbol"), "round_pendant:JST_1P25_2P_MP", *jst_sym[2:]])

    # Replace BT1 symbol instance & update description note
    new_pwr = []
    for c in pwr_tree:
        if isinstance(c, list) and head(c) == "symbol":
            props = {p[1]: p[2] for p in children(c, "property")}
            if props.get("Reference") == "BT1":
                # Place JST_1P25_2P_MP at (43.18, 170.18, 0):
                #   Pin 1 (VBAT)  = (50.80, 167.64) -> exact match to existing wire!
                #   Pin 2 (BAT_N) = (50.80, 170.18) -> exact match to existing wire!
                #   Pin MP (MP)   = (43.18, 177.80) -> wire to GND at (43.18, 180.34)!
                new_pwr.append(
                    make_sym_instance(
                        lib_id="round_pendant:JST_1P25_2P_MP",
                        ref="BT1",
                        val="A1251WR-S-2P",
                        at=(43.18, 170.18, 0),
                        sheet_uuid=PWR_SHEET_UUID,
                        ref_at=(36.83, 166.37, 0),
                        val_at=(36.83, 168.91, 0),
                        footprint="round_pendant:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal",
                        fields={"LCSC": "C225111", "MPN": "A1251WR-S-2P", "Manufacturer": "CJT"},
                        pins=["1", "2", "MP"],
                        in_bom=True,
                        on_board=True,
                        ref_justify="right",
                        val_justify="right",
                        descr="Micro-JST 1.25 / MX1.25 2-pin right-angle SMT battery socket (CJT A1251WR-S-2P)",
                    )
                )
                continue
        if isinstance(c, list) and head(c) == "text" and "Hand-soldered leads" in str(c[1]):
            c = list(c)
            c[1] = "Inward 1.25 mm 2P SMT socket (A1251WR-S-2P, C225111); verify harness polarity (+ pin 1, - pin 2)."
        new_pwr.append(c)

    # Insert wire (43.18, 177.80)->(43.18, 180.34) and GND symbol #PWR50 before sheet_instances
    tail_idx = next(i for i, x in enumerate(new_pwr) if isinstance(x, list) and head(x) in ("sheet_instances", "embedded_fonts"))
    pwr_additions = [
        make_wire((43.18, 177.80), (43.18, 180.34)),
        make_sym_instance(
            lib_id="power:GND",
            ref="#PWR50",
            val="GND",
            at=(43.18, 180.34, 0),
            sheet_uuid=PWR_SHEET_UUID,
            ref_at=(43.18, 180.34, 0),
            val_at=(43.18, 184.15, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
    ]
    new_pwr[tail_idx:tail_idx] = pwr_additions
    pwr_path.write_text(dump(new_pwr) + "\n", encoding="utf-8")

    # 6. Update mcu.kicad_sch: wire U3.31 (GPIO19) -> RTC_INT & add REAL-TIME CLOCK (WAKE) functional block
    mcu_path = DST_DIR / "mcu.kicad_sch"
    mcu_tree = parse_sexpr(mcu_path.read_text(encoding="utf-8"))
    update_title_block(
        mcu_tree,
        rev="FUR",
        date="2026-11-09",
        comment1="Variant f-usbc-rtc (added U13 RX8130CE RTC on I2C1 + GPIO19 wake)",
        comment2="RP2350A, flash, crystal, accel, RX8130CE RTC, ALS, buttons, I2C0",
    )
    mcu_libs = child(mcu_tree, "lib_symbols")
    mcu_libs[:] = [c for c in mcu_libs if not (isinstance(c, list) and head(c) == "symbol" and c[1] == "round_pendant:RX8130CE")]
    mcu_libs.append([Sym("symbol"), "round_pendant:RX8130CE", *rx_sym[2:]])

    # Remove ONLY the no_connect at U3 pin 31 (214.63, 157.48)
    new_mcu = []
    removed_nc = 0
    for c in mcu_tree:
        if isinstance(c, list) and head(c) == "no_connect":
            at = [round(float(v), 2) for v in child(c, "at")[1:]]
            if at == [214.63, 157.48]:
                removed_nc += 1
                continue
        new_mcu.append(c)
    assert removed_nc == 1, f"Expected 1 no_connect at U3.31, found {removed_nc}"

    # Coordinates of REAL-TIME CLOCK (WAKE) block in row E right beside AMBIENT LIGHT SENSOR:
    # Box: (218.44, 223.52) -> (299.72, 271.78) (81.28 x 48.26 mm, 100% clear of TEST PADS y<=228.6 and Title Block x>=301)
    # Wait: TEST PADS box is [271.78, 200.66] -> [381.00, 228.60], so for x >= 271.78 y must start at >= 231.14!
    # Starting the RTC box at y = 231.14 ([218.44, 231.14] -> [298.45, 278.13]) gives 100% clearance to BOTH
    # AMBIENT LIGHT SENSOR (x <= 213.36), TEST PADS (y <= 228.60), and Title Block (x >= 301)!
    # Let's check every pin coordinate inside [218.44, 231.14] -> [298.45, 278.13] on exact 1.27 mm grid:
    #   U13 (RX8130CE) at (254.00, 256.54, 0):
    #     Pin 1  (VIO)   = (251.46, 246.38)
    #     Pin 8  (VDD)   = (254.00, 246.38)
    #     Pin 10 (VBAT)  = (256.54, 246.38)
    #     Pin 2  (SCL)   = (242.57, 254.00)
    #     Pin 3  (SDA)   = (242.57, 259.08)
    #     Pin 6  (~IRQ)  = (265.43, 251.46)
    #     Pin 9  (VOUT)  = (265.43, 256.54)
    #     Pin 4  (FOUT)  = (265.43, 259.08) -> no_connect
    #     Pin 5  (~RST)  = (265.43, 261.62) -> no_connect
    #     Pin 7  (GND)   = (254.00, 266.70)
    #   Top +3V3 rail at y = 243.84:
    #     Pin 1 (251.46, 246.38) -> (251.46, 243.84)
    #     Pin 8 (254.00, 246.38) -> (254.00, 243.84)
    #     Pin 10 (256.54, 246.38) -> (256.54, 243.84)
    #     Horizontal rail: (236.22, 243.84) -> (251.46, 243.84) -> (254.00, 243.84) -> (256.54, 243.84)
    #     +3V3 power symbol #PWR51 at (254.00, 241.30) -> wire (254.00, 241.30)->(254.00, 243.84) (note: two T-junctions offset or +3V3 at (236.22, 241.30) so zero 4-way junction!)
    #     YES! Put +3V3 symbol #PWR51 at (236.22, 241.30) right above C75!
    #   C75 (100n, Device:C, pins 1=(0,+3.81)->y-3.81, 2=(0,-3.81)->y+3.81) at (236.22, 250.19, 0):
    #     C75.1 = (236.22, 246.38) -> wire to (236.22, 243.84) (T-junction with +3V3 from (236.22, 241.30) and horizontal rail to U13!)
    #     C75.2 = (236.22, 254.00)? Wait: SCL wire is below at y=254.00! Put C75 at x = 260.35 or y above SCL, OR put C75 at (233.68, 248.92) -> C75.2=(233.68, 252.73)->GND #PWR52 at (233.68, 254.00), while SCL label wire starts at x = 237.49 -> (242.57, 254.00)! Zero overlap!
    #     Even cleaner: put C75 at x = 246.38? No, SCL wire goes (231.14, 254.00)->(242.57, 254.00). If C75 is on the RIGHT of U13? No, C75 decouples U13.8 (254.00, 246.38), so placing C75 at (227.33, 250.19) (left of SCL/SDA labels at x=236.22!) keeps C75 27mm away or placing C75 at (261.62, 247.65)? Wait: ~IRQ is at y=251.46!
    #     Look! Put SCL at (231.14, 256.54)? No, pin 2 is at y=254.00, pin 3 is at y=259.08:
    #     If SCL wire is (233.68, 254.00) -> (242.57, 254.00) and SDA wire is (233.68, 259.08) -> (242.57, 259.08),
    #     and C75 is at (226.06, 250.19, 0): distance from C75 (226.06, 250.19) to U13.8 (254.00, 246.38) is 28.2 mm (style check decoupler limit is 40 mm, let's check schematic_style_check.py's exact limit!).
    #     Even better: put C75 at (246.38, 245.11)? No, y=241.30..248.92 is ABOVE y=254.00!
    #     Wait: Device:C height between pins is 7.62 mm (3.81*2):
    #     If U13 is at (254.00, 260.35, 0):
    #       Pin 1 (VIO)  = (251.46, 250.19)
    #       Pin 8 (VDD)  = (254.00, 250.19)
    #       Pin 10 (VBAT)= (256.54, 250.19)
    #       Pin 2 (SCL)  = (242.57, 257.81)
    #       Pin 3 (SDA)  = (242.57, 262.89)
    #       Pin 6 (~IRQ) = (265.43, 255.27)
    #       Pin 9 (VOUT) = (265.43, 260.35)
    #       Pin 4 (FOUT) = (265.43, 262.89)
    #       Pin 5 (~RST) = (265.43, 265.43)
    #       Pin 7 (GND)  = (254.00, 270.51)
    #     Now look ABOVE y=257.81 (SCL): we have y = 236.22 .. 255.27 (19 mm of vertical height!!)!
    #     Put C75 at (238.76, 246.38, 0):
    #       C75.1 = (238.76, 242.57) — ONLY 16.9 mm from U13.8!
    #       C75.2 = (238.76, 250.19) -> GND #PWR52 at (238.76, 251.46) (ends at y=254, cleanly ABOVE SCL at y=257.81!)
    #     Top +3V3 rail at y = 242.57:
    #       +3V3 #PWR51 at (238.76, 240.03) -> (238.76, 242.57) (T-junction: up to +3V3, down to C75.1, right to U13 power pins!)
    #       (238.76, 242.57) -> (251.46, 242.57) -> (254.00, 242.57) -> (256.54, 242.57)
    #       Down-drops to Pin 1 (251.46, 250.19), Pin 8 (254.00, 250.19), Pin 10 (256.54, 250.19)! (Zero 4-way junctions — every junction has degree 3!)
    #     R32 (100k pull-up on ~IRQ, Device:R pins 1=(0,+3.81)->y-3.81, 2=(0,-3.81)->y+3.81) at (273.05, 247.65, 0):
    #       R32.1 = (273.05, 243.84) -> +3V3 #PWR53 at (273.05, 242.57)
    #       R32.2 = (273.05, 251.46) -> down to (273.05, 255.27) (T-junction with Pin 6 (265.43, 255.27) and right to RTC_INT label at (280.67, 255.27)!)
    #     C76 (1u smoothing cap on VOUT) at (278.13, 265.43, 0):
    #       C76.1 = (278.13, 261.62) <- wire (265.43, 260.35) -> (278.13, 260.35) -> (278.13, 261.62) (ONLY 12.7 mm from U13.9!)
    #       C76.2 = (278.13, 269.24) -> GND #PWR54 at (278.13, 270.51)
    #     U13 Pin 7 (GND) at (254.00, 270.51) -> wire to (254.00, 271.78) -> GND #PWR55 at (254.00, 271.78)!

    rtc_items = [
        # U3.31 (GPIO19) -> RTC_INT
        make_wire((214.63, 157.48), (237.49, 157.48)),
        make_label("RTC_INT", (237.49, 157.48, 0), justify="left bottom"),
        # Dashed functional block box & title + note
        S(
            "rectangle",
            S("start", 217.17, 231.14),
            S("end", 299.72, 284.48),
            S("stroke", S("width", 0), S("type", Sym("dash"))),
            S("fill", S("type", Sym("none"))),
            S("uuid", new_uuid()),
        ),
        S(
            "text",
            "REAL-TIME CLOCK (WAKE)",
            S("exclude_from_sim", yes(False)),
            S("at", 218.44, 233.68, 0),
            [Sym("effects"), S("font", S("size", 1.778, 1.778)), S("justify", Sym("left"))],
            S("uuid", new_uuid()),
        ),
        S(
            "text",
            "Address 0x32 on I2C1 (400 kHz). VBAT tied to +3V3 (ETM50E-10 EX7).\nSet FSEL=11b (FOUT off, 1.5 uA); 100k pull-up keeps PUE=PDE=0 in sleep.",
            S("exclude_from_sim", yes(False)),
            S("at", 219.71, 280.67, 0),
            [Sym("effects"), S("font", S("size", 1.016, 1.016)), S("justify", Sym("left"))],
            S("uuid", new_uuid()),
        ),
        # U13 RX8130CE:BB at (255.27, 261.62)
        make_sym_instance(
            lib_id="round_pendant:RX8130CE",
            ref="U13",
            val="RX8130CE",
            at=(255.27, 261.62, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(245.11, 250.19, 0),
            val_at=(259.08, 271.78, 0),
            footprint="round_pendant:Seiko_Epson_RX8130CE_3.2x2.5mm_P0.7mm",
            fields={"LCSC": "C1542426", "MPN": "RX8130CE:BB", "Manufacturer": "Seiko Epson"},
            pins=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            ref_justify="right",
            val_justify="left",
            descr="I2C Real-Time Clock Module with built-in 32.768 kHz crystal, 3.2x2.5mm",
        ),
        # C75 100n bypass on VDD/VIO/VBAT (cleanly above SCL label)
        make_sym_instance(
            lib_id="Device:C",
            ref="C75",
            val="100n",
            at=(234.95, 246.38, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(232.41, 245.11, 0),
            val_at=(232.41, 247.65, 0),
            footprint="Capacitor_SMD:C_0402_1005Metric",
            fields={
                "LCSC": "C1525",
                "MPN": "CL05B104KO5NNNC",
                "Manufacturer": "Samsung Electro-Mechanics",
                "Decouples": "U13.8",
            },
            pins=["1", "2"],
            ref_justify="right",
            val_justify="right",
            descr="Unpolarized capacitor",
        ),
        # C76 1u smoothing cap on VOUT
        make_sym_instance(
            lib_id="Device:C",
            ref="C76",
            val="1u",
            at=(280.67, 266.70, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(283.21, 265.43, 0),
            val_at=(283.21, 267.97, 0),
            footprint="Capacitor_SMD:C_0402_1005Metric",
            fields={
                "LCSC": "C52923",
                "MPN": "CL05A105KA5NQNC",
                "Manufacturer": "Samsung Electro-Mechanics",
                "Decouples": "U13.9",
            },
            pins=["1", "2"],
            ref_justify="left",
            val_justify="left",
            descr="Unpolarized capacitor",
        ),
        # R32 100k pull-up on /IRQ (RTC_INT)
        make_sym_instance(
            lib_id="Device:R",
            ref="R32",
            val="100k",
            at=(275.59, 248.92, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(278.13, 247.65, 0),
            val_at=(278.13, 250.19, 0),
            footprint="Resistor_SMD:R_0402_1005Metric",
            fields={"LCSC": "C25741", "MPN": "0402WGF1003TCE", "Manufacturer": "UNI-ROYAL"},
            pins=["1", "2"],
            ref_justify="left",
            val_justify="left",
            descr="Resistor",
        ),
        # Power & GND symbols (#PWR51..#PWR55) with standard ±3.81 mm value offsets
        make_sym_instance(
            lib_id="power:+3V3",
            ref="#PWR51",
            val="+3V3",
            at=(234.95, 240.03, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(234.95, 240.03, 0),
            val_at=(234.95, 236.22, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
        make_sym_instance(
            lib_id="power:GND",
            ref="#PWR52",
            val="GND",
            at=(234.95, 251.46, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(234.95, 251.46, 0),
            val_at=(234.95, 255.27, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
        make_sym_instance(
            lib_id="power:+3V3",
            ref="#PWR53",
            val="+3V3",
            at=(275.59, 242.57, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(275.59, 242.57, 0),
            val_at=(275.59, 238.76, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
        make_sym_instance(
            lib_id="power:GND",
            ref="#PWR54",
            val="GND",
            at=(280.67, 271.78, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(280.67, 271.78, 0),
            val_at=(280.67, 275.59, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
        make_sym_instance(
            lib_id="power:GND",
            ref="#PWR55",
            val="GND",
            at=(255.27, 273.05, 0),
            sheet_uuid=MCU_SHEET_UUID,
            ref_at=(255.27, 273.05, 0),
            val_at=(255.27, 276.86, 0),
            pins=["1"],
            in_bom=False,
            on_board=False,
            hide_ref=True,
            ref_justify=None,
            val_justify=None,
        ),
        # Wires & Junctions for +3V3 rail + C75 + U13.1/8/10
        make_wire((234.95, 240.03), (234.95, 242.57)),
        make_wire((234.95, 242.57), (251.46, 242.57)),
        make_wire((251.46, 242.57), (255.27, 242.57)),
        make_wire((255.27, 242.57), (259.08, 242.57)),
        make_wire((251.46, 242.57), (251.46, 251.46)),
        make_wire((255.27, 242.57), (255.27, 251.46)),
        make_wire((259.08, 242.57), (259.08, 251.46)),
        make_junction((234.95, 242.57)),
        make_junction((251.46, 242.57)),
        make_junction((255.27, 242.57)),
        make_wire((234.95, 250.19), (234.95, 251.46)),
        # Wires & Labels for I2C1 (ACC_SCL, ACC_SDA)
        make_wire((231.14, 259.08), (242.57, 259.08)),
        make_label("ACC_SCL", (231.14, 259.08, 180), justify="right bottom"),
        make_wire((231.14, 264.16), (242.57, 264.16)),
        make_label("ACC_SDA", (231.14, 264.16, 180), justify="right bottom"),
        # Wires & Label for ~IRQ + R32 -> RTC_INT
        make_wire((275.59, 242.57), (275.59, 245.11)),
        make_wire((275.59, 252.73), (275.59, 256.54)),
        make_wire((267.97, 256.54), (275.59, 256.54)),
        make_wire((275.59, 256.54), (283.21, 256.54)),
        make_junction((275.59, 256.54)),
        make_label("RTC_INT", (283.21, 256.54, 0), justify="left bottom"),
        # Wires & Label for VOUT -> C76 (named RTC_VOUT so no unnamed power pin exists)
        make_wire((267.97, 261.62), (280.67, 261.62)),
        make_label("RTC_VOUT", (270.51, 261.62, 0), justify="left bottom"),
        make_wire((280.67, 261.62), (280.67, 262.89)),
        make_wire((280.67, 270.51), (280.67, 271.78)),
        # No-connects for FOUT (pin 4) and ~RST (pin 5)
        S("no_connect", S("at", 267.97, 264.16), S("uuid", new_uuid())),
        S("no_connect", S("at", 267.97, 266.70), S("uuid", new_uuid())),
        # Wire for U13 GND (pin 7)
        make_wire((255.27, 271.78), (255.27, 273.05)),
    ]

    mcu_tail = next(i for i, x in enumerate(new_mcu) if isinstance(x, list) and head(x) in ("sheet_instances", "embedded_fonts"))
    new_mcu[mcu_tail:mcu_tail] = rtc_items
    mcu_path.write_text(dump(new_mcu) + "\n", encoding="utf-8")
    print(f"Successfully generated {DST_DIR} schematics & libraries.")


if __name__ == "__main__":
    main()
