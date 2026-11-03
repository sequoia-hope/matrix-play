#!/usr/bin/env python3
"""symbols.py -- the project symbol library for round-pendant.

    python3 scripts/symbols.py      writes hw/round-pendant/a/lib/round_pendant.kicad_sym and sym-lib-table

Pins are by function: inputs and control left, outputs right, power top, ground bottom
(references/schematic-style.md). RP2350A is the stock symbol respaced, as in easy2350.
Pin numbers and names are from each part's audit in design/parts/.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
from kicad_files import Sym, child, children, head  # noqa: E402
from kicad_write import S, SymbolLib, dump  # noqa: E402

import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
LIB = HW / "lib"
STEP = 2.54


def font():
    return S("effects", S("font", S("size", 1.27, 1.27)))


def pin(kind, num, name, x, y, ang, hide=False, length=2.54):
    p = [Sym("pin"), Sym(kind), Sym("line"), S("at", x, y, ang), S("length", length)]
    if hide:
        p.append(S("hide", Sym("yes")))
    return p + [S("name", name, font()), S("number", num, font())]


def prop(k, v, at, hide=False):
    eff = [Sym("effects"), S("font", S("size", 1.27, 1.27))]
    if hide:
        eff.append(S("hide", Sym("yes")))
    return S("property", k, v, S("at", *at, 0), eff)


def ic(name, desc, fp, left=(), right=(), top=(), bottom=(), width=None, ref="U"):
    """Sides are lists of (kind, number, name) or None for a one-step gap. A number
    may be a list: the extra pins stack, hidden, under the first."""
    rows = max(len(left), len(right), 2)
    half_h = (rows + 1) * STEP / 2
    half_h = round(half_h / STEP) * STEP
    cols = max(len(top), len(bottom), 2)
    half_w = width / 2 if width else max(7.62, (cols + 1) * STEP * 2 / 2)
    half_w = round(half_w / STEP) * STEP
    pins = []

    def add(items, place, ang):
        for i, it in enumerate(items):
            if it is None:
                continue
            kind, num, nm = it
            nums = num if isinstance(num, list) else [num]
            x, y = place(i, len(items))
            pins.append(pin(kind, nums[0], nm, x, y, ang))
            pins.extend(pin("passive", n, nm, x, y, ang, hide=True) for n in nums[1:])

    add(left, lambda i, n: (-half_w - STEP, half_h - STEP * (i + 1)), 0)
    add(right, lambda i, n: (half_w + STEP, half_h - STEP * (i + 1)), 180)
    add(top, lambda i, n: ((i - (n - 1) / 2) * STEP * 2, half_h + STEP), 270)
    add(bottom, lambda i, n: ((i - (n - 1) / 2) * STEP * 2, -half_h - STEP), 90)
    return [Sym("symbol"), name, S("pin_names", S("offset", 0.508)), S("exclude_from_sim", Sym("no")),
            S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
            prop("Reference", ref, (-half_w, half_h + 1.27)), prop("Value", name, (0, -half_h - 1.27)),
            prop("Footprint", fp, (0, 0), True), prop("Datasheet", "", (0, 0), True),
            prop("Description", desc, (0, 0), True),
            [Sym("symbol"), f"{name}_0_1",
             S("rectangle", S("start", -half_w, half_h), S("end", half_w, -half_h),
               S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background"))))],
            [Sym("symbol"), f"{name}_1_1", *pins]]


def led():
    n = "XL-1010RGB"
    return [Sym("symbol"), n, S("pin_names", S("offset", 0.25), Sym("hide")),
            S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
            prop("Reference", "D", (0, 5.08)), prop("Value", n, (0, 0)),
            prop("Footprint", "round_pendant:LED_XL-1010RGB", (0, 0), True), prop("Datasheet", "", (0, 0), True),
            prop("Description", "1 mm common-anode RGB LED", (0, 0), True),
            [Sym("symbol"), f"{n}_0_1",
             S("rectangle", S("start", -3.81, 2.54), S("end", 3.81, -2.54),
               S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background"))))],
            [Sym("symbol"), f"{n}_1_1",
             pin("passive", "3", "A", 0, 5.08, 270, length=2.54),
             pin("passive", "1", "R", -2.54, -5.08, 90, length=2.54),
             pin("passive", "2", "G", 0, -5.08, 90, length=2.54),
             pin("passive", "4", "B", 2.54, -5.08, 90, length=2.54)]]


def fet_pair():
    """NTZD3155C as two units so each half reads on its own. Datasheet p.1: 1 S1, 2 G1, 6 D1 = N; 4 S2, 5 G2, 3 D2 = P."""
    n = "NTZD3155C"
    def box(unit, label, pins):
        return [[Sym("symbol"), f"{n}_{unit}_0",
                 S("rectangle", S("start", -5.08, 5.08), S("end", 5.08, -5.08),
                   S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background")))),
                 S("text", label, S("at", 0, 0, 0), S("effects", S("font", S("size", 1.27, 1.27))))],
                [Sym("symbol"), f"{n}_{unit}_1", *pins]]
    return [Sym("symbol"), n, S("pin_names", S("offset", 0.508)), S("exclude_from_sim", Sym("no")),
            S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
            prop("Reference", "Q", (-5.08, 6.35)), prop("Value", n, (0, -6.35)),
            prop("Footprint", "Package_TO_SOT_SMD:SOT-563", (0, 0), True), prop("Datasheet", "", (0, 0), True),
            prop("Description", "Complementary N + P FET, SOT-563", (0, 0), True),
            *box(1, "N", [pin("passive", "6", "D", 0, 7.62, 270), pin("input", "2", "G", -7.62, 2.54, 0),
                          pin("passive", "1", "S", 0, -7.62, 90)]),
            *box(2, "P", [pin("passive", "4", "S", 0, 7.62, 270), pin("input", "5", "G", -7.62, 2.54, 0),
                          pin("passive", "3", "D", 0, -7.62, 90)])]


def rp2350():
    TOP_X = {"VREG_AVDD": -27.94, "USB_OTP_VDD": -20.32, "ADC_AVDD": -15.24, "QSPI_IOVDD": -10.16,
             "IOVDD": -5.08, "VREG_VIN": 5.08, "VREG_LX": 10.16, "VREG_FB": 15.24, "DVDD": 22.86}
    BOTTOM_X = {"VREG_PGND": -5.08, "GND": 5.08}
    H = 30.48
    sym = SymbolLib().get("MCU_RaspberryPi:RP2350A")
    out = [Sym("symbol"), "RP2350A"]
    for c in sym[2:]:
        if head(c) == "property" and c[1] in ("Reference", "Value"):
            child(c, "at")[1] = H + 1.27
        if head(c) == "symbol":
            for g in c[2:]:
                if head(g) == "rectangle":
                    child(g, "start")[1], child(g, "end")[1] = -H, H
                if head(g) != "pin":
                    continue
                at, nm = child(g, "at"), child(g, "name")[1]
                if nm in TOP_X and float(at[2]) > 0:
                    at[1] = TOP_X[nm]
                elif nm in BOTTOM_X:
                    at[1] = BOTTOM_X[nm]
                elif float(at[1]) < 0:
                    at[1] = -H - 3.81
                else:
                    at[1] = H + 3.81
        out.append(c)
    return out


def power_sym(name):
    """A global power symbol for a rail the stock library lacks: stock +3V3 renamed."""
    sym = SymbolLib().get("power:+3V3")
    out = [Sym("symbol"), name]
    for c in sym[2:]:
        if head(c) == "property" and c[1] == "Value":
            c = [c[0], c[1], name, *c[3:]]
        if head(c) == "symbol":
            c = [c[0], c[1].replace("+3V3", name), *c[2:]]
            for g in c[2:]:
                if head(g) == "pin":
                    child(g, "name")[1] = name
        out.append(c)
    return out


def main():
    LIB.mkdir(parents=True, exist_ok=True)
    gnd = ("power_in", ["12", "36", "55", "61"], "GND")
    driver = ic("IS31FL3741A", "39 x 9 matrix LED driver, I2C, QFN-60 7 x 7 mm", "round_pendant:QFN-60-1EP_7x7mm_P0.4mm_EP5.4x5.4mm",
                left=[("input", "9", "SDA"), ("input", "10", "SCL"), ("open_collector", "7", "INTB"),
                      ("input", "11", "SDB"), None, ("passive", "13", "ISET"), ("input", "8", "ADDR")],
                right=[("output", str(15 + i), f"SW{i}") for i in range(1, 10)] + [None] +
                      [("input", str(n), f"CS{c}") for c, n in zip(range(1, 40),
                       [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
                        50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 1, 2, 3, 4, 5, 6])],
                top=[("power_in", "15", "PVCC"), ("power_in", "25", "PVCC"), ("power_in", "14", "AVCC")],
                bottom=[gnd], width=27.94)
    charger = ic("BQ24073", "Li-ion charger with power path, VQFN-16 3 x 3 mm", "Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
                 left=[("power_in", "13", "IN"), None, ("input", "6", "EN1"), ("input", "5", "EN2"), ("input", "4", "CE"),
                       ("input", "15", "TD"), None, None, ("passive", "1", "TS"), ("passive", "16", "ISET"), ("passive", "12", "ILIM"),
                       ("passive", "14", "TMR")],
                right=[("power_out", ["10", "11"], "OUT"), None, ("power_in", ["2", "3"], "BAT"), None, None, None,
                       ("open_collector", "7", "~{PGOOD}"), ("open_collector", "9", "~{CHG}")],
                bottom=[("power_in", ["8", "17"], "VSS")], width=17.78)
    ldo = ic("TPS7A0233", "3.3 V 200 mA LDO, 25 nA Iq, X2SON-4 1 x 1 mm", "Package_SON:Texas_X2SON-4_1x1mm_P0.65mm",
             left=[("power_in", "4", "IN"), ("input", "3", "EN")], right=[("power_out", "1", "OUT")],
             bottom=[("power_in", ["2", "5"], "GND")], width=10.16)
    prot = ic("XB9901A", "One-cell protection with FETs, DFN 1.8 x 1.4 mm", "round_pendant:XySemi_DFN-6_1.8x1.4mm",
              left=[("passive", "6", "VDD")], right=[("passive", ["1", "2", "3"], "VM")],
              bottom=[("passive", ["4", "5"], "GND")], width=12.7)
    accel = ic("LIS2DW12", "3-axis accelerometer, LGA-12 2 x 2 mm", "Package_LGA:LGA-12_2x2mm_P0.5mm",
               left=[("input", "1", "SCL"), ("bidirectional", "4", "SDA"), None, ("input", "2", "CS"), ("input", "3", "SA0")],
               right=[("output", "12", "INT1"), ("output", "11", "INT2")],
               top=[("power_in", "9", "VDD"), ("power_in", "10", "VDD_IO")],
               bottom=[("power_in", ["6", "8", "7"], "GND"), ("no_connect", "5", "NC")], width=22.86)
    fet = fet_pair()
    usb = ic("USB_Pads", "Pads for off-board USB-C wires", "round_pendant:USB_Pads",
             right=[("passive", "5", "VBUS"), ("passive", "3", "D-"), ("passive", "4", "D+"), ("passive", "1", "CC1"), ("passive", "2", "CC2"), ("passive", "6", "GND")],
             width=10.16, ref="J")
    lib = [Sym("kicad_symbol_lib"), S("version", Sym("20241209")), S("generator", "round_pendant_symbols"),
           S("generator_version", "9.0"), *([usb] if VARIANT != "a" else []), driver, charger, ldo, prot, accel, fet, led(), rp2350(),
           power_sym("VSYS"), power_sym("VBAT")]
    (LIB / "round_pendant.kicad_sym").write_text(dump(lib) + "\n")
    (HW / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.kicad_sym")(options "")(descr "project symbols"))\n)\n')
    (HW / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.pretty")(options "")(descr "project footprints"))\n)\n')
    print("wrote", LIB)


if __name__ == "__main__":
    main()
