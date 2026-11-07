#!/usr/bin/env python3
"""sch_gen.py -- generate hierarchical KiCad 9 schematics for hw/sunflower/<variant>/."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
sys.path.insert(0, str(ROOT / "scripts/sunflower"))

from kicad_write import S, Schematic, Sym, SymbolLib, dump, new_uuid, yes  # noqa: E402
from config import USB_FP, BAT_FP, BAT_LCSC, BAT_MFR, BAT_MPN, BAT_VALUE, VARIANTS, VariantSpec, DriverSpec, build_led_cells  # noqa: E402

PROJECT = "sunflower"
DATE = "2026-11-05"

C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0402S = "round_pendant:C_0402_1005Metric_small_pads"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
TP = "TestPoint:TestPoint_Pad_D1.0mm"
BTN_FP = "round_pendant:SW_Panasonic_EVQP7J"
BTN_FIELDS = {"LCSC": "C2828254", "MPN": "EVQP7J01P", "Manufacturer": "PANASONIC"}

PARTS = {
    "100n": ("C1525", "CL05B104KO5NNNC", "Samsung Electro-Mechanics"),
    "1u": ("C52923", "CL05A105KA5NQNC", "Samsung Electro-Mechanics"),
    "4.7u": ("C23733", "CL05A475MP5NRNC", "Samsung Electro-Mechanics"),
    "10u": ("C19702", "CL10A106KP8NNNC", "Samsung Electro-Mechanics"),
    "22u": ("C86295", "CL10A226MP8NUNE", "Samsung Electro-Mechanics"),
    "15p": ("C1548", "0402CG150J500NT", "FH"),
    "27R": ("C25100", "0402WGF270JTCE", "UNI-ROYAL"),
    "33R": ("C25105", "0402WGF330JTCE", "UNI-ROYAL"),
    "100R": ("C25076", "0402WGF1000TCE", "UNI-ROYAL"),
    "1k": ("C11702", "0402WGF1001TCE", "UNI-ROYAL"),
    "3k": ("C25784", "0402WGF3001TCE", "UNI-ROYAL"),
    "3.6k": ("C25891", "0402WGF3601TCE", "UNI-ROYAL"),
    "4.7k": ("C25900", "0402WGF4701TCE", "UNI-ROYAL"),
    "5.1k": ("C25905", "0402WGF5101TCE", "UNI-ROYAL"),
    "10k": ("C25744", "0402WGF1002TCE", "UNI-ROYAL"),
    "22k": ("C25768", "0402WGF2202TCE", "UNI-ROYAL"),
    "30k": ("C25776", "0402WGF3002TCE", "UNI-ROYAL"),
    "100k": ("C25741", "0402WGF1003TCE", "UNI-ROYAL"),
}
GL = dict(kind="global_label")


def fields(value: str) -> dict:
    lcsc, mpn, mfr = PARTS[value]
    return {"LCSC": lcsc, "MPN": mpn, "Manufacturer": mfr}


class Sheet(Schematic):
    def __init__(self, spec: VariantSpec, libs: SymbolLib, title: str, comment: str, paper: str = "A3"):
        super().__init__(
            PROJECT,
            title=f"sunflower ({spec.name}): {title}",
            rev=spec.title_rev,
            date=DATE,
            company="CERN-OHL-P-2.0",
            comments=[comment, "Drawn by scripts/sunflower/sch_gen.py"],
            paper=paper,
            libs=libs,
        )

    def cap(self, ref, value, top, fp=C0402, text_left=False, decouples=None):
        x, y = top
        dx = -2.54 if text_left else 2.54
        j = "right" if text_left else "left"
        f = fields(value) | ({"Decouples": decouples} if decouples else {})
        c = self.symbol(
            "Device:C", ref, value, (x, y + 3.81), footprint=fp, fields=f,
            ref_at=(x + dx, y + 2.54), value_at=(x + dx, y + 5.08), justify=j,
        )
        self.power("power:GND", (x, y + 7.62))
        return c

    def res_v(self, ref, value, top, text_left=False, to_gnd=False):
        x, y = top
        dx = -2.54 if text_left else 2.54
        j = "right" if text_left else "left"
        r = self.symbol(
            "Device:R", ref, value, (x, y + 3.81), footprint=R0402, fields=fields(value),
            ref_at=(x + dx, y + 2.54), value_at=(x + dx, y + 5.08), justify=j,
        )
        if to_gnd:
            self.power("power:GND", (x, y + 7.62))
        return r

    def res_h(self, ref, value, left, text_below=False):
        x, y = left
        ty = (y + 2.54, y + 5.08) if text_below else (y - 5.08, y - 2.54)
        return self.symbol(
            "Device:R", ref, value, (x + 3.81, y), rot=90, footprint=R0402, fields=fields(value),
            ref_at=(x + 3.81, ty[0]), value_at=(x + 3.81, ty[1]), justify="",
        )

    def tp(self, ref, net, at):
        t = self.symbol(
            "Connector:TestPoint", ref, net, (at[0], at[1] + 2.54), rot=180,
            footprint=TP, in_bom=False, fields={"Manufacturer": "", "MPN": "", "LCSC": ""},
            ref_at=(at[0] + 2.54, at[1] + 5.08), value_at=(at[0] + 2.54, at[1] + 7.62),
        )
        self.wire(at, t.pin("1"))
        return t


def build_power(spec: VariantSpec, libs: SymbolLib) -> Sheet:
    s = Sheet(spec, libs, "power", "USB-C wires, charger, protection, LDO, VBAT sense (35 mm round cell on a PicoBlade 1.25 mm plug)")
    if spec.usb_c:
        j1 = s.symbol(
            "round_pendant:USB_C_16P", "J1", "USB-C", (40.64, 93.98),
            footprint=USB_FP,
            fields={"LCSC": "C165948", "MPN": "TYPE-C-31-M-12", "Manufacturer": "Korean Hroparts Elec"},
            ref_at=(30.48, 78.74), value_at=(30.48, 81.28),
        )
        # The wire-pad symbol's pin numbers, mapped to the receptacle's
        jp = {"1": "A5", "2": "B5", "3": "A7", "4": "A6", "5": "A4", "6": "A1"}
        sh = j1.pin("S1")
        s.wire(sh, (sh[0] + 2.54, sh[1]))
        s.power("power:GND", (sh[0] + 2.54, sh[1]))
        for nc in ("A8", "B8"):
            s.no_connect(j1.pin(nc))
    else:
        j1 = s.symbol(
            "round_pendant:USB_Pads", "J1", "USB wires", (40.64, 93.98),
            in_bom=False, fields={"MPN": "none, wire pads"}, ref_at=(30.48, 81.28), value_at=(30.48, 83.82),
        )
        jp = {k: k for k in "123456"}
    vbus_y = 68.58
    px = j1.pin(jp["5"])[0]
    s.wire(j1.pin(jp["5"]), (px + 2.54, j1.pin(jp["5"])[1]), (px + 2.54, vbus_y), (64.77, vbus_y))
    g = j1.pin(jp["6"])
    s.wire(g, (g[0] + 2.54, g[1]), (g[0] + 2.54, g[1] + 7.62))
    s.power("power:GND", (g[0] + 2.54, g[1] + 7.62))
    s.power("power:PWR_FLAG", (g[0] + 7.62, g[1] + 7.62), rot=180, value="PWR_FLAG")
    s.wire((g[0] + 2.54, g[1] + 7.62), (g[0] + 7.62, g[1] + 7.62))
    for pin, net, x, ref in (("1", "CC1", 60.96, "R1"), ("2", "CC2", 71.12, "R2")):
        p = j1.pin(jp[pin])
        s.wire(p, (x, p[1]), (x, 104.14))
        s.label(net, (p[0] + 7.62, p[1]))
        s.res_v(ref, "5.1k", (x, 104.14), to_gnd=True)

    u7 = s.symbol(
        "Power_Protection:USBLC6-2P6", "U7", "USBLC6-2P6", (86.36, 88.9),
        footprint="Package_TO_SOT_SMD:SOT-666",
        fields={"LCSC": "C15999", "MPN": "USBLC6-2P6", "Manufacturer": "STMicroelectronics"},
        ref_at=(90.17, 99.06), value_at=(90.17, 101.6),
    )
    for pin, u, jog in (("3", "1", 5.08), ("4", "3", 7.62)):
        q, v = j1.pin(jp[pin]), u7.pin(u)
        s.wire(q, (q[0] + jog, q[1]), (q[0] + jog, v[1]), v)
    s.label("USB_DM_C", (74.93, u7.pin("1")[1]))
    s.label("USB_DP_C", (74.93, u7.pin("3")[1]))
    s.wire(u7.pin("5"), (86.36, vbus_y))
    s.power("power:GND", u7.pin("2"))
    for pin, net in (("6", "USB_DM"), ("4", "USB_DP")):
        p = u7.pin(pin)
        s.wire(p, (p[0] + 5.08, p[1]))
        s.label(net, (p[0] + 5.08, p[1]), **GL)
    s.wire((64.77, vbus_y), (121.92, vbus_y))
    s.power("power:VBUS", (73.66, vbus_y))
    s.power("power:PWR_FLAG", (81.28, vbus_y), value="PWR_FLAG")
    s.box((15.24, 55.88), (110.49, 132.08), "USB-C, ESD" if spec.usb_c else "USB WIRES, ESD")

    u5x, u5y = 160.02, 86.36
    u5 = s.symbol(
        "round_pendant:BQ24073", "U5", "BQ24073", (u5x, u5y),
        fields={"LCSC": "C15220", "MPN": "BQ24073RGTR", "Manufacturer": "Texas Instruments"},
        footprint="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
        ref_at=(u5x - 8.89, u5y - 19.05), value_at=(u5x + 8.89, u5y - 19.05),
    )
    i = u5.pin("IN")
    s.wire((121.92, vbus_y), (121.92, i[1]), i)
    s.cap("C1", "1u", (116.84, vbus_y), decouples="U5.13")
    en1, en2, ce, td = u5.pin("EN1"), u5.pin("EN2"), u5.pin("CE"), u5.pin("TD")
    s.wire(en1, (en1[0] - 7.62, en1[1]))
    s.power("power:+3V3", (en1[0] - 7.62, en1[1]))
    gx = en1[0] - 2.54
    s.wire(en2, (gx, en2[1]))
    s.wire(ce, (gx, ce[1]))
    s.wire(td, (gx, td[1]))
    s.wire((gx, en2[1]), (gx, td[1] + 1.27))
    s.power("power:GND", (gx, td[1] + 1.27))
    for pin, ref, val, x in (("TS", "R3", "10k", 119.38), ("ISET", "R4", "3k", 129.54), ("ILIM", "R5", "3.6k", 139.7)):
        p = u5.pin(pin)
        s.wire(p, (x, p[1]))
        s.res_v(ref, val, (x, p[1]), text_left=True, to_gnd=True)
    s.no_connect(u5.pin("TMR"))
    s.text("USB500: 450-500 mA in. 297 mA charge, ILIM must not float.\nTMR open: default 5 h. TS fixed: no NTC.", (116.84, 124.46))
    s.power("power:GND", u5.pin("VSS"))
    pg, ch = u5.pin("~{PGOOD}"), u5.pin("~{CHG}")
    for p, net in ((pg, "PGOOD"), (ch, "CHG")):
        s.wire(p, (205.74, p[1]))
        s.label(net, (205.74, p[1]), **GL)
    s.res_v("R6", "100k", (198.12, pg[1] - 7.62))
    s.power("power:+3V3", (198.12, pg[1] - 7.62))
    s.res_v("R7", "100k", (187.96, pg[1] - 10.16), text_left=True)
    s.power("power:+3V3", (187.96, pg[1] - 10.16))
    s.wire((187.96, pg[1] - 2.54), (187.96, ch[1]))
    o, b = u5.pin("OUT"), u5.pin("BAT")
    vsys_y = o[1]
    s.wire(o, (228.6, vsys_y))
    s.power("round_pendant:VSYS", (205.74, vsys_y))
    s.cap("C2", "22u", (213.36, vsys_y), fp=C0603, text_left=True, decouples="U5.10")
    s.tp("TP1", "VSYS", (218.44, vsys_y))
    s.box((111.76, 55.88), (227.33, 132.08), "CHARGER AND POWER PATH")

    u6 = s.symbol(
        "round_pendant:TPS7A0233", "U6", "TPS7A0233", (254.0, vsys_y + 2.54),
        footprint="Package_SON:Texas_X2SON-4_1x1mm_P0.65mm",
        fields={"LCSC": "C2860046", "MPN": "TPS7A0233PDQNR", "Manufacturer": "Texas Instruments"},
        ref_at=(246.38, vsys_y - 7.62), value_at=(246.38, vsys_y - 5.08),
    )
    vin, en = u6.pin("IN"), u6.pin("EN")
    s.wire((228.6, vsys_y), (233.68, vsys_y), (233.68, vin[1]), vin)
    s.wire((vin[0] - 2.54, vin[1]), (vin[0] - 2.54, en[1]), en)
    s.cap("C3", "1u", (233.68, vin[1]), text_left=True, decouples="U6.4")
    s.power("power:GND", u6.pin("GND"))
    out = u6.pin("OUT")
    s.wire(out, (292.1, out[1]))
    s.cap("C4", "1u", (271.78, out[1]), decouples="U6.1")
    s.power("power:+3V3", (284.48, out[1]))
    s.tp("TP2", "+3V3", (292.1, out[1]))
    s.text("3V3 follows VSYS down: AW20198 inputs stay within VCC + 0.3 V.\n150 mA max.", (231.14, 118.11))
    s.box((228.6, 55.88), (304.8, 132.08), "3V3")

    by = 165.1
    s.wire(b, (b[0] + 2.54, b[1]))
    s.power("round_pendant:VBAT", (b[0] + 2.54, b[1]))
    bt = s.symbol(
        "Connector_Generic:Conn_01x02", "BT1", BAT_VALUE, (45.72, by + 2.54), mirror="y",
        footprint=BAT_FP,
        fields={"Manufacturer": BAT_MFR, "MPN": BAT_MPN, "LCSC": BAT_LCSC},
        ref_at=(25.4, by), value_at=(25.4, by + 2.54), justify="left",
    )
    a, n = bt.pin("1"), bt.pin("2")
    s.text("Molex PicoBlade 1.25 mm socket (the friction-fit \"JST 1.25\" on most small LiPos) for the 403535 (35 mm round) cell. Pin 1 = +. Check the plug's polarity: makers differ.", (20.32, by - 7.62))
    vbat_y = by
    s.wire(a, (a[0] + 7.62, a[1]), (a[0] + 7.62, vbat_y), (208.28, vbat_y))
    s.power("round_pendant:VBAT", (66.04, vbat_y))
    s.power("power:PWR_FLAG", (73.66, vbat_y), value="PWR_FLAG")
    s.cap("C5", "10u", (193.04, vbat_y), fp=C0603, decouples="U5.2")
    s.tp("TP3", "VBAT", (208.28, vbat_y))
    u8 = s.symbol(
        "round_pendant:XB9901A", "U8", "XB9901A", (101.6, by + 25.4),
        footprint="round_pendant:XySemi_DFN-6_1.8x1.4mm",
        fields={"LCSC": "C669687", "MPN": "XB9901A", "Manufacturer": "XySemi"},
        ref_at=(93.98, by + 15.24), value_at=(104.14, by + 15.24),
    )
    r8x = 81.28
    s.res_v("R8", "100R", (r8x, vbat_y), text_left=True)
    vdd = u8.pin("VDD")
    s.wire((r8x, vbat_y + 7.62), (r8x, vdd[1]), vdd)
    c6 = s.symbol(
        "Device:C", "C6", "100n", (r8x - 5.08, vdd[1] + 3.81), footprint=C0402,
        fields=fields("100n") | {"Decouples": "U8.6"},
        ref_at=(r8x - 7.62, vdd[1] + 2.54), value_at=(r8x - 7.62, vdd[1] + 5.08), justify="right",
    )
    s.wire((r8x, vdd[1]), (r8x - 5.08, vdd[1]), c6.pin("1"))
    ng = u8.pin("GND")
    bat_n_y = ng[1] + 2.54
    s.wire(ng, (ng[0], bat_n_y))
    s.wire(n, (n[0] + 2.54, n[1]), (n[0] + 2.54, bat_n_y), (ng[0], bat_n_y))
    s.wire(c6.pin("2"), (c6.pin("2")[0], bat_n_y))
    s.label("BAT_N", (58.42, bat_n_y))
    vm = u8.pin("VM")
    s.wire(vm, (vm[0] + 7.62, vm[1]))
    s.power("power:GND", (vm[0] + 7.62, vm[1]))
    s.text("BAT_N: cell minus. Never pour GND here.", (58.42, bat_n_y + 5.08))
    s.box((15.24, by - 12.7), (129.54, bat_n_y + 15.24), "CELL AND PROTECTION")

    qf = {"LCSC": "C236117", "MPN": "NTZD3155CT1G", "Manufacturer": "onsemi"}
    QFP = "Package_TO_SOT_SMD:SOT-563"
    qp = s.symbol(
        "round_pendant:NTZD3155C", "Q1", "NTZD3155C", (177.8, by + 12.7), unit=2,
        footprint=QFP, fields=qf, ref_at=(184.15, by + 10.16), value_at=(184.15, by + 12.7),
    )
    qn = s.symbol(
        "round_pendant:NTZD3155C", "Q1", "NTZD3155C", (160.02, by + 30.48), unit=1,
        footprint=QFP, fields=qf, ref_at=(166.37, by + 27.94), value_at=(166.37, by + 30.48),
    )
    s.wire(qp.pin("S"), (qp.pin("S")[0], vbat_y))
    s.res_v("R10", "100k", (160.02, vbat_y), text_left=True)
    gate = qp.pin("G")
    s.wire((160.02, vbat_y + 7.62), qn.pin("D"))
    s.wire((160.02, gate[1]), gate)
    g1 = qn.pin("G")
    s.wire(g1, (139.7, g1[1]))
    s.label("VBAT_EN", (139.7, g1[1]), rot=180, **GL)
    s.res_v("R9", "100k", (146.05, g1[1]), text_left=True, to_gnd=True)
    s.power("power:GND", qn.pin("S"))
    dx = 203.2
    d2 = qp.pin("D")
    s.wire(d2, (d2[0], d2[1] + 2.54), (dx, d2[1] + 2.54))
    s.res_v("R11", "100k", (dx, d2[1] + 2.54))
    mid = d2[1] + 10.16
    s.res_v("R12", "100k", (dx, mid), to_gnd=True)
    s.wire((dx, mid), (dx + 15.24, mid))
    s.cap("C7", "100n", (dx + 10.16, mid))
    s.label("VBAT_SENSE", (dx + 15.24, mid), **GL)
    s.box((130.81, by - 12.7), (241.3, by + 58.42), "VBAT SENSE")
    return s


def build_mcu(spec: VariantSpec, libs: SymbolLib) -> Sheet:
    s = Sheet(spec, libs, "mcu", "RP2350A, flash, crystal, accelerometer, peg-less side buttons, top-bezel light sensor")
    Ux, Uy = 180.34, 147.32
    u = s.symbol(
        "round_pendant:RP2350A", "U3", "RP2350A", (Ux, Uy),
        footprint="round_pendant:RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias",
        fields={"LCSC": "C42411118", "MPN": "RP2350A", "Manufacturer": "Raspberry Pi"},
        ref_at=(Ux - 5.08, Uy - 7.62), value_at=(Ux - 5.08, Uy - 5.08),
    )
    rail = 81.28
    for name in ("USB_OTP_VDD", "ADC_AVDD", "QSPI_IOVDD", "IOVDD"):
        p = u.pin(name)
        s.wire(p, (p[0], rail))
    vin = u.pin("VREG_VIN")
    s.wire(vin, (vin[0], rail))
    s.wire((83.82, rail), (vin[0], rail))
    s.power("power:+3V3", (83.82, rail))
    s.wire((vin[0], 86.36), (vin[0] - 6.35, 86.36))
    s.cap("C16", "4.7u", (vin[0] - 6.35, 86.36), fp=C0402S, decouples="U3.49")
    av = u.pin("VREG_AVDD")
    s.res_v("R13", "33R", (av[0], rail))
    s.wire((av[0], rail + 7.62), av)
    s.wire((av[0], 99.06), (av[0] - 7.62, 99.06))
    s.cap("C17", "4.7u", (av[0] - 7.62, 99.06), text_left=True, decouples="U3.46")
    s.label("VREG_AVDD", (av[0], 97.79), rot=90)
    s.power("power:PWR_FLAG", (av[0] - 7.62, 99.06), value="PWR_FLAG")
    serves = [("C8", "1"), ("C9", "11"), ("C10", "20"), ("C11", "30"), ("C12", "38"), ("C13", "53"), ("C14", "44")]
    for i, (ref, pin) in enumerate(serves):
        s.cap(ref, "100n", (88.9 + 8.89 * i, rail), decouples=f"U3.{pin}")
    lx, fb, dv = u.pin("VREG_LX"), u.pin("VREG_FB"), u.pin("DVDD")
    y_lx, y_fb, x1 = 71.12, 88.9, dv[0] + 5.08
    s.wire(lx, (lx[0], y_lx))
    l1 = s.symbol(
        "Device:L", "L1", "3.3u", ((lx[0] + x1) / 2, y_lx), rot=270,
        footprint="round_pendant:L_pol_2016",
        fields={"LCSC": "C42411119", "MPN": "AOTA-B201610S3R3-101-T", "Manufacturer": "Abracon"},
        ref_at=((lx[0] + x1) / 2, y_lx - 5.08), value_at=((lx[0] + x1) / 2, y_lx - 2.54), justify="",
    )
    s.wire((lx[0], y_lx), l1.pin("2"))
    s.wire(l1.pin("1"), (x1, y_lx))
    s.label("VREG_LX", (lx[0], 96.52), rot=90)
    s.wire(fb, (fb[0], y_fb), (x1, y_fb), (x1, y_lx))
    s.wire(dv, (dv[0], y_fb))
    s.wire((x1, y_lx), (x1 + 50.8, y_lx))
    s.power("power:+1V1", (x1 + 50.8, y_lx))
    s.power("power:PWR_FLAG", (x1 + 43.18, y_lx), value="PWR_FLAG")
    t = s.symbol(
        "Connector:TestPoint", "TP4", "1V1", (x1 + 50.8, y_lx + 7.62), rot=180,
        footprint=TP, in_bom=False, fields={"Manufacturer": "", "MPN": "", "LCSC": ""},
        ref_at=(x1 + 53.34, y_lx + 10.16), value_at=(x1 + 53.34, y_lx + 12.7),
    )
    s.wire((x1 + 50.8, y_lx), t.pin("1"))
    s.cap("C18", "4.7u", (x1 + 7.62, y_lx), fp=C0402S, decouples="U3.50")
    s.cap("C19", "4.7u", (x1 + 17.78, y_lx), decouples="U3.23")
    for x, ref, pin in ((x1 + 27.94, "C20", "6"), (x1 + 38.1, "C21", "39")):
        s.cap(ref, "100n", (x, y_lx), decouples=f"U3.{pin}")
    for name in ("VREG_PGND", "GND"):
        s.power("power:GND", u.pin(name))

    used = {
        1: "LIGHT_PWR",
        2: "ACC_SDA",
        3: "ACC_SCL",
        4: "I2C_SDA",
        5: "I2C_SCL",
        6: "LED_SDB",
        10: "ACC_INT",
        11: "BTN",
        12: "CHG",
        13: "PGOOD",
        spec.vbat_en_gpio: "VBAT_EN",
        27: "LIGHT",
    }
    assert len(used) == 12, "vbat_en_gpio clashes with a used GPIO"
    gl = {"I2C_SDA", "I2C_SCL", "LED_SDB", "CHG", "PGOOD", "VBAT_EN"}
    for i in range(30):
        nm = f"GPIO{i}" if i < 26 else f"GPIO{i}/ADC{i - 26}"
        p = u.pin(nm)
        if i in used:
            s.wire(p, (p[0] + 7.62, p[1]))
            if used[i] in gl:
                s.label(used[i], (p[0] + 7.62, p[1]), **GL)
            else:
                s.wire((p[0] + 7.62, p[1]), (p[0] + 22.86, p[1]))
                s.label(used[i], (p[0] + 22.86, p[1]))
        elif i == 26:
            s.wire(p, (p[0] + 7.62, p[1]))
            s.label("VBAT_SENSE", (p[0] + 7.62, p[1]), **GL)
        else:
            s.no_connect(p)

    for nm in ("RUN", "SWCLK", "SWDIO"):
        p = u.pin(nm)
        s.wire(p, (p[0] - 7.62, p[1]))
        s.label(nm, (p[0] - 7.62, p[1]), rot=180)

    dm, dp = u.pin("USB_DM"), u.pin("USB_DP")
    r4 = s.res_h("R14", "27R", (dm[0] - 26.67, dm[1]))
    s.wire(dm, r4.pin("2"))
    s.wire(r4.pin("1"), (r4.pin("1")[0] - 5.08, dm[1]))
    s.label("USB_DM", (r4.pin("1")[0] - 5.08, dm[1]), rot=180, **GL)
    r5 = s.res_h("R15", "27R", (dp[0] - 26.67, dp[1]), text_below=True)
    s.wire(dp, r5.pin("2"))
    s.wire(r5.pin("1"), (r5.pin("1")[0] - 5.08, dp[1]))
    s.label("USB_DP", (r5.pin("1")[0] - 5.08, dp[1]), rot=180, **GL)
    s.label("USB_DM_MCU", (dm[0] - 5.08, dm[1]), rot=180)
    s.label("USB_DP_MCU", (dp[0] - 5.08, dp[1]), rot=180)

    ss = u.pin("~{QSPI_SS}")
    fx, fy = 93.98, ss[1] + 7.62
    u4 = s.symbol(
        "Memory_Flash:W25Q128JVS", "U4", "W25Q128JVPIQ", (fx, fy), mirror="y",
        footprint="round_pendant:WSON-8_6x5mm_P1.27mm_NoEPCopper",
        fields={"LCSC": "C190862", "MPN": "W25Q128JVPIQ", "Manufacturer": "Winbond"},
        ref_at=(fx - 8.89, fy + 13.97), value_at=(fx - 8.89, fy + 16.51), justify="right",
    )
    for fpin, upin, lab in (
        ("1", "~{QSPI_SS}", "QSPI_SS"),
        ("6", "QSPI_SCLK", "QSPI_SCLK"),
        ("5", "QSPI_SD0", "QSPI_SD0"),
        ("2", "QSPI_SD1", "QSPI_SD1"),
        ("3", "QSPI_SD2", "QSPI_SD2"),
        ("7", "QSPI_SD3", "QSPI_SD3"),
    ):
        a, b = u4.pin(fpin), u.pin(upin)
        s.wire(a, b)
        s.label(lab, (a[0] + 2.54, a[1]))
    vcc, gnd = u4.pin("8"), u4.pin("4")
    s.wire(vcc, (vcc[0] - 12.7, vcc[1]))
    s.power("power:+3V3", (vcc[0] - 12.7, vcc[1]))
    s.cap("C22", "100n", (vcc[0] - 12.7, vcc[1]), text_left=True, decouples="U4.8")
    s.power("power:GND", gnd)

    xin, xout = u.pin("XIN"), u.pin("XOUT")
    xa, xb = 111.76, 119.38
    yc = (xin[1] + xout[1]) / 2
    y1 = s.symbol(
        "Device:Crystal_GND24", "Y1", "12MHz", ((xa + xb) / 2, yc),
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
        fields={"LCSC": "C20625731", "MPN": "ABM8-272-T3", "Manufacturer": "Abracon"},
        ref_at=((xa + xb) / 2, xin[1] - 5.08), value_at=((xa + xb) / 2, xin[1] - 2.54), justify="",
    )
    p1, p3 = y1.pin("1"), y1.pin("3")
    s.wire(xin, (p1[0], xin[1]), p1)
    r6 = s.res_h("R17", "1k", (xout[0] - 12.7, xout[1]))
    s.wire(xout, r6.pin("2"))
    s.wire(r6.pin("1"), (p3[0], xout[1]), p3)
    s.power("power:GND", y1.pin("2"))
    s.wire((p1[0], xin[1]), (p1[0] - 7.62, xin[1]))
    s.cap("C23", "15p", (p1[0] - 7.62, xin[1]), text_left=True)
    s.cap("C24", "15p", (p3[0], xout[1]))
    s.box((73.66, 53.34), (266.7, 218.44), "RP2350A, FLASH, CRYSTAL")

    ax, ay = 317.5, 96.52
    u9 = s.symbol(
        "round_pendant:LIS2DW12", "U9", "LIS2DW12", (ax, ay),
        footprint="Package_LGA:LGA-12_2x2mm_P0.5mm",
        fields={"LCSC": "C189624", "MPN": "LIS2DW12TR", "Manufacturer": "STMicroelectronics"},
        ref_at=(ax + 12.7, ay + 5.08), value_at=(ax + 12.7, ay + 7.62),
    )
    vd, vio = u9.pin("VDD"), u9.pin("VDD_IO")
    cs, sa = u9.pin("CS"), u9.pin("SA0")
    sda, scl = u9.pin("SDA"), u9.pin("SCL")
    top = vd[1] - 10.16
    hx = cs[0] - 2.54
    s.wire(vd, (vd[0], top))
    s.wire(vio, (vio[0], top))
    s.wire((hx, top), (vio[0] + 22.86, top))
    s.power("power:+3V3", (hx, top))
    s.cap("C25", "100n", (vio[0] + 5.08, top), decouples="U9.9")
    s.cap("C26", "4.7u", (vio[0] + 13.97, top), decouples="U9.9")
    s.cap("C27", "100n", (vio[0] + 22.86, top), decouples="U9.10")
    s.wire(cs, (hx, cs[1]))
    s.wire(sa, (hx, sa[1]))
    s.wire((hx, top), (hx, sa[1]))
    bx0 = hx - 22.86
    for pin, net, x, ref in ((scl, "ACC_SCL", hx - 5.08, "R19"), (sda, "ACC_SDA", hx - 15.24, "R20")):
        s.wire(pin, (bx0, pin[1]))
        s.label(net, (bx0, pin[1]), rot=180)
        s.res_v(ref, "4.7k", (x, top), text_left=(net == "ACC_SDA"))
        s.power("power:+3V3", (x, top))
        s.wire((x, top + 7.62), (x, pin[1]))
    i1 = u9.pin("INT1")
    s.wire(i1, (i1[0] + 7.62, i1[1]))
    s.label("ACC_INT", (i1[0] + 7.62, i1[1]))
    s.no_connect(u9.pin("INT2"))
    s.power("power:GND", u9.pin("GND"))
    s.no_connect(u9.pin("NC"))
    s.box((271.78, 66.04), (381.0, 132.08), "ACCELEROMETER (WAKE)")

    y = 147.32
    s.label("BTN", (284.48, y), rot=180)
    r = s.res_h("R18", "1k", (284.48, y))
    sw1 = s.symbol(
        "Switch:SW_Push", "SW1", "USER / WAKE", (306.07, y),
        footprint=BTN_FP, fields=BTN_FIELDS, ref_at=(306.07, y - 5.08), value_at=(306.07, y - 2.54), justify="",
    )
    s.wire(r.pin("2"), sw1.pin("1"))
    q = sw1.pin("2")
    s.wire(q, (q[0] + 2.54, q[1]))
    s.power("power:GND", (q[0] + 2.54, q[1]))
    y = 160.02
    s.label("QSPI_SS", (284.48, y), rot=180)
    r = s.res_h("R16", "1k", (284.48, y), text_below=True)
    sw2 = s.symbol(
        "Switch:SW_Push", "SW2", "BOOTSEL", (306.07, y),
        footprint=BTN_FP, fields=BTN_FIELDS, ref_at=(306.07, y + 2.54), value_at=(306.07, y + 5.08), justify="",
    )
    s.wire(r.pin("2"), sw2.pin("1"))
    q = sw2.pin("2")
    s.wire(q, (q[0] + 2.54, q[1]))
    s.power("power:GND", (q[0] + 2.54, q[1]))
    s.box((271.78, 134.62), (381.0, 170.18), "PEG-LESS SIDE BUTTONS (EVQP7J01P)")

    y = 187.96
    for ref, net, x in (("R21", "I2C_SDA", 289.56), ("R22", "I2C_SCL", 320.04)):
        s.res_v(ref, "1k", (x, y - 7.62), text_left=True)
        s.power("power:+3V3", (x, y - 7.62))
        s.wire((x, y), (x + 7.62, y))
        s.label(net, (x + 7.62, y), **GL)
    sdb_x, sdb_y = 353.06, 180.34
    s.label("LED_SDB", (sdb_x - 5.08, sdb_y), rot=180, **GL)
    s.wire((sdb_x - 5.08, sdb_y), (sdb_x + 12.7, sdb_y))
    s.res_v("R31", "100k", (sdb_x, sdb_y), text_left=True, to_gnd=True)
    s.cap("C35", "100n", (sdb_x + 12.7, sdb_y))
    s.box((271.78, 171.45), (381.0, 198.12), "I2C0 PULL-UPS & AW20198 EN")

    y = 213.36
    for ref, net, x in (("TP5", "RUN", 287.02), ("TP8", "GND", 299.72), ("TP6", "SWCLK", 317.5), ("TP7", "SWDIO", 330.2)):
        t = s.symbol(
            "Connector:TestPoint", ref, net, (x, y), footprint=TP, in_bom=False,
            fields={"Manufacturer": "", "MPN": "", "LCSC": ""},
            ref_at=(x + 1.27, y - 6.35), value_at=(x + 1.27, y - 3.81),
        )
        p = t.pin("1")
        if net == "GND":
            s.wire(p, (p[0] + 2.54, p[1]), (p[0] + 2.54, p[1] + 2.54))
            s.power("power:GND", (p[0] + 2.54, p[1] + 2.54))
        else:
            s.wire(p, (p[0], p[1] + 2.54))
            s.label(net, (p[0], p[1] + 2.54), rot=270)
    s.box((271.78, 200.66), (381.0, 228.6), "TEST PADS")

    qx, qy = 116.84, 243.84
    q2 = s.symbol(
        "round_pendant:ALS-PT19", "Q2", "XYC-PT19C-L1", (qx, qy),
        footprint="round_pendant:SENSOR_ALS-PT19",
        fields={"LCSC": "C2693594", "MPN": "XYC-PT19C-L1", "Manufacturer": "NEWOPTO"},
        ref_at=(qx - 5.08, qy - 7.62), value_at=(qx - 5.08, qy + 7.62),
    )
    pc, pe = q2.pin("C"), q2.pin("E")
    s.wire((pc[0] - 12.7, pc[1]), pc)
    s.label("LIGHT_PWR", (pc[0] - 12.7, pc[1]), rot=180)
    rx = pe[0] + 10.16
    cx = pe[0] + 22.86
    lx_lbl = pe[0] + 33.02
    s.wire(pe, (lx_lbl, pe[1]))
    s.res_v("R43", "22k", (rx, pe[1]), to_gnd=True)
    s.cap("C70", "100n", (cx, pe[1]))
    s.label("LIGHT", (lx_lbl, pe[1]))
    s.box((73.66, 223.52), (213.36, 271.78), "AMBIENT LIGHT SENSOR (TOP BEZEL)")
    return s


def build_matrix_sheet(spec: VariantSpec, libs: SymbolLib, drv: DriverSpec, drv_cells: list) -> Sheet:
    """One AW20198QNR QFN-40 and its assigned RGB LEDs (up to 6 triplets x 11 SW = 66 LEDs)."""
    s = Sheet(
        spec, libs,
        f"driver {drv.idx} and matrix",
        f"{drv.uref} AW20198QNR ({drv.i2c_hex}), {len(drv_cells)} RGB LEDs (drivers-aw20198.md)",
        paper="A3",
    )
    Ux, Uy = 83.82, 139.70
    u = s.symbol(
        "round_pendant:AW20198QNR", drv.uref, "AW20198QNR", (Ux, Uy),
        footprint="round_pendant:AW20198_QFN-40-1EP_5x5mm_P0.4mm_EP3.4x3.4mm",
        fields={"LCSC": "C5137654", "MPN": "AW20198QNR", "Manufacturer": "Shanghai Awinic Tech"},
        ref_at=(Ux - 5.08, Uy - 5.08), value_at=(Ux - 5.08, Uy - 2.54),
    )
    pvcc, vcc = u.pin("PVCC"), u.pin("VCC")
    rail = pvcc[1] - 15.24
    x_left = pvcc[0] - (27.94 if drv.bulk_ref else 17.78)
    x_right = vcc[0] + 15.24
    s.power("round_pendant:VSYS", (x_left, rail))
    s.wire((x_left, rail), (x_right, rail))
    s.wire(pvcc, (pvcc[0], rail))
    s.wire(vcc, (vcc[0], rail))
    if drv.bulk_ref:
        s.cap(drv.bulk_ref, "22u", (pvcc[0] - 25.4, rail), fp=C0603, decouples=f"{drv.uref}.5")
    s.cap(f"C{drv.cap_base}", "1u", (pvcc[0] - 15.24, rail), decouples=f"{drv.uref}.5")
    s.cap(f"C{drv.cap_base + 1}", "100n", (pvcc[0] - 6.35, rail), decouples=f"{drv.uref}.5")
    s.cap(f"C{drv.cap_base + 2}", "100n", (vcc[0] + 6.35, rail), decouples=f"{drv.uref}.22")
    s.cap(f"C{drv.cap_base + 3}", "1u", (vcc[0] + 15.24, rail), decouples=f"{drv.uref}.22")

    sda, scl, en, ad0, ad1, iset, sync = (
        u.pin(k) for k in ("SDA", "SCL", "EN", "AD0", "AD1", "ISET", "SYNC")
    )
    lx = sda[0] - 33.02
    sda_x = sda[0] - 10.16
    scl_x = scl[0] - 15.24
    for p, net in ((sda, "I2C_SDA"), (scl, "I2C_SCL"), (en, "LED_SDB")):
        s.wire(p, (lx, p[1]))
        s.label(net, (lx, p[1]), rot=180, **GL)

    def strap_pin(pin_pt, target: str, gx_off: float):
        if target == "SDA":
            s.wire(pin_pt, (sda_x, pin_pt[1]), (sda_x, sda[1]))
        elif target == "SCL":
            s.wire(pin_pt, (scl_x, pin_pt[1]), (scl_x, scl[1]))
        elif target == "GND":
            gx = pin_pt[0] - gx_off
            s.wire(pin_pt, (gx, pin_pt[1]), (gx, pin_pt[1] + 2.54))
            s.power("power:GND", (gx, pin_pt[1] + 2.54))
        elif target == "VSYS":
            vx = pin_pt[0] - gx_off
            s.wire(pin_pt, (vx, pin_pt[1]), (vx, pin_pt[1] - 3.81))
            s.power("round_pendant:VSYS", (vx, pin_pt[1] - 3.81))
        else:
            raise ValueError(target)

    if drv.ad0_strap == drv.ad1_strap and drv.ad0_strap in ("GND", "VSYS"):
        sx = ad0[0] - 5.08
        s.wire(ad0, (sx, ad0[1]), (sx, ad1[1]), ad1)
        if drv.ad0_strap == "GND":
            s.wire((sx, ad1[1]), (sx, ad1[1] + 2.54))
            s.power("power:GND", (sx, ad1[1] + 2.54))
        else:
            s.wire((sx, ad0[1]), (sx, ad0[1] - 3.81))
            s.power("round_pendant:VSYS", (sx, ad0[1] - 3.81))
    else:
        strap_pin(ad0, drv.ad0_strap, 5.08)
        strap_pin(ad1, drv.ad1_strap, 5.08)

    s.wire(iset, (iset[0] - 12.7, iset[1]))
    s.res_v(drv.rset_ref, "30k", (iset[0] - 12.7, iset[1]), text_left=True, to_gnd=True)
    s.no_connect(sync)
    s.power("power:GND", u.pin("GND"))

    used_sws = sorted({c["sw"] for c in drv_cells})
    used_trips = sorted({c["triplet"] for c in drv_cells})
    used_css = {3 * k - off for k in used_trips for off in (0, 1, 2)}

    rx = u.pin("SW1")[0] + 5.08
    for i in range(1, 12):
        p = u.pin(f"SW{i}")
        if i in used_sws:
            s.wire(p, (rx, p[1]))
            s.label(f"SW{drv.idx}_{i}", (rx, p[1]))
        else:
            s.no_connect(p)
    for i in range(1, 19):
        p = u.pin(f"CS{i}")
        if i in used_css:
            s.wire(p, (rx, p[1]))
            s.label(f"CS{drv.idx}_{i}", (rx, p[1]))
        else:
            s.no_connect(p)
    s.box((12.7, 35.56), (144.78, 246.38), f"DRIVER {drv.idx} ({drv.uref}, {drv.i2c_hex})")

    # Draw up to 6 triplets x 11 SW matrix cleanly on A3 right half (x = 170..345, y = 55..230).
    cell_by_key = {(c["triplet"], c["sw"]): c for c in drv_cells}
    mx, my, dx, dy = 170.18, 58.42, 15.24, 25.4
    for row_idx, k in enumerate(used_trips):
        y = my + row_idx * dy
        yr, yg, yb = y + 6.35, y + 8.89, y + 11.43
        row_sws = [m for m in used_sws if (k, m) in cell_by_key]
        max_col_idx = used_sws.index(max(row_sws))
        last_x = mx + max_col_idx * dx
        # AW20198 RGB mapping (p. 5 Fig. 5): CS(3k-2)=R (pin 1), CS(3k-1)=G (pin 2), CS(3k)=B (pin 4).
        for yy, cs_num, off in ((yr, 3 * k - 2, -2.54), (yg, 3 * k - 1, 0.0), (yb, 3 * k, 2.54)):
            s.wire((mx - 10.16, yy), (last_x + off, yy))
            s.label(f"CS{drv.idx}_{cs_num}", (mx - 10.16, yy), rot=180)
        for col_idx, sw_m in enumerate(used_sws):
            cell = cell_by_key.get((k, sw_m))
            if not cell:
                continue
            x = mx + col_idx * dx
            if spec.led_type == "XL-1615RGBC":
                led = s.symbol(
                    "round_pendant:XL-1615RGBC", cell["ref"], "RGB", (x, y),
                    footprint="round_pendant:LED_XL-1615RGBC",
                    fields={
                        "LCSC": "C965840",
                        "MPN": "XL-1615RGBC-RF",
                        "Manufacturer": "XINGLIGHT",
                        "Cell": f"{drv.uref} SW{sw_m} / triplet {k} (col {cell['col']}, row {cell['row']})",
                    },
                    ref_at=(x + 1.27, y - 5.08), value_at=(x, y), justify="",
                )
                # xl-1615rgbc-rf.pdf p. 8: Pin 1=R, Pin 2=Common Anode (+), Pin 3=G, Pin 4=B
                pr, pg, pb, pa = led.pin("1"), led.pin("3"), led.pin("4"), led.pin("2")
            else:
                led = s.symbol(
                    "round_pendant:XL-1010RGB", cell["ref"], "RGB", (x, y),
                    footprint="round_pendant:LED_XL-1010RGB",
                    fields={
                        "LCSC": "C965834",
                        "MPN": "XL-1010RGB-YG",
                        "Manufacturer": "XINGLIGHT",
                        "Cell": f"{drv.uref} SW{sw_m} / triplet {k} (col {cell['col']}, row {cell['row']})",
                    },
                    ref_at=(x + 1.27, y - 5.08), value_at=(x, y), justify="",
                )
                # xl-1010rgb-yg.pdf p. 8: Pin 1=R, Pin 2=G, Pin 3=Common Anode (+), Pin 4=B
                pr, pg, pb, pa = led.pin("1"), led.pin("2"), led.pin("4"), led.pin("3")
            s.wire(pr, (pr[0], yr))
            s.wire(pg, (pg[0], yg))
            s.wire(pb, (pb[0], yb))
            s.wire(pa, (pa[0], pa[1] - 1.27), (x - 5.08, pa[1] - 1.27))

    for col_idx, sw_m in enumerate(used_sws):
        x = mx + col_idx * dx - 5.08
        top_y = my - 8.89
        last_row_idx = max(idx_r for idx_r, k in enumerate(used_trips) if (k, sw_m) in cell_by_key)
        s.wire((x, top_y), (x, my + last_row_idx * dy - 6.35))
        s.label(f"SW{drv.idx}_{sw_m}", (x, top_y), rot=90)
    s.box((149.86, 35.56), (355.60, 246.38), f"{len(drv_cells)} RGB LEDS: R=CS(3k-2), G=CS(3k-1), B=CS(3k)")
    return s


def child_save(sheet: Sheet, path: Path, root_uuid: str, sheet_uuid: str):
    sheet.save(path)
    t = path.read_text()
    t = t.replace(f'(path "/{sheet.uuid}"', f'(path "/{root_uuid}/{sheet_uuid}"')
    t = re.sub(r'\n?\s*\(sheet_instances\s*\(path "/"\s*\(page "1"\)\s*\)\s*\)', "", t)
    path.write_text(t)


def sheet_node(name, file, uuid, at, size, page, root_uuid):
    def p(k, v, y):
        return S(
            "property", k, v, S("at", at[0], y, 0),
            [Sym("effects"), S("font", S("size", 1.27, 1.27)), [Sym("justify"), Sym("left"), Sym("bottom")]],
        )

    return [
        Sym("sheet"),
        S("at", at[0], at[1]),
        S("size", size[0], size[1]),
        S("exclude_from_sim", yes(False)),
        S("in_bom", yes(True)),
        S("on_board", yes(True)),
        S("dnp", yes(False)),
        S("fields_autoplaced", yes(True)),
        S("stroke", S("width", 0.1524), S("type", Sym("solid"))),
        S("fill", S("color", 0, 0, 0, 0.0)),
        S("uuid", uuid),
        p("Sheetname", name, at[1] - 0.7),
        p("Sheetfile", file, at[1] + size[1] + 1.8),
        S("instances", S("project", PROJECT, S("path", "/" + root_uuid, S("page", str(page))))),
    ]


def generate_schematics(variant_name: str):
    spec = VARIANTS[variant_name]
    hw = spec.hw_dir
    libs = SymbolLib([hw / "lib/round_pendant.kicad_sym"])
    cells = build_led_cells(spec)

    root = Sheet(spec, libs, "top", spec.summary, paper="A4")
    sheets = [
        ("Power", "power.kicad_sch", build_power(spec, libs)),
        ("MCU", "mcu.kicad_sch", build_mcu(spec, libs)),
    ]
    for drv in spec.drivers:
        drv_cells = [c for c in cells if c["drv_idx"] == drv.idx]
        sheets.append((
            f"Driver {drv.idx} and matrix",
            f"matrix{drv.idx}.kicad_sch",
            build_matrix_sheet(spec, libs, drv, drv_cells),
        ))

    places = [
        ((20.32, 35.56), (48.26, 43.18)),
        ((83.82, 35.56), (48.26, 43.18)),
        ((149.86, 25.4), (58.42, 20.32)),
        ((149.86, 53.34), (58.42, 20.32)),
        ((149.86, 81.28), (58.42, 20.32)),
        ((149.86, 109.22), (58.42, 20.32)),
    ]
    nodes = []
    for i, ((name, file, sh), (at, size)) in enumerate(zip(sheets, places)):
        u = new_uuid()
        child_save(sh, hw / file, root.uuid, u)
        nodes.append(sheet_node(name, file, u, at, size, i + 2, root.uuid))

    root.text(
        f"Sunflower 4-layer density study ({spec.name}): {spec.summary}.\n"
        "38 mm round board, Vogel-spiral LED field, 35 mm round LiPo cell behind the board.\n"
        "Solid GND thermal pads on U3, U5, and all AW20198QNR QFN-40 drivers (0 via-in-pad).",
        (20.32, 105.0),
    )
    path = hw / f"{PROJECT}.kicad_sch"
    root._cleanup()
    tree = [
        Sym("kicad_sch"),
        S("version", Sym("20250114")),
        S("generator", "eeschema"),
        S("generator_version", "9.0"),
        S("uuid", root.uuid),
        S("paper", root.paper),
        [Sym("title_block"), *[t for t in root.title if t[-1] != ""]],
        [Sym("lib_symbols")],
        *root.items,
        *nodes,
        S("sheet_instances", S("path", "/", S("page", "1"))),
        S("embedded_fonts", yes(False)),
    ]
    path.write_text(dump(tree) + "\n")
    print(f"wrote schematics for {variant_name}: {path} ({spec.n_leds} LEDs, {len(spec.drivers)} drivers)")


if __name__ == "__main__":
    generate_schematics(sys.argv[1])
