#!/usr/bin/env python3
"""lib_gen.py -- generate symbol and footprint libraries for hw/sunflower/<variant>/lib/.

Includes:
  - AW20198QNR symbol & QFN-40 5x5 mm P0.4 mm EP3.4x3.4 mm solid thermal pad footprint (aw20198qnr.pdf pp. 2-3, 37-38)
  - SW_Panasonic_EVQP7J peg-less side tactile switch footprint (evqp7j01p.pdf p. 2)
  - RP2350A solid EP, SENSOR_ALS-PT19, LED_XL-1010RGB, USB_Pads, BatteryPads, WSON-8 NoEPCopper, XySemi_DFN-6
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/bga"))
sys.path.insert(0, str(ROOT / "scripts/sunflower"))

from kicad_write import S, Sym, dump  # noqa: E402
from symbols import fet_pair, ic, led as sym_led, pin, power_sym, prop, rp2350  # noqa: E402
from footprints import VENDOR, XB, battery, led as fp_led, line, rect, strip_pads, text, usb_pads  # noqa: E402
from footprints_d import als_pt19, rp2350_solid_ep  # noqa: E402
from config import VARIANTS  # noqa: E402

# Verified against datasheets/aw20198qnr.pdf p. 2 Fig. 2 (Top View) & p. 3 Pin Description:
AW20198_SW_PINS = [
    ("1", "6"),
    ("2", "4"),
    ("3", "7"),
    ("4", "3"),
    ("5", "8"),
    ("6", "2"),
    ("7", "9"),
    ("8", "1"),
    ("9", "10"),
    ("10", "40"),
    ("11", "11"),
]

AW20198_CS_PINS = [
    ("1", "39"),
    ("2", "38"),
    ("3", "37"),
    ("4", "36"),
    ("5", "35"),
    ("6", "34"),
    ("7", "33"),
    ("8", "32"),
    ("9", "31"),
    ("10", "21"),
    ("11", "20"),
    ("12", "19"),
    ("13", "18"),
    ("14", "17"),
    ("15", "15"),
    ("16", "14"),
    ("17", "13"),
    ("18", "12"),
]


def aw20198_sym():
    """AW20198QNR QFN-40 5x5 mm 18 CS x 11 SW matrix LED driver symbol."""
    fixed_pins = {"5", "22", "16", "23", "41", "24", "25", "26", "27", "28", "29", "30"}
    all_pins = fixed_pins | {p for _, p in AW20198_SW_PINS} | {p for _, p in AW20198_CS_PINS}
    expected = {str(i) for i in range(1, 42)}
    assert all_pins == expected, f"AW20198 pin mismatch: {expected ^ all_pins}"

    return ic(
        "AW20198QNR",
        "18 CS x 11 SW matrix LED driver, I2C, QFN-40 5 x 5 mm 0.4 mm pitch",
        "round_pendant:AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm",
        left=[
            ("bidirectional", "28", "SDA"),
            ("input", "27", "SCL"),
            ("input", "26", "EN"),
            None,
            ("input", "25", "AD0"),
            ("input", "24", "AD1"),
            None,
            None,
            ("passive", "29", "ISET"),
            ("bidirectional", "30", "SYNC"),
        ],
        right=(
            [("output", p, f"SW{i}") for i, p in AW20198_SW_PINS]
            + [None]
            + [("input", p, f"CS{i}") for i, p in AW20198_CS_PINS]
        ),
        top=[
            ("power_in", "5", "PVCC"),
            ("power_in", "22", "VCC"),
        ],
        bottom=[
            ("power_in", ["23", "16", "41"], "GND"),
        ],
        width=25.4,
    )


def aw20198_fp() -> str:
    """AW20198QNR QFN-40 5x5 mm P0.4 mm EP 3.4x3.4 mm solid thermal pad (aw20198qnr.pdf pp. 37-38).
    40 peripheral lands: 0.60 x 0.20 mm (W/E) or 0.20 x 0.60 mm (N/S), centered at +-2.30 mm (inner +-2.00, outer +-2.60).
    Pin 41 thermal pad: solid 3.40 x 3.40 mm SMD copper + 4x 1.10 x 1.10 mm paste stencil windows at (+-0.95, +-0.95).
    """
    pads = []
    # Pins 1..10: West edge (x = -2.30, y = -1.80 .. +1.80)
    for k in range(10):
        y = round(-1.80 + 0.40 * k, 4)
        pads.append(
            f'\t(pad "{k + 1}" smd roundrect (at -2.3 {y:g}) (size 0.6 0.2)'
            ' (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))\n'
        )
    # Pins 11..20: South edge (y = +2.30, x = -1.80 .. +1.80)
    for k in range(10):
        x = round(-1.80 + 0.40 * k, 4)
        pads.append(
            f'\t(pad "{k + 11}" smd roundrect (at {x:g} 2.3) (size 0.2 0.6)'
            ' (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))\n'
        )
    # Pins 21..30: East edge (x = +2.30, y = +1.80 .. -1.80)
    for k in range(10):
        y = round(1.80 - 0.40 * k, 4)
        pads.append(
            f'\t(pad "{k + 21}" smd roundrect (at 2.3 {y:g}) (size 0.6 0.2)'
            ' (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))\n'
        )
    # Pins 31..40: North edge (y = -2.30, x = +1.80 .. -1.80)
    for k in range(10):
        x = round(1.80 - 0.40 * k, 4)
        pads.append(
            f'\t(pad "{k + 31}" smd roundrect (at {x:g} -2.3) (size 0.2 0.6)'
            ' (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))\n'
        )
    # Pin 41: solid 3.40 x 3.40 mm GND exposed pad + 2x2 paste stencil apertures
    pads.append(
        '\t(pad "41" smd roundrect (at 0 0) (size 3.4 3.4) (layers "F.Cu" "F.Mask")'
        ' (roundrect_rratio 0.045) (zone_connect 2))\n'
    )
    for px in (-0.95, 0.95):
        for py in (-0.95, 0.95):
            pads.append(f'\t(pad "" smd rect (at {px} {py}) (size 1.1 1.1) (layers "F.Paste"))\n')

    # 5.00 x 5.00 mm body on F.Fab with 0.45 mm pin-1 chamfer
    h = 2.50
    ch = 0.45
    fab_pts = [(-h + ch, -h), (h, -h), (h, h), (-h, h), (-h, -h + ch), (-h + ch, -h)]
    fab = "".join(line(a, b, "F.Fab", 0.05) for a, b in zip(fab_pts, fab_pts[1:]))
    # Silkscreen corner ticks outside pads (at +-2.55 mm) + pin-1 tick
    silk = (
        line((-2.55, -2.55), (-2.15, -2.55), "F.SilkS", 0.12)
        + line((-2.55, -2.55), (-2.55, -2.15), "F.SilkS", 0.12)
        + line((2.15, -2.55), (2.55, -2.55), "F.SilkS", 0.12)
        + line((2.55, -2.55), (2.55, -2.15), "F.SilkS", 0.12)
        + line((2.15, 2.55), (2.55, 2.55), "F.SilkS", 0.12)
        + line((2.55, 2.15), (2.55, 2.55), "F.SilkS", 0.12)
        + line((-2.55, 2.15), (-2.55, 2.55), "F.SilkS", 0.12)
        + line((-2.55, 2.55), (-2.15, 2.55), "F.SilkS", 0.12)
    )
    crtyd = rect(2.80, "F.CrtYd", 0.05)
    model = (
        '\t(model "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-40-1EP_5x5mm_P0.4mm_EP3.5x3.5mm.step"\n'
        "\t\t(offset (xyz 0 0 0))\n"
        "\t\t(scale (xyz 1 1 1))\n"
        "\t\t(rotate (xyz 0 0 0))\n"
        "\t)\n"
    )
    return (
        '(footprint "AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm"\n'
        '\t(version 20241229)\n'
        '\t(generator "sunflower_lib")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "Shanghai Awinic AW20198QNR QFN-40 5x5x0.75mm, P0.4mm, solid 3.4x3.4mm EP; aw20198qnr.pdf pp.37-38")\n'
        '\t(attr smd)\n'
        + text("Reference", "REF**", -3.2, "F.SilkS")
        + text("Value", "AW20198QNR", 3.2, "F.Fab", True)
        + fab
        + silk
        + crtyd
        + "".join(pads)
        + model
        + ")\n"
    )


def evqp7j_fp() -> str:
    """Panasonic EVQP7J01P side-push tactile switch WITHOUT boss pegs (evqp7j01p.pdf p. 2 No. 1).
    Knob at +y (tip 2.1 mm from centre); Pad 1 away from knob, Pad 2 by knob; ZERO NPTH holes.
    """
    pads = "".join(
        f'\t(pad "{n}" smd rect (at {x} {y}) (size 1.4 1.05) (layers "F.Cu" "F.Mask" "F.Paste"))\n'
        for n, x, y in (("1", -1.8, -0.725), ("1", 1.8, -0.725), ("2", -1.8, 0.725), ("2", 1.8, 0.725))
    )
    c = ((-2.6, -1.55), (2.6, -1.55), (2.6, 1.55), (0.95, 1.55), (0.95, 2.2), (-0.95, 2.2), (-0.95, 1.55), (-2.6, 1.55), (-2.6, -1.55))
    fab_c = ((-1.75, -1.45), (1.75, -1.45), (1.75, 1.45), (0.85, 1.45), (0.85, 2.1), (-0.85, 2.1), (-0.85, 1.45), (-1.75, 1.45), (-1.75, -1.45))
    return (
        '(footprint "SW_Panasonic_EVQP7J"\n'
        '\t(version 20241229)\n'
        '\t(generator "sunflower_lib")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "Panasonic EVQP7J01P side-push without boss pegs; evqp7j01p.pdf p.2. Knob at +y")\n'
        '\t(attr smd)\n'
        + text("Reference", "REF**", -2.2, "F.SilkS")
        + text("Value", "EVQP7J01P", 2.8, "F.Fab", True)
        + "".join(line(a, b, "F.Fab", 0.05) for a, b in zip(fab_c, fab_c[1:]))
        + "".join(line(a, b, "F.CrtYd", 0.05) for a, b in zip(c, c[1:]))
        + pads
        + ")\n"
    )


def sym_led_xl1615():
    """XINGLIGHT XL-1615RGBC-RF (C965840), 1.6 x 1.5 mm common-anode RGB LED (xl-1615rgbc-rf.pdf p. 8).
    Pin 1 = R cathode, Pin 2 = Common Anode (+), Pin 3 = G cathode, Pin 4 = B cathode.
    """
    n = "XL-1615RGBC"
    return [
        Sym("symbol"), n, S("pin_names", S("offset", 0.25), Sym("hide")),
        S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")), S("on_board", Sym("yes")),
        prop("Reference", "D", (0, 5.08)), prop("Value", n, (0, 0)),
        prop("Footprint", "round_pendant:LED_XL-1615RGBC", (0, 0), True),
        prop("Datasheet", "", (0, 0), True),
        prop("Description", "1.6 x 1.5 mm common-anode RGB LED, Pin 2 anode", (0, 0), True),
        [
            Sym("symbol"), f"{n}_0_1",
            S(
                "rectangle", S("start", -3.81, 2.54), S("end", 3.81, -2.54),
                S("stroke", S("width", 0.254), S("type", Sym("default"))),
                S("fill", S("type", Sym("background"))),
            ),
        ],
        [
            Sym("symbol"), f"{n}_1_1",
            pin("passive", "2", "A", 0, 5.08, 270, length=2.54),
            pin("passive", "1", "R", -2.54, -5.08, 90, length=2.54),
            pin("passive", "3", "G", 0, -5.08, 90, length=2.54),
            pin("passive", "4", "B", 2.54, -5.08, 90, length=2.54),
        ],
    ]


def fp_led_xl1615() -> str:
    """XINGLIGHT XL-1615RGBC-RF (C965840) 1.60 x 1.50 mm RGB LED (xl-1615rgbc-rf.pdf p. 8 Recommended Soldering Pattern).
    Top View (F.Cu, KiCad y-down):
      Pad 1 (R-): (-0.625, -0.475), 0.45 x 0.65 mm
      Pad 2 (A+): (-0.625, +0.475), 0.45 x 0.65 mm
      Pad 3 (G-): (+0.625, -0.475), 0.45 x 0.65 mm
      Pad 4 (B-): (+0.625, +0.475), 0.45 x 0.65 mm
    Inner X gap = 0.80 mm (1.25 mm center pitch); inner Y gap = 0.30 mm (0.95 mm center pitch).
    """
    pads = "".join(
        f'\t(pad "{n}" smd rect (at {x:g} {y:g}) (size 0.45 0.65) (layers "F.Cu" "F.Mask" "F.Paste"))\n'
        for n, x, y in (
            ("1", -0.625, -0.475),
            ("2", -0.625, 0.475),
            ("3", 0.625, -0.475),
            ("4", 0.625, 0.475),
        )
    )
    fab_c = [(-0.80, -0.75), (0.80, -0.75), (0.80, 0.75), (-0.80, 0.75), (-0.80, -0.75)]
    crtyd_c = [(-1.00, -0.95), (1.00, -0.95), (1.00, 0.95), (-1.00, 0.95), (-1.00, -0.95)]
    # Pin-1 bevel at top-left (-0.80, -0.75) + left-side triangle mark pointing toward (-X) between Pad 1 & Pad 2 (p. 8)
    fab = (
        "".join(line(a, b, "F.Fab", 0.05) for a, b in zip(fab_c, fab_c[1:]))
        + line((-0.80, -0.50), (-0.55, -0.75), "F.Fab", 0.05)
        + line((-0.72, 0.0), (-0.56, -0.10), "F.Fab", 0.05)
        + line((-0.56, -0.10), (-0.56, 0.10), "F.Fab", 0.05)
        + line((-0.56, 0.10), (-0.72, 0.0), "F.Fab", 0.05)
    )
    crtyd = "".join(line(a, b, "F.CrtYd", 0.05) for a, b in zip(crtyd_c, crtyd_c[1:]))
    model = (
        '\t(model "${KIPRJMOD}/../../../3dmodels/LED-ARRAY-SMD_4P-L1.6-W1.5-BR_XL-1615RGBC-RF.step"\n'
        "\t\t(offset (xyz 0 0 0))\n"
        "\t\t(scale (xyz 1 1 1))\n"
        "\t\t(rotate (xyz 0 0 180))\n"
        "\t)\n"
    )
    return (
        '(footprint "LED_XL-1615RGBC"\n'
        '\t(version 20241229)\n'
        '\t(generator "sunflower_lib")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "XINGLIGHT XL-1615RGBC-RF (C965840), 1.6 x 1.5 x 0.6 mm RGB, common anode pad 2; xl-1615rgbc-rf.pdf p.8")\n'
        '\t(attr smd)\n'
        + text("Reference", "REF**", -1.25, "F.Fab", True)
        + text("Value", "XL-1615RGBC", 1.25, "F.Fab", True)
        + fab
        + crtyd
        + pads
        + model
        + ")\n"
    )


def generate_libs(variant_name: str):
    spec = VARIANTS[variant_name]
    hw = spec.hw_dir
    lib_dir = hw / "lib"
    pretty = lib_dir / "round_pendant.pretty"
    pretty.mkdir(parents=True, exist_ok=True)

    # 1. Symbol library
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
    usb_c = ic(
        "USB_C_16P",
        "USB-C receptacle, USB 2.0, 16 pins (HRO TYPE-C-31-M-12)",
        "round_pendant:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        right=[
            ("passive", ["A4", "A9", "B4", "B9"], "VBUS"),
            ("passive", ["A7", "B7"], "D-"),
            ("passive", ["A6", "B6"], "D+"),
            ("passive", "A5", "CC1"),
            ("passive", "B5", "CC2"),
            ("passive", ["A1", "A12", "B1", "B12"], "GND"),
            ("passive", "S1", "SHIELD"),
            ("passive", "A8", "SBU1"),
            ("passive", "B8", "SBU2"),
        ],
        width=10.16,
        ref="J",
    )
    als = ic(
        "ALS-PT19",
        "Ambient light sensor phototransistor, 1.6 x 0.8 mm SMD",
        "round_pendant:SENSOR_ALS-PT19",
        left=[("passive", "1", "C")],
        right=[("passive", "2", "E")],
        width=10.16,
        ref="Q",
    )
    sym_lib = [
        Sym("kicad_symbol_lib"),
        S("version", Sym("20241209")),
        S("generator", "sunflower_symbols"),
        S("generator_version", "9.0"),
        usb,
        usb_c,
        als,
        aw20198_sym(),
        charger,
        ldo,
        prot,
        accel,
        fet_pair(),
        sym_led(),
        sym_led_xl1615(),
        rp2350(),
        power_sym("VSYS"),
        power_sym("VBAT"),
    ]
    (lib_dir / "round_pendant.kicad_sym").write_text(dump(sym_lib) + "\n")
    (hw / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.kicad_sym")(options "")(descr "project symbols"))\n)\n'
    )
    (hw / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n  (lib (name "round_pendant")(type "KiCad")'
        '(uri "${KIPRJMOD}/lib/round_pendant.pretty")(options "")(descr "project footprints"))\n)\n'
    )

    # 2. Footprint library
    (pretty / "AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm.kicad_mod").write_text(aw20198_fp())
    (pretty / "SW_Panasonic_EVQP7J.kicad_mod").write_text(evqp7j_fp())
    (pretty / "SENSOR_ALS-PT19.kicad_mod").write_text(als_pt19())
    (pretty / "USB_Pads.kicad_mod").write_text(usb_pads())
    (pretty / "LED_XL-1010RGB.kicad_mod").write_text(fp_led())
    (pretty / "LED_XL-1615RGBC.kicad_mod").write_text(fp_led_xl1615())
    (pretty / "BatteryPads.kicad_mod").write_text(battery())
    # Battery connector (config.BAT_FP): KiCad's own footprint, copied in; its 3D model stays in KiCad's library
    from config import BAT_FP, BAT_LIB_SRC
    bat_name = BAT_FP.split(":")[1]
    shutil.copy(f"{BAT_LIB_SRC}/{bat_name}.kicad_mod", pretty / f"{bat_name}.kicad_mod")
    if VARIANTS[variant_name].usb_c:
        from config import USB_FP, USB_LIB_SRC
        usb_name = USB_FP.split(":")[1]
        shutil.copy(f"{USB_LIB_SRC}/{usb_name}.kicad_mod", pretty / f"{usb_name}.kicad_mod")
    if VARIANTS[variant_name].test_pads:
        # KiCad's 1.0 mm test pad with its courtyard cut from r = 1.0 to r = 0.75 mm (pad edge + 0.25 mm)
        tp = Path("/usr/share/kicad/footprints/TestPoint.pretty/TestPoint_Pad_D1.0mm.kicad_mod").read_text()
        tp = tp.replace('(footprint "TestPoint_Pad_D1.0mm"', '(footprint "TestPoint_Pad_D1.0mm_CrtYd0.75"', 1)
        i = tp.rfind("(fp_circle", 0, tp.index('(layer "F.CrtYd")'))
        circ = tp[i:tp.index('(layer "F.CrtYd")', i)]
        assert "(end 1 0)" in circ, "unexpected TestPoint courtyard"
        tp = tp[:i] + circ.replace("(end 1 0)", "(end 0.75 0)") + tp[i + len(circ):]
        (pretty / "TestPoint_Pad_D1.0mm_CrtYd0.75.kicad_mod").write_text(tp)
    for name in ("L_pol_2016", "C_0402_1005Metric_small_pads"):
        shutil.copy(VENDOR / f"{name}.kicad_mod", pretty / f"{name}.kicad_mod")
    (pretty / "RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias.kicad_mod").write_text(rp2350_solid_ep())
    w = Path("/usr/share/kicad/footprints/Package_SON.pretty/WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm.kicad_mod").read_text()
    w = w.replace('"WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm"', '"WSON-8_6x5mm_P1.27mm_NoEPCopper"', 1)
    w = strip_pads(w, {"9", ""})
    (pretty / "WSON-8_6x5mm_P1.27mm_NoEPCopper.kicad_mod").write_text(w)
    xb = XB.read_text().replace("DFNFC-6_L1.8-W1.4-P0.50_XB9901A", "XySemi_DFN-6_1.8x1.4mm")
    (pretty / "XySemi_DFN-6_1.8x1.4mm.kicad_mod").write_text(xb)
    print(f"wrote libs for {variant_name}: {pretty}")


if __name__ == "__main__":
    generate_libs(sys.argv[1])
