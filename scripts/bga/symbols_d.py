#!/usr/bin/env python3
"""symbols_d.py -- project symbol library for round-pendant Variant D (5x IS31FL3745-CLS4-TR BGA).

Writes hw/round-pendant/$PENDANT_VARIANT/lib/round_pendant.kicad_sym, sym-lib-table, and fp-lib-table.
Pins are arranged by function: inputs/control left, outputs right, power top, ground bottom.
Ball names and numbers verified against datasheets/is31fl3745.pdf p. 3 (Top View).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
from kicad_write import S, Sym, dump  # noqa: E402
from symbols import fet_pair, ic, led, power_sym, rp2350  # noqa: E402

VARIANT = os.environ.get("PENDANT_VARIANT", "d")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
LIB = HW / "lib"

SW_BALLS = [
    ("1", "A2"),
    ("2", "A4"),
    ("3", "A1"),
    ("4", "A5"),
    ("5", "B1"),
    ("6", "A6"),
    ("7", "C1"),
    ("8", "B6"),
]

CS_BALLS = [
    ("1", "B2"),
    ("2", "B3"),
    ("3", "C3"),
    ("4", "C2"),
    ("5", "D2"),
    ("6", "D1"),
    ("7", "E2"),
    ("8", "E1"),
    ("9", "F1"),
    ("10", "F6"),
    ("11", "E6"),
    ("12", "D5"),
    ("13", "D6"),
    ("14", "C4"),
    ("15", "C6"),
    ("16", "C5"),
    ("17", "B4"),
    ("18", "B5"),
]


def is31fl3745():
    """IS31FL3745-CLS4-TR WLCSP-36 18x8 LED matrix driver (datasheets/is31fl3745.pdf p. 3)."""
    all_balls = {"A3", "F5", "F4", "D3", "E3", "E5", "D4", "E4", "F3", "F2"}
    all_balls |= {b for _, b in SW_BALLS} | {b for _, b in CS_BALLS}
    expected = {f"{r}{c}" for r in "ABCDEF" for c in range(1, 7)}
    assert all_balls == expected and len(all_balls) == 36, f"Ball mismatch: {expected ^ all_balls}"

    return ic(
        "IS31FL3745",
        "18 x 8 matrix LED driver, I2C, WLCSP-36 2.9 x 2.9 mm 0.5 mm pitch",
        "round_pendant:WLCSP-36_2.9x2.9mm_P0.5mm",
        left=[
            ("bidirectional", "D3", "SDA"),
            ("input", "E3", "SCL"),
            ("input", "E5", "SDB"),
            None,
            ("input", "D4", "ADDR1"),
            ("input", "E4", "ADDR2"),
            None,
            None,
            ("passive", "F3", "RSET"),
            ("bidirectional", "F2", "SYNC"),
        ],
        right=(
            [("output", b, f"SW{i}") for i, b in SW_BALLS]
            + [None]
            + [("input", b, f"CS{i}") for i, b in CS_BALLS]
        ),
        top=[
            ("power_in", "A3", "PVCC"),
            ("power_in", "F5", "VDD"),
        ],
        bottom=[
            ("power_in", "F4", "GND"),
        ],
        width=25.4,
    )


def main():
    LIB.mkdir(parents=True, exist_ok=True)
    driver = is31fl3745()
    charger = ic(
        "BQ24073",
        "Li-ion charger with power path, VQFN-16 3 x 3 mm",
        "Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
        left=[
            ("power_in", "13", "IN"),
            None,
            ("input", "6", "EN1"),
            ("input", "5", "EN2"),
            ("input", "4", "CE"),
            ("input", "15", "TD"),
            None,
            None,
            ("passive", "1", "TS"),
            ("passive", "16", "ISET"),
            ("passive", "12", "ILIM"),
            ("passive", "14", "TMR"),
        ],
        right=[
            ("power_out", ["10", "11"], "OUT"),
            None,
            ("power_in", ["2", "3"], "BAT"),
            None,
            None,
            None,
            ("open_collector", "7", "~{PGOOD}"),
            ("open_collector", "9", "~{CHG}"),
        ],
        bottom=[("power_in", ["8", "17"], "VSS")],
        width=17.78,
    )
    ldo = ic(
        "TPS7A0233",
        "3.3 V 200 mA LDO, 25 nA Iq, X2SON-4 1 x 1 mm",
        "Package_SON:Texas_X2SON-4_1x1mm_P0.65mm",
        left=[("power_in", "4", "IN"), ("input", "3", "EN")],
        right=[("power_out", "1", "OUT")],
        bottom=[("power_in", ["2", "5"], "GND")],
        width=10.16,
    )
    prot = ic(
        "XB9901A",
        "One-cell protection with FETs, DFN 1.8 x 1.4 mm",
        "round_pendant:XySemi_DFN-6_1.8x1.4mm",
        left=[("passive", "6", "VDD")],
        right=[("passive", ["1", "2", "3"], "VM")],
        bottom=[("passive", ["4", "5"], "GND")],
        width=12.7,
    )
    accel = ic(
        "LIS2DW12",
        "3-axis accelerometer, LGA-12 2 x 2 mm",
        "Package_LGA:LGA-12_2x2mm_P0.5mm",
        left=[
            ("input", "1", "SCL"),
            ("bidirectional", "4", "SDA"),
            None,
            ("input", "2", "CS"),
            ("input", "3", "SA0"),
        ],
        right=[("output", "12", "INT1"), ("output", "11", "INT2")],
        top=[("power_in", "9", "VDD"), ("power_in", "10", "VDD_IO")],
        bottom=[("power_in", ["6", "8", "7"], "GND"), ("no_connect", "5", "NC")],
        width=22.86,
    )
    usb = ic(
        "USB_Pads",
        "Pads for off-board USB-C wires",
        "round_pendant:USB_Pads",
        right=[
            ("passive", "5", "VBUS"),
            ("passive", "3", "D-"),
            ("passive", "4", "D+"),
            ("passive", "1", "CC1"),
            ("passive", "2", "CC2"),
            ("passive", "6", "GND"),
        ],
        width=10.16,
        ref="J",
    )
    lib = [
        Sym("kicad_symbol_lib"),
        S("version", Sym("20241209")),
        S("generator", "round_pendant_symbols_d"),
        S("generator_version", "9.0"),
        usb,
        driver,
        charger,
        ldo,
        prot,
        accel,
        fet_pair(),
        led(),
        rp2350(),
        power_sym("VSYS"),
        power_sym("VBAT"),
    ]
    (LIB / "round_pendant.kicad_sym").write_text(dump(lib) + "\n")
    (HW / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.kicad_sym")(options "")(descr "project symbols"))\n)\n'
    )
    (HW / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.pretty")(options "")(descr "project footprints"))\n)\n'
    )
    print("wrote", LIB)


if __name__ == "__main__":
    main()
