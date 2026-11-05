#!/usr/bin/env python3
"""make_nets_d.py -- write design/nets-d.csv, .kicad_pro, and .kicad_dru for Variant D (5x IS31FL3745 BGA).

    PENDANT_VARIANT=d python3 scripts/bga/make_nets_d.py
"""
import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VARIANT = os.environ.get("PENDANT_VARIANT", "d")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
NETS_CSV = ROOT / "design/nets-d.csv"
PRO = HW / "round-pendant.kicad_pro"
DRU = HW / "round-pendant.kicad_dru"

# Base non-driver rows shared with Variant C (with accepted crystal 11 mm & USB 1-via decisions from decisions.md 2026-11-04).
BASE_ROWS = [
    ("+1V1", "POWER", "1.1", "0.05", "0.1", "", "", "RP2350 core; reference zones per chips/rp2350.md"),
    ("+3V3", "POWER", "3.4", "0.04", "0.15", "", "", "Logic rail; 150 mA max, intent power table"),
    ("/MCU/ACC_INT", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/ACC_SCL", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/ACC_SDA", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/BTN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/QSPI_SCLK", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/QSPI_SD0", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/QSPI_SD1", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/QSPI_SD2", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/QSPI_SD3", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/QSPI_SS", "SE_HS", "3.4", "", "", "", "25", "Flash at up to 75 MHz; keep under 25 mm, chips and flash.md"),
    ("/MCU/RUN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/SWCLK", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/SWDIO", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/MCU/USB_DM_MCU", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, 27 R to pin, very short"),
    ("/MCU/USB_DP_MCU", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, 27 R to pin, very short"),
    ("/MCU/VREG_AVDD", "ANALOG", "3.4", "0.001", "0.001", "", "", "Regulator analog filter, RFILT and CFILT"),
    ("/MCU/VREG_LX", "SWITCH", "3.4", "0.1", "0.2", "", "", "Core regulator switch node; keep minimal; reference zone"),
    ("/Power/BAT_N", "POWER", "4.3", "0.34", "1.0", "", "", "Cell minus, XB9901A GND pins; never joined to board GND; protection.md"),
    ("/Power/CC1", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/Power/CC2", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("/Power/USB_DM_C", "DIFF_HS", "5.5", "", "", "90 diff", "", "USB FS, connector to ESD; both D- rows join here"),
    ("/Power/USB_DP_C", "DIFF_HS", "5.5", "", "", "90 diff", "", "USB FS, connector to ESD; both D+ rows join here"),
    ("CHG", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("GND", "POWER", "0", "1.0", "2.0", "", "", "Return for everything; plane on In2.Cu"),
    ("I2C_SCL", "SIGNAL", "3.4", "0.0033", "0.0033", "", "", "Driver bus to 5x IS31FL3745 at 1 MHz, 1 k pull-up; <100 pF; drivers-bga.md"),
    ("I2C_SDA", "SIGNAL", "3.4", "0.0033", "0.0033", "", "", "Driver bus to 5x IS31FL3745 at 1 MHz, 1 k pull-up; <100 pF; drivers-bga.md"),
    ("LED_SDB", "SIGNAL", "3.4", "", "", "", "", "Shared hardware shutdown to all 5 IS31FL3745 drivers; 100k pull-down + 100nF; drivers-bga.md"),
    ("Net-(C24-Pad1)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm (decisions.md 2026-11-04), no vias; rp2350-core.md"),
    ("Net-(Q1A-D)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("Net-(Q1B-D)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("Net-(R16-Pad2)", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("Net-(R18-Pad2)", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("Net-(U3-XIN)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm (decisions.md 2026-11-04), no vias; rp2350-core.md"),
    ("Net-(U3-XOUT)", "CLOCK", "3.4", "", "", "", "11", "12 MHz crystal; <=11 mm (decisions.md 2026-11-04), no vias; rp2350-core.md"),
    ("Net-(U5-ILIM)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node; resistor close, return to chip ground; datasheet layout"),
    ("Net-(U5-ISET)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node; resistor close, return to chip ground; datasheet layout"),
    ("Net-(U5-TS)", "ANALOG", "4.5", "", "", "", "", "Current-setting resistor node; resistor close, return to chip ground; datasheet layout"),
    ("Net-(U8-VDD)", "SIGNAL", "4.5", "", "", "", "", "Control or status, low current"),
    ("PGOOD", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("USB_DM", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, between ESD and 27 R; pair with USB_DP; max 1 via (decisions.md 2026-11-04)"),
    ("USB_DP", "DIFF_HS", "3.6", "", "", "90 diff", "", "USB FS, between ESD and 27 R; pair with USB_DM; max 1 via (decisions.md 2026-11-04)"),
    ("VBAT", "POWER", "4.3", "0.34", "1.0", "", "", "Protected cell rail; same load through BQ24073 BAT-OUT, charge 300 mA"),
    ("VBAT_EN", "SIGNAL", "3.4", "", "", "", "", "Control or status, low current"),
    ("VBAT_SENSE", "ANALOG", "3.4", "", "", "", "", "ADC0 from switched divider; away from LX and SW lines"),
    ("VBUS", "POWER", "5.5", "0.5", "0.5", "", "", "USB input, 500 mA limit, charger.md"),
    ("VSYS", "POWER", "4.5", "0.34", "1.02", "", "", "System rail: 300 mA LEDs + 40 mA logic; 5x 204 mA = 1.02 A scan peak; plane on In5.Cu; drivers-bga.md"),
]

DRIVER_REFS = [(1, "U1"), (2, "U2"), (3, "U10"), (4, "U11"), (5, "U12")]

# Board netclasses (matching c-solid-z10 + powerclass.py).
CLASSES = {
    "Default": (0.1, 0.09, 0.25, 0.15),
    "SIGNAL": (0.1, 0.09, 0.25, 0.15),
    "POWER": (0.2, 0.09, 0.3, 0.15),
    "SW_SCAN": (0.1, 0.09, 0.25, 0.15),
    "ANALOG": (0.1, 0.09, 0.25, 0.15),
    "CLOCK": (0.15, 0.15, 0.25, 0.15),
    "SE_HS": (0.1, 0.1, 0.25, 0.15),
    "SWITCH": (0.4, 0.12, 0.3, 0.15),
    "DIFF_HS": (0.15, 0.15, 0.25, 0.15),
    "BATTERY": (0.3, 0.09, 0.3, 0.15),
    "USB_POWER": (0.25, 0.09, 0.3, 0.15),
}


def build_rows():
    rows = list(BASE_ROWS)
    for idx, uref in DRIVER_REFS:
        for cs in range(1, 19):
            rows.append(
                (
                    f"/Driver {idx} and matrix/CS{idx}_{cs}",
                    "SIGNAL",
                    "4.5",
                    "0.010",
                    "0.0114",
                    "",
                    "",
                    "LED sink: 11.34 mA peak; up to 8 LEDs of one colour; drivers-bga.md",
                )
            )
        for sw in range(1, 9):
            rows.append(
                (
                    f"/Driver {idx} and matrix/SW{idx}_{sw}",
                    "SIGNAL",
                    "4.5",
                    "0.025",
                    "0.204",
                    "",
                    "",
                    "LED scan line: 204 mA peak at 1/8.2 duty (25 mA avg); 0.1 mm track; drivers-bga.md",
                )
            )
        rows.append(
            (
                f"Net-({uref}-RSET)",
                "ANALOG",
                "4.5",
                "",
                "",
                "",
                "",
                "Current-setting resistor node (30 k); resistor close, return to F4 GND; drivers-bga.md",
            )
        )
    rows.sort(key=lambda r: r[0])
    return rows


def write_rules(rows):
    HW.mkdir(parents=True, exist_ok=True)
    tmpl_pro = ROOT / "hw/round-pendant/c/round-pendant.kicad_pro"
    d = json.loads(tmpl_pro.read_text())
    d["meta"]["filename"] = PRO.name
    d["sheets"] = []
    d["boards"] = []
    ds = d["board"]["design_settings"]
    ds["rules"].update(
        min_clearance=0.09,
        min_copper_edge_clearance=0.2,
        min_hole_clearance=0.2,
        min_hole_to_hole=0.2,
        min_resolved_spokes=1,
        min_through_hole_diameter=0.1,
        min_track_width=0.09,
        min_via_annular_width=0.05,
        min_via_diameter=0.2,
    )
    ds["via_dimensions"] = [
        {"diameter": 0, "drill": 0},
        {"diameter": 0.25, "drill": 0.15},
        {"diameter": 0.3, "drill": 0.15},
    ]
    ds["track_widths"] = [0, 0.1, 0.15, 0.2, 0.3, 0.4]
    ds["rule_severities"].update(
        silk_overlap="error",
        silk_over_copper="error",
        track_dangling="error",
        via_dangling="warning",
        net_conflict="error",
        duplicate_footprints="error",
        extra_footprint="error",
        missing_footprint="error",
        lib_footprint_issues="warning",
        lib_footprint_mismatch="ignore",
    )
    tmpl_cls = d["net_settings"]["classes"][0]
    d["net_settings"]["classes"] = []
    for n, (w, c, vd, vh) in CLASSES.items():
        k = dict(
            tmpl_cls,
            name=n,
            track_width=w,
            clearance=c,
            via_diameter=vd,
            via_drill=vh,
            microvia_diameter=0.2,
            microvia_drill=0.1,
            diff_pair_width=0.15,
            diff_pair_gap=0.15,
            priority=2147483647 if n == "Default" else len(d["net_settings"]["classes"]),
        )
        d["net_settings"]["classes"].append(k)

    pats = []
    for r in rows:
        net, cls = r[0], r[1]
        if net in ("VBAT", "/Power/BAT_N"):
            cls = "BATTERY"
        elif net == "VBUS":
            cls = "USB_POWER"
        elif "/SW" in net and net.startswith("/Driver "):
            cls = "SW_SCAN"
        pats.append({"netclass": cls, "pattern": net})
    d["net_settings"]["netclass_patterns"] = pats
    PRO.write_text(json.dumps(d, indent=2) + "\n")

    out = [
        "(version 1)",
        "",
        "# Derived from design/nets-d.csv and design/brief.md. Each rule cites its source.",
        "",
    ]
    for net, w, why in (
        ("VBUS", 0.25, "0.5 A, nets-d.csv; IPC-2221 outer 1 oz, 10 C rise"),
        ("VSYS", 0.2, "VSYS plane on In5.Cu; pad stubs min 0.2 mm (powerclass.py / LESSONS.md)"),
        ("VBAT", 0.3, "0.34 A avg, 1 A peak, nets-d.csv"),
        ("/Power/BAT_N", 0.3, "same as VBAT, cell minus"),
        ("+3V3", 0.2, "150 mA max, intent.md"),
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
                "  (constraint track_width (min 0.1mm)))",
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
    out += [
        '(rule "USB_DM one via"',
        '  (condition "A.NetName == \'USB_DM\'")',
        "  (constraint via_count (max 1)))",
        '(rule "USB_DP one via"',
        '  (condition "A.NetName == \'USB_DP\'")',
        "  (constraint via_count (max 1)))",
        "",
        '(rule "U3 ring foreign vias"',
        '  (condition "A.intersectsArea(\'U3 ring vias\') && A.NetName != \'+1V1\' && A.NetName != \'GND\'")',
        "  (constraint disallow via))",
        "",
        "# U3 and regulator keep-outs: foreign nets only (LESSONS.md, a part's own power may pass).",
        '(rule "U3 ring foreign tracks"',
        '  (condition "A.intersectsArea(\'U3 ring\') && A.NetName != \'+3V3\' && A.NetName != \'+1V1\' && A.NetName != \'GND\'")',
        "  (constraint disallow track))",
        '(rule "reg corner foreign"',
        '  (condition "A.intersectsArea(\'reg corner\') && A.NetName != \'/MCU/VREG_LX\' && A.NetName != \'+1V1\' && A.NetName != \'+3V3\' && A.NetName != \'GND\' && A.NetName != \'/MCU/VREG_AVDD\'")',
        "  (constraint disallow track via))",
        '(rule "L1 window foreign"',
        '  (condition "A.intersectsArea(\'L1 window\') && A.NetName != \'/MCU/VREG_LX\' && A.NetName != \'+1V1\'")',
        "  (constraint disallow track via))",
    ]
    DRU.write_text("\n".join(out) + "\n")


def main():
    rows = build_rows()
    with NETS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["net", "class", "v_max", "i_cont", "i_peak", "impedance", "length_limit", "reason"])
        w.writerows(rows)
    write_rules(rows)
    print(f"wrote {NETS_CSV} ({len(rows)} rows), {PRO}, {DRU}")


if __name__ == "__main__":
    main()
