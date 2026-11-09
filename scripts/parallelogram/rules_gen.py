#!/usr/bin/env python3
"""rules_gen.py -- write design/nets-parallelogram-<variant>.csv, .kicad_pro, and .kicad_dru (4L JLCPCB standard)."""
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/parallelogram"))
from config import VARIANTS, VariantSpec, build_led_cells  # noqa: E402

BASE_ROWS = [
    ("+1V1", "POWER", "1.1", "0.05", "0.1", "", "", "RP2350 core; reference ring + regulator zones per chips/rp2350.md"),
    ("+3V3", "POWER", "3.4", "0.04", "0.15", "", "", "Logic rail; 150 mA max, RP2350 band + local links"),
    ("/MCU/ACC_INT", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/ACC_SCL", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/ACC_SDA", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/BTN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/LIGHT", "ANALOG", "3.4", "0.00015", "0.00015", "", "", "XYC-PT19C-L1 emitter analog node (22 k || 100 nF to GND, ADC1)"),
    ("/MCU/LIGHT_PWR", "SIGNAL", "3.4", "0.00015", "0.00015", "", "", "GPIO1 switched 3.3 V collector supply for Q2 (0 uA sleep)"),
    ("/MCU/QSPI_SCLK", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/QSPI_SD0", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/QSPI_SD1", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/QSPI_SD2", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/QSPI_SD3", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/QSPI_SS", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm"),
    ("/MCU/RUN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/SWCLK", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/SWDIO", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/USB_DM_MCU", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, 27 R to pin, very short"),
    ("/MCU/USB_DP_MCU", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, 27 R to pin, very short"),
    ("/MCU/VREG_AVDD", "ANALOG", "3.4", "0.001", "0.001", "", "", "Regulator analog filter, RFILT and CFILT"),
    ("/MCU/VREG_LX", "SWITCH", "3.4", "0.1", "0.2", "", "", "Core regulator switch node; reference zone"),
    ("/Power/BAT_N", "POWER", "4.3", "0.34", "1.0", "", "", "Cell minus, XB9901A GND pins; never joined to board GND"),
    ("/Power/CC1", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/Power/CC2", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/Power/USB_DM_C", "DIFF_HS", "5.5", "", "", "90 diff", "", "USB FS, pads to ESD"),
    ("/Power/USB_DP_C", "DIFF_HS", "5.5", "", "", "90 diff", "", "USB FS, pads to ESD"),
    ("CHG", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("GND", "POWER", "0", "1.0", "2.0", "", "", "Return for everything; unbroken solid plane on In1.Cu (L2)"),
    ("I2C_SCL", "SIGNAL", "3.4", "0.0033", "0.0033", "", "", "Driver bus to AW20198QNR at 1 MHz, 1 k pull-up"),
    ("I2C_SDA", "SIGNAL", "3.4", "0.0033", "0.0033", "", "", "Driver bus to AW20198QNR at 1 MHz, 1 k pull-up"),
    ("LED_SDB", "SIGNAL", "3.4", "", "", "", "", "Shared AW20198QNR EN; 100k pull-down + 100nF"),
    ("Net-(C24-Pad1)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm, no vias"),
    ("Net-(Q1A-D)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("Net-(Q1B-D)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("Net-(R16-Pad2)", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("Net-(R18-Pad2)", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("Net-(U3-XIN)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm, no vias"),
    ("Net-(U3-XOUT)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm, no vias"),
    ("Net-(U5-ILIM)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node"),
    ("Net-(U5-ISET)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node"),
    ("Net-(U5-TS)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node"),
    ("Net-(U8-VDD)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("PGOOD", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("USB_DM", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, between ESD and 27 R"),
    ("USB_DP", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, between ESD and 27 R"),
    ("VBAT", "POWER", "4.3", "0.34", "1.0", "", "", "Protected cell rail; 300 mA charge"),
    ("VBAT_EN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("VBAT_SENSE", "ANALOG", "3.4", "", "", "", "", "ADC0 from switched divider"),
    ("VBUS", "POWER", "5.5", "0.5", "0.5", "", "", "USB input, 500 mA limit"),
    ("VSYS", "POWER", "4.5", "0.34", "0.96", "", "", "System rail: 300 mA LEDs + 40 mA logic; routed 0.25 mm min"),
]

# 4-layer JLCPCB netclasses (0.10 mm min trace/space, 0.15 mm drill / 0.30 mm via for 0.40 mm QFN escape, 0 via-in-pad):
CLASSES = {
    "Default": (0.10, 0.10, 0.30, 0.15),
    "SIGNAL": (0.10, 0.10, 0.30, 0.15),
    "POWER": (0.20, 0.10, 0.30, 0.15),
    "SW_SCAN": (0.10, 0.10, 0.30, 0.15),
    "ANALOG": (0.10, 0.10, 0.30, 0.15),
    "CLOCK": (0.15, 0.15, 0.30, 0.15),
    "SE_HS": (0.10, 0.10, 0.30, 0.15),
    "SWITCH": (0.40, 0.12, 0.35, 0.15),
    "DIFF_HS": (0.15, 0.15, 0.30, 0.15),
    "BATTERY": (0.25, 0.10, 0.35, 0.15),
    "USB_POWER": (0.25, 0.10, 0.35, 0.15),
}


def build_rows(spec: VariantSpec):
    rows = list(BASE_ROWS)
    if spec.io_mode == "usb":
        rows.extend([
            ("/MCU/BTN_NW", "SIGNAL", "3.4", "", "", "", "", "NW back-wing flat-face push button via 1 k (GPIO7)"),
            ("/MCU/BTN_SE", "SIGNAL", "3.4", "", "", "", "", "SE back-wing flat-face push button via 1 k (GPIO19)"),
            ("Net-(R44-Pad2)", "SIGNAL", "3.4", "", "", "", "", "SW3 NW wing button node between 1 k R44 and switch"),
            ("Net-(R45-Pad2)", "SIGNAL", "3.4", "", "", "", "", "SW4 SE wing button node between 1 k R45 and switch"),
        ])
    if spec.extra_side_buttons:
        patched = []
        for r in rows:
            net, cls, vmax, ic, ipk, imp, llim, why = r
            if net in ("VBAT", "/Power/BAT_N", "VBUS"):
                cls = "POWER_HI"
            elif net == "GND":
                ic = "0.50"
                why = "0.50 A max per pad escape stub; 1.0 A / 2.0 A bulk return in unbroken In1.Cu plane GND"
            elif net == "VSYS":
                why = "System rail: 300 mA LEDs + 40 mA logic; 0.20 mm POWER nominal, 0.16 mm DRU min for 0.20 mm AW20198 PVCC pads"
            elif net in ("/Power/USB_DP_C", "/Power/USB_DM_C", "USB_DP", "USB_DM"):
                llim = "35"
            elif net in ("/MCU/USB_DP_MCU", "/MCU/USB_DM_MCU"):
                llim = "6"
                why = "USB FS, 27 R to pin, <=6 mm, no vias"
            patched.append((net, cls, vmax, ic, ipk, imp, llim, why))
        rows = patched
        rows.extend([
            ("/MCU/USER_C", "SIGNAL", "3.4", "", "", "", "", "West-North side push button SW5 via 1 k R46 + 100 nF C71 (GPIO9)"),
            ("/MCU/USER_D", "SIGNAL", "3.4", "", "", "", "", "West-South side push button SW6 via 1 k R47 + 100 nF C72 (GPIO0)"),
            ("Net-(R46-Pad2)", "SIGNAL", "3.4", "", "", "", "", "SW5 West-North button node between 1 k R46 and switch"),
            ("Net-(R47-Pad2)", "SIGNAL", "3.4", "", "", "", "", "SW6 West-South button node between 1 k R47 and switch"),
        ])
    cells = build_led_cells(spec)
    for drv in spec.drivers:
        drv_cells = [c for c in cells if c["drv_idx"] == drv.idx]
        used_sws = sorted({c["sw"] for c in drv_cells})
        used_trips = sorted({c["triplet"] for c in drv_cells})
        used_css = sorted({3 * k - off for k in used_trips for off in (0, 1, 2)})
        for cs in used_css:
            rows.append((
                f"/Driver {drv.idx} and matrix/CS{drv.idx}_{cs}",
                "SIGNAL", "4.5", "0.011", "0.0133", "", "",
                "AW20198 CS sink: 13.33 mA peak (1.07 mA avg); drivers-aw20198.md",
            ))
        for sw in used_sws:
            rows.append((
                f"/Driver {drv.idx} and matrix/SW{drv.idx}_{sw}",
                "SIGNAL", "4.5", "0.020", "0.240", "", "",
                "AW20198 SW scan line: 240 mA peak at 1/12.4 duty (19.3 mA avg); drivers-aw20198.md",
            ))
        rows.append((
            f"Net-({drv.uref}-ISET)",
            "ANALOG", "4.5", "", "", "", "",
            "AW20198 ISET current-setting resistor node (30 k to GND); drivers-aw20198.md",
        ))
    rows.sort(key=lambda r: r[0])
    return rows


def generate_rules(variant_name: str):
    spec = VARIANTS[variant_name]
    hw = spec.hw_dir
    hw.mkdir(parents=True, exist_ok=True)
    rows = build_rows(spec)

    design_dir = Path(os.environ["PARALLELOGRAM_DESIGN_ROOT"]) if os.environ.get("PARALLELOGRAM_DESIGN_ROOT") else (ROOT / "design")
    design_dir.mkdir(parents=True, exist_ok=True)
    nets_csv = design_dir / f"nets-parallelogram-{variant_name}.csv"
    with nets_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["net", "class", "v_max", "i_cont", "i_peak", "impedance", "length_limit", "reason"])
        w.writerows(rows)

    pro = hw / "parallelogram.kicad_pro"
    dru = hw / "parallelogram.kicad_dru"
    tmpl_pro = ROOT / "hw/round-pendant/c/round-pendant.kicad_pro"
    d = json.loads(tmpl_pro.read_text())
    d["meta"]["filename"] = pro.name
    d["sheets"] = []
    d["boards"] = []
    ds = d["board"]["design_settings"]
    ds["rules"].update(
        min_clearance=0.10,
        min_connection=0.09,
        min_copper_edge_clearance=0.25,
        min_hole_clearance=0.20,
        min_hole_to_hole=0.20,
        min_resolved_spokes=1,
        min_text_height=0.8,
        min_text_thickness=0.15,
        min_through_hole_diameter=0.15,
        min_track_width=0.10,
        min_via_annular_width=0.05,
        min_via_diameter=0.30,
    )
    ds["via_dimensions"] = [
        {"diameter": 0, "drill": 0},
        {"diameter": 0.30, "drill": 0.15},
        {"diameter": 0.35, "drill": 0.15},
    ]
    ds["track_widths"] = [0, 0.10, 0.12, 0.15, 0.16, 0.20, 0.25, 0.30, 0.40]
    ds["rule_severities"].update(
        connection_width="error",
        copper_sliver="error",
        hole_to_hole="error",
        holes_co_located="error",
        isolated_copper="error",
        silk_overlap="error",
        silk_over_copper="error",
        track_dangling="error",
        via_dangling="error",
        net_conflict="error",
        duplicate_footprints="error",
        extra_footprint="error",
        missing_footprint="error",
        lib_footprint_issues="warning",
        lib_footprint_mismatch="ignore",
    )
    if spec.extra_side_buttons:
        ds["rules"]["min_copper_edge_clearance"] = 0.30
        ds["rules"]["solder_mask_min_width"] = 0.0
        if "defaults" in ds:
            ds["defaults"]["silk_text_thickness"] = 0.15
        ds["rule_severities"].update(
            footprint_symbol_mismatch="error",
            lib_footprint_issues="error",
            missing_courtyard="error",
            silk_edge_clearance="error",
            text_height="error",
            text_thickness="error",
            mirrored_text_on_front_layer="error",
            nonmirrored_text_on_back_layer="error",
            padstack="error",
        )
    tmpl_cls = d["net_settings"]["classes"][0]
    d["net_settings"]["classes"] = []
    cls_map = dict(CLASSES)
    if spec.extra_side_buttons:
        cls_map["POWER_HI"] = (0.25, 0.10, 0.35, 0.15)
    for n, (w, c, vd, vh) in cls_map.items():
        k = dict(
            tmpl_cls,
            name=n,
            track_width=w,
            clearance=c,
            via_diameter=vd,
            via_drill=vh,
            microvia_diameter=0.45,
            microvia_drill=0.20,
            diff_pair_width=0.15,
            diff_pair_gap=0.15,
            priority=2147483647 if n == "Default" else len(d["net_settings"]["classes"]),
        )
        d["net_settings"]["classes"].append(k)

    pats = []
    for r in rows:
        net, cls = r[0], r[1]
        if not spec.extra_side_buttons:
            if net in ("VBAT", "/Power/BAT_N"):
                cls = "BATTERY"
            elif net == "VBUS":
                cls = "USB_POWER"
            elif "/SW" in net and net.startswith("/Driver "):
                cls = "SW_SCAN"
        pats.append({"netclass": cls, "pattern": net})
    d["net_settings"]["netclass_patterns"] = pats
    if spec.extra_side_buttons:
        d["net_settings"]["netclass_assignments"] = {r[0]: [r[1]] for r in rows}
    pro.write_text(json.dumps(d, indent=2) + "\n")

    out = [
        "(version 1)",
        "",
        f"# 4-layer JLCPCB JLC04161H-7628 rules for parallelogram/{variant_name}.",
        "",
    ]
    for net, w, why in (
        ("VBUS", 0.25, "0.5 A USB input, IPC-2221 outer 1 oz"),
        ("VSYS", 0.16, "340 mA avg system rail (IPC-2152 0.09 mm; 0.16 mm enters 0.20 mm AW20198 PVCC/VCC pads cleanly)"),
        ("VBAT", 0.25, "0.34 A avg, 1 A peak battery rail"),
        ("/Power/BAT_N", 0.25, "cell minus protection path"),
        ("+3V3", 0.15, "150 mA max logic rail (IPC-2152 0.09 mm)"),
    ):
        out += [
            f"# {why}",
            f'(rule "{net} current width"',
            f'  (condition "A.NetName == \'{net}\'")',
            f"  (constraint track_width (min {w}mm)))",
            "",
        ]
    for r in rows:
        net, length_lim, reason = r[0], r[6], r[7]
        if "/SW" in net and net.startswith("/Driver "):
            out += [
                f'(rule "{net} width"',
                f'  (condition "A.NetName == \'{net}\'")',
                "  (constraint track_width (min 0.10mm)))",
                "",
            ]
        if length_lim:
            out += [
                f'(rule "{net} length"',
                f'  (condition "A.NetName == \'{net}\'")',
                f"  (constraint length (max {length_lim}mm)))",
            ]
        if "no vias" in reason:
            out += [
                f'(rule "{net} no vias"',
                f'  (condition "A.NetName == \'{net}\'")',
                "  (constraint via_count (max 0)))",
            ]

    # Solid exposed thermal pads on U3, U5, and every AW20198QNR driver: zero foreign vias or B.Cu tracks.
    solid_refs = ["U3", "U5"] + [drv.uref for drv in spec.drivers]
    for sref in solid_refs:
        out += [
            f'(rule "{sref} solid EP foreign"',
            f'  (condition "A.intersectsArea(\'{sref} solid EP\') && A.NetName != \'GND\'")',
            "  (constraint disallow track via))",
            "",
        ]

    out += [
        '(rule "U3 ring foreign vias"',
        '  (condition "A.intersectsArea(\'U3 ring vias\') && A.NetName != \'+1V1\' && A.NetName != \'GND\'")',
        "  (constraint disallow via))",
        '(rule "U3 ring foreign tracks"',
        '  (condition "A.intersectsArea(\'U3 ring\') && A.NetName != \'+3V3\' && A.NetName != \'+1V1\' && A.NetName != \'GND\'")',
        "  (constraint disallow track))",
        '(rule "reg corner foreign"',
        '  (condition "A.intersectsArea(\'reg corner\') && A.NetName != \'/MCU/VREG_LX\' && A.NetName != \'+1V1\' && A.NetName != \'+3V3\' && A.NetName != \'GND\' && A.NetName != \'/MCU/VREG_AVDD\'")',
        "  (constraint disallow track via))",
        '(rule "L1 window foreign"',
        '  (condition "A.intersectsArea(\'L1 window\') && A.NetName != \'/MCU/VREG_LX\' && A.NetName != \'+1V1\'")',
        "  (constraint disallow track via))",
        '(rule "vendor +1V1 area foreign"',
        '  (condition "A.intersectsArea(\'vendor +1V1 area\') && A.NetName != \'+1V1\'")',
        "  (constraint disallow track via))",
        '(rule "vendor GND area foreign"',
        '  (condition "A.intersectsArea(\'vendor GND area\') && A.NetName != \'GND\'")',
        "  (constraint disallow track via))",
        '(rule "vendor VREG_LX area foreign"',
        '  (condition "A.intersectsArea(\'vendor /MCU/VREG_LX area\') && A.NetName != \'/MCU/VREG_LX\'")',
        "  (constraint disallow track via))",
        '(rule "vendor +3V3 area foreign"',
        '  (condition "A.intersectsArea(\'vendor +3V3 area\') && A.NetName != \'+3V3\'")',
        "  (constraint disallow track via))",
    ]
    if spec.extra_side_buttons:
        out += [
            "",
            "# Unbroken RP2350 +3V3 band: disallow foreign vias and non-+3V3 B.Cu crossings inside U3 band annulus",
            '(rule "U3 band foreign"',
            '  (condition "A.intersectsArea(\'U3 band\') && A.NetName != \'+3V3\'")',
            "  (constraint disallow track via))",
            "# Enforce 0.15 mm CLOCK and MCU-side USB stub widths; non-HDI 4L disallows micro/buried vias",
            '(rule "12 MHz crystal width"',
            '  (condition "A.NetClass == \'CLOCK\'")',
            "  (constraint track_width (min 0.15mm)))",
            '(rule "MCU USB stub width"',
            '  (condition "A.NetName == \'/MCU/USB_DP_MCU\' || A.NetName == \'/MCU/USB_DM_MCU\'")',
            "  (constraint track_width (min 0.15mm)))",
            '(rule "4L standard through-vias only"',
            '  (condition "A.Type == \'Via\'")',
            "  (constraint disallow microvia buried_via))",
        ]
    dru.write_text("\n".join(out) + "\n")
    print(f"wrote rules for {variant_name}: {nets_csv} ({len(rows)} rows), {pro}, {dru}")


if __name__ == "__main__":
    generate_rules(sys.argv[1])
