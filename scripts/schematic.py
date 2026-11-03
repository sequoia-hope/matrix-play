#!/usr/bin/env python3
"""schematic.py -- draw the round-pendant schematic: a root sheet and four child sheets.

    python3 scripts/symbols.py && python3 scripts/schematic.py

This script is the schematic's source. Edit it, re-run it, then check with
`kicad-cli sch erc` and the exported PDF. Every value comes from design/parts/.

  power.kicad_sch    USB-C, charger and power path, protection, LDO, VBAT sense
  mcu.kicad_sch      RP2350A, flash, crystal, buttons, accelerometer, test points
  matrix1/2.kicad_sch  one IS31FL3741A and its 13 x 9 matrix each

The matrices are drawn as matrices: that is what they are (decisions.md waives the
style check's grid rule for these two sheets). Each LED's position on the board is
set at placement; references here are only cell order.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude/skills/pcb-design/scripts"))
from kicad_write import S, Schematic, Sym, SymbolLib, dump, new_uuid, yes  # noqa: E402

import os
VARIANT = os.environ.get("PENDANT_VARIANT", "a")
HW = ROOT / f"hw/round-pendant/{VARIANT}"
PROJECT = "round-pendant"
LIBS = SymbolLib([HW / "lib/round_pendant.kicad_sym"])
DATE = "2026-11-02"

C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0402S = "round_pendant:C_0402_1005Metric_small_pads"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
TP = "TestPoint:TestPoint_Pad_D1.0mm"

PARTS = {
    "100n": ("C1525", "CL05B104KO5NNNC", "Samsung Electro-Mechanics"),
    "1u": ("C52923", "CL05A105KA5NQNC", "Samsung Electro-Mechanics"),
    "4.7u": ("C23733", "CL05A475MP5NRNC", "Samsung Electro-Mechanics"),
    "10u": ("C19702", "CL10A106KP8NNNC", "Samsung Electro-Mechanics"),
    "22u": ("C86295", "CL10A226MP8NUNE", "Samsung Electro-Mechanics"),
    "15p": ("C1548", "0402CG150J500NT", "FH"),
    "27R": ("C25100", "0402WGF270JTCE", "UNI-ROYAL"),
    "33R": ("C25105", "0402WGF330JTCE", "UNI-ROYAL"),
    "470R": ("C25117", "0402WGF4700TCE", "UNI-ROYAL"),
    "100R": ("C25076", "0402WGF1000TCE", "UNI-ROYAL"),
    "1k": ("C11702", "0402WGF1001TCE", "UNI-ROYAL"),
    "3k": ("C25784", "0402WGF3001TCE", "UNI-ROYAL"),
    "3.6k": ("C25891", "0402WGF3601TCE", "UNI-ROYAL"),
    "4.7k": ("C25900", "0402WGF4701TCE", "UNI-ROYAL"),
    "5.1k": ("C25905", "0402WGF5101TCE", "UNI-ROYAL"),
    "10k": ("C25744", "0402WGF1002TCE", "UNI-ROYAL"),
    "30k": ("C25776", "0402WGF3002TCE", "UNI-ROYAL"),
    "100k": ("C25741", "0402WGF1003TCE", "UNI-ROYAL"),
}
GL = dict(kind="global_label")


def fields(value):
    lcsc, mpn, mfr = PARTS[value]
    return {"LCSC": lcsc, "MPN": mpn, "Manufacturer": mfr}


class Sheet(Schematic):
    def __init__(self, title, comment, paper="A3"):
        super().__init__(PROJECT, title="round-pendant: " + title, rev="A", date=DATE,
                         company="CERN-OHL-P-2.0", comments=[comment, "Drawn by scripts/schematic.py"],
                         paper=paper, libs=LIBS)

    def cap(self, ref, value, top, fp=C0402, text_left=False, decouples=None):
        x, y = top
        dx = -2.54 if text_left else 2.54
        j = "right" if text_left else "left"
        f = fields(value) | ({"Decouples": decouples} if decouples else {})
        c = self.symbol("Device:C", ref, value, (x, y + 3.81), footprint=fp, fields=f,
                        ref_at=(x + dx, y + 2.54), value_at=(x + dx, y + 5.08), justify=j)
        self.power("power:GND", (x, y + 7.62))
        return c

    def res_v(self, ref, value, top, text_left=False, to_gnd=False):
        x, y = top
        dx = -2.54 if text_left else 2.54
        j = "right" if text_left else "left"
        r = self.symbol("Device:R", ref, value, (x, y + 3.81), footprint=R0402, fields=fields(value),
                        ref_at=(x + dx, y + 2.54), value_at=(x + dx, y + 5.08), justify=j)
        if to_gnd:
            self.power("power:GND", (x, y + 7.62))
        return r

    def res_h(self, ref, value, left, text_below=False):
        x, y = left
        ty = (y + 2.54, y + 5.08) if text_below else (y - 5.08, y - 2.54)
        return self.symbol("Device:R", ref, value, (x + 3.81, y), rot=90, footprint=R0402, fields=fields(value),
                           ref_at=(x + 3.81, ty[0]), value_at=(x + 3.81, ty[1]), justify="")

    def tp(self, ref, net, at):
        """A test pad hanging below `at`, which is on the net."""
        t = self.symbol("Connector:TestPoint", ref, net, (at[0], at[1] + 2.54), rot=180, footprint=TP, in_bom=False,
                        fields={"Manufacturer": "", "MPN": "", "LCSC": ""},
                        ref_at=(at[0] + 2.54, at[1] + 5.08), value_at=(at[0] + 2.54, at[1] + 7.62))
        self.wire(at, t.pin("1"))
        return t


# ---------------------------------------------------------------- power sheet

BTN_FP = "Button_Switch_SMD:SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010" if VARIANT == "a" else "round_pendant:SW_Panasonic_EVQP7C"
BTN_FIELDS = {"LCSC": "C110293", "MPN": "SKRTLAE010", "Manufacturer": "ALPSALPINE"} if VARIANT == "a" else {"LCSC": "C388883", "MPN": "EVQP7C01P", "Manufacturer": "PANASONIC"}


def power() -> Sheet:
    s = Sheet("power", "USB-C, charger, protection, LDO, VBAT sense")
    if VARIANT != "a":
        # Off-board USB-C: wire pads. Rd stays here, so a bare receptacle works.
        j1 = s.symbol("round_pendant:USB_Pads", "J1", "USB wires", (40.64, 93.98), fields={"MPN": "none, wire pads"},
                      ref_at=(30.48, 81.28), value_at=(30.48, 83.82))
        vbus_y = 68.58
        px = j1.pin("5")[0]
        s.wire(j1.pin("5"), (px + 2.54, j1.pin("5")[1]), (px + 2.54, vbus_y), (64.77, vbus_y))
        g = j1.pin("6")
        s.wire(g, (g[0] + 2.54, g[1]), (g[0] + 2.54, g[1] + 7.62))
        s.power("power:GND", (g[0] + 2.54, g[1] + 7.62))
        s.power("power:PWR_FLAG", (g[0] + 7.62, g[1] + 7.62), rot=180, value="PWR_FLAG")
        s.wire((g[0] + 2.54, g[1] + 7.62), (g[0] + 7.62, g[1] + 7.62))
        for pin, net, x, ref in (("1", "CC1", 60.96, "R1"), ("2", "CC2", 71.12, "R2")):
            p = j1.pin(pin)
            s.wire(p, (x, p[1]), (x, 104.14))
            s.label(net, (p[0] + 7.62, p[1]))
            s.res_v(ref, "5.1k", (x, 104.14), to_gnd=True)
    else:
        # J1
        j1 = s.symbol("Connector:USB_C_Receptacle_USB2.0_16P", "J1", "USB-C", (40.64, 88.9),
                      footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
                      fields={"LCSC": "C165948", "MPN": "TYPE-C-31-M-12", "Manufacturer": "Korean Hroparts Elec"},
                      ref_at=(30.48, 66.04), value_at=(30.48, 68.58))
        vbus_y = 68.58
        s.wire(j1.pin("A4"), (64.77, j1.pin("A4")[1]), (64.77, vbus_y))
        s.wire(j1.pin("A7"), (58.42, j1.pin("A7")[1]), (58.42, j1.pin("B7")[1]))
        s.wire(j1.pin("A6"), (58.42, j1.pin("A6")[1]), (58.42, j1.pin("B6")[1]), j1.pin("B6"))
        for sbu in ("A8", "B8"):
            s.no_connect(j1.pin(sbu))
        g, sh = j1.pin("A1"), j1.pin("S1")
        s.wire(sh, (sh[0], sh[1] + 2.54), (g[0], sh[1] + 2.54))
        s.wire(g, (g[0], g[1] + 2.54))
        s.power("power:GND", (g[0], g[1] + 2.54))
        s.power("power:PWR_FLAG", (g[0] + 10.16, g[1] + 2.54), rot=180, value="PWR_FLAG")
        s.wire((g[0], g[1] + 2.54), (g[0] + 10.16, g[1] + 2.54))
        s.text("Shield straight to GND", (20.32, g[1] + 8.89))
        for pin, net, x, ref in (("A5", "CC1", 60.96, "R1"), ("B5", "CC2", 71.12, "R2")):
            p = j1.pin(pin)
            s.wire(p, (x, p[1]), (x, 104.14))
            s.label(net, (p[0] + 1.27, p[1]))
            s.res_v(ref, "5.1k", (x, 104.14), to_gnd=True)
    # ESD array in line.
    u7 = s.symbol("Power_Protection:USBLC6-2P6", "U7", "USBLC6-2P6", (86.36, 88.9),
                  footprint="Package_TO_SOT_SMD:SOT-666",
                  fields={"LCSC": "C15999", "MPN": "USBLC6-2P6", "Manufacturer": "STMicroelectronics"},
                  ref_at=(90.17, 99.06), value_at=(90.17, 101.6))
    if VARIANT != "a":
        for pin, u, jog in (("3", "1", 5.08), ("4", "3", 7.62)):
            q, v = j1.pin(pin), u7.pin(u)
            s.wire(q, (q[0] + jog, q[1]), (q[0] + jog, v[1]), v)
    else:
        s.wire(j1.pin("B7"), u7.pin("1"))
        s.wire(j1.pin("A6"), u7.pin("3"))
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
    s.box((15.24, 55.88), (110.49, 132.08), "USB-C, ESD" if VARIANT == "a" else "USB WIRES, ESD")

    # Charger.
    u5x, u5y = 160.02, 86.36
    u5 = s.symbol("round_pendant:BQ24073", "U5", "BQ24073", (u5x, u5y),
                  fields={"LCSC": "C15220", "MPN": "BQ24073RGTR", "Manufacturer": "Texas Instruments"},
                  footprint="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm",
                  ref_at=(u5x - 8.89, u5y - 19.05), value_at=(u5x + 8.89, u5y - 19.05))
    i = u5.pin("IN")
    s.wire((121.92, vbus_y), (121.92, i[1]), i)
    s.cap("C1", "1u", (116.84, vbus_y), decouples="U5.13")
    # EN1 high, EN2 low: USB500 (charger.md).
    en1, en2, ce, td = u5.pin("EN1"), u5.pin("EN2"), u5.pin("CE"), u5.pin("TD")
    s.wire(en1, (en1[0] - 7.62, en1[1]))
    s.power("power:+3V3", (en1[0] - 7.62, en1[1]))
    gx = en1[0] - 2.54
    s.wire(en2, (gx, en2[1]))
    s.wire(ce, (gx, ce[1]))
    s.wire(td, (gx, td[1]))
    s.wire((gx, en2[1]), (gx, td[1] + 1.27))
    s.power("power:GND", (gx, td[1] + 1.27))
    # TS, ISET, ILIM to ground on their own pins, fanned out left.
    for pin, ref, val, x in (("TS", "R3", "10k", 119.38), ("ISET", "R4", "3k", 129.54), ("ILIM", "R5", "3.6k", 139.7)):
        p = u5.pin(pin)
        s.wire(p, (x, p[1]))
        s.res_v(ref, val, (x, p[1]), text_left=True, to_gnd=True)
    s.no_connect(u5.pin("TMR"))
    s.text("USB500: 450-500 mA in. 297 mA charge, ILIM must not float.\nTMR open: default 5 h. TS fixed: no NTC.", (116.84, 124.46))
    s.power("power:GND", u5.pin("VSS"))
    # Status, pulled to 3V3 at the charger. CHG's wire crosses PGOOD's.
    pg, ch = u5.pin("~{PGOOD}"), u5.pin("~{CHG}")
    for p, net in ((pg, "PGOOD"), (ch, "CHG")):
        s.wire(p, (205.74, p[1]))
        s.label(net, (205.74, p[1]), **GL)
    s.res_v("R6", "100k", (198.12, pg[1] - 7.62))
    s.power("power:+3V3", (198.12, pg[1] - 7.62))
    s.res_v("R7", "100k", (187.96, pg[1] - 10.16), text_left=True)
    s.power("power:+3V3", (187.96, pg[1] - 10.16))
    s.wire((187.96, pg[1] - 2.54), (187.96, ch[1]))
    # OUT is VSYS; BAT goes on to the cell.
    o, b = u5.pin("OUT"), u5.pin("BAT")
    vsys_y = o[1]
    s.wire(o, (228.6, vsys_y))
    s.power("round_pendant:VSYS", (205.74, vsys_y))
    s.cap("C2", "22u", (213.36, vsys_y), fp=C0603, text_left=True, decouples="U5.10")
    s.tp("TP1", "VSYS", (218.44, vsys_y))
    s.box((111.76, 55.88), (227.33, 132.08), "CHARGER AND POWER PATH")

    # LDO.
    u6 = s.symbol("round_pendant:TPS7A0233", "U6", "TPS7A0233", (254.0, vsys_y + 2.54),
                  footprint="Package_SON:Texas_X2SON-4_1x1mm_P0.65mm",
                  fields={"LCSC": "C2860046", "MPN": "TPS7A0233PDQNR", "Manufacturer": "Texas Instruments"},
                  ref_at=(246.38, vsys_y - 7.62), value_at=(246.38, vsys_y - 5.08))
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
    s.text("3V3 only ever follows VSYS down: the driver inputs\nstay within VCC + 0.3 V (drivers.md). 150 mA max.", (231.14, 118.11))
    s.box((228.6, 55.88), (304.8, 132.08), "3V3")

    # Battery and protection, under the charger.
    by = 165.1
    s.wire(b, (b[0] + 2.54, b[1]))
    s.power("round_pendant:VBAT", (b[0] + 2.54, b[1]))
    bt = s.symbol("Connector_Generic:Conn_01x02", "BT1", "CELL 5435035", (45.72, by + 2.54), mirror="y",
                  footprint="round_pendant:BatteryPads", in_bom=False, fields={"Manufacturer": "Grepow", "MPN": "5435035", "LCSC": ""},
                  ref_at=(25.4, by), value_at=(25.4, by + 2.54), justify="left")
    a, n = bt.pin("1"), bt.pin("2")
    s.text("Hand-soldered leads. 610 mAh listed, charged to 4.2 V (battery.md)", (20.32, by - 7.62))
    vbat_y = by
    s.wire(a, (a[0] + 7.62, a[1]), (a[0] + 7.62, vbat_y), (208.28, vbat_y))
    s.power("round_pendant:VBAT", (66.04, vbat_y))
    s.power("power:PWR_FLAG", (73.66, vbat_y), value="PWR_FLAG")
    s.cap("C5", "10u", (193.04, vbat_y), fp=C0603, decouples="U5.2")
    s.tp("TP3", "VBAT", (208.28, vbat_y))
    # XB9901A: low-side. Cell minus (BAT_N) is NOT board ground.
    u8 = s.symbol("round_pendant:XB9901A", "U8", "XB9901A", (101.6, by + 25.4),
                  footprint="round_pendant:XySemi_DFN-6_1.8x1.4mm",
                  fields={"LCSC": "C669687", "MPN": "XB9901A", "Manufacturer": "XySemi"},
                  ref_at=(93.98, by + 15.24), value_at=(104.14, by + 15.24))
    r8x = 81.28
    s.res_v("R8", "100R", (r8x, vbat_y), text_left=True)
    vdd = u8.pin("VDD")
    s.wire((r8x, vbat_y + 7.62), (r8x, vdd[1]), vdd)
    c6 = s.symbol("Device:C", "C6", "100n", (r8x - 5.08, vdd[1] + 3.81), footprint=C0402,
                  fields=fields("100n") | {"Decouples": "U8.6"},
                  ref_at=(r8x - 7.62, vdd[1] + 2.54), value_at=(r8x - 7.62, vdd[1] + 5.08), justify="right")
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
    s.text("BAT_N: cell minus. Pins 4, 5 and the pad. Never pour GND here,\nor protection is bypassed (protection.md).", (58.42, bat_n_y + 5.08))
    s.box((15.24, by - 12.7), (129.54, bat_n_y + 15.24), "CELL AND PROTECTION")

    # Switched VBAT sense: N pulls the P gate down; P feeds the divider.
    qf = {"LCSC": "C236117", "MPN": "NTZD3155CT1G", "Manufacturer": "onsemi"}
    QFP = "Package_TO_SOT_SMD:SOT-563"
    qp = s.symbol("round_pendant:NTZD3155C", "Q1", "NTZD3155C", (177.8, by + 12.7), unit=2, footprint=QFP, fields=qf,
                  ref_at=(184.15, by + 10.16), value_at=(184.15, by + 12.7))
    qn = s.symbol("round_pendant:NTZD3155C", "Q1", "NTZD3155C", (160.02, by + 30.48), unit=1, footprint=QFP, fields=qf,
                  ref_at=(166.37, by + 27.94), value_at=(166.37, by + 30.48))
    s.wire(qp.pin("S"), (qp.pin("S")[0], vbat_y))
    # P gate: pulled up to VBAT by R10, down by the N drain.
    s.res_v("R10", "100k", (160.02, vbat_y), text_left=True)
    gate = qp.pin("G")
    s.wire((160.02, vbat_y + 7.62), qn.pin("D"))
    s.wire((160.02, gate[1]), gate)
    # N gate: VBAT_EN, held low by R9 when the MCU is off.
    g1 = qn.pin("G")
    s.wire(g1, (139.7, g1[1]))
    s.label("VBAT_EN", (139.7, g1[1]), rot=180, **GL)
    s.res_v("R9", "100k", (146.05, g1[1]), text_left=True, to_gnd=True)
    s.power("power:GND", qn.pin("S"))
    # Divider off the P drain.
    dx = 203.2
    d2 = qp.pin("D")
    s.wire(d2, (d2[0], d2[1] + 2.54), (dx, d2[1] + 2.54))
    s.res_v("R11", "100k", (dx, d2[1] + 2.54))
    mid = d2[1] + 10.16
    s.res_v("R12", "100k", (dx, mid), to_gnd=True)
    s.wire((dx, mid), (dx + 15.24, mid))
    s.cap("C7", "100n", (dx + 10.16, mid))
    s.label("VBAT_SENSE", (dx + 15.24, mid), **GL)
    s.text("Zero draw off. ADC reads true only while 3V3 regulates,\nVBAT >= 3.5 V (intent R22). Wait >= 5 ms after enabling.", (139.7, by + 52.07))
    s.box((130.81, by - 12.7), (241.3, by + 58.42), "VBAT SENSE")
    return s


# ---------------------------------------------------------------- MCU sheet

def mcu() -> Sheet:
    s = Sheet("mcu", "RP2350A, flash, crystal, accelerometer, buttons")
    Ux, Uy = 180.34, 147.32
    u = s.symbol("round_pendant:RP2350A", "U3", "RP2350A", (Ux, Uy),
                 footprint="round_pendant:RP2350-QFN-60-1EP_7x7_P0.4mm_EP3.4x3.4mm_ThermalVias",
                 fields={"LCSC": "C42411118", "MPN": "RP2350A", "Manufacturer": "Raspberry Pi"},
                 ref_at=(Ux - 5.08, Uy - 7.62), value_at=(Ux - 5.08, Uy - 5.08))
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
    s.text("100 nF at IOVDD pins 1, 11, 20, 30, 38 (C8-C12), USB_OTP_VDD 53\nand QSPI_IOVDD 54 (C13), ADC_AVDD 44 and IOVDD 45 (C14).", (83.82, 66.04))
    lx, fb, dv = u.pin("VREG_LX"), u.pin("VREG_FB"), u.pin("DVDD")
    y_lx, y_fb, x1 = 71.12, 88.9, dv[0] + 5.08
    s.wire(lx, (lx[0], y_lx))
    l1 = s.symbol("Device:L", "L1", "3.3u", ((lx[0] + x1) / 2, y_lx), rot=270, footprint="round_pendant:L_pol_2016",
                  fields={"LCSC": "C42411119", "MPN": "AOTA-B201610S3R3-101-T", "Manufacturer": "Abracon"},
                  ref_at=((lx[0] + x1) / 2, y_lx - 5.08), value_at=((lx[0] + x1) / 2, y_lx - 2.54), justify="")
    s.wire((lx[0], y_lx), l1.pin("2"))
    s.wire(l1.pin("1"), (x1, y_lx))
    s.label("VREG_LX", (lx[0], 96.52), rot=90)
    s.wire(fb, (fb[0], y_fb), (x1, y_fb), (x1, y_lx))
    s.wire(dv, (dv[0], y_fb))
    s.wire((x1, y_lx), (x1 + 50.8, y_lx))
    s.power("power:+1V1", (x1 + 50.8, y_lx))
    s.power("power:PWR_FLAG", (x1 + 43.18, y_lx), value="PWR_FLAG")
    t = s.symbol("Connector:TestPoint", "TP4", "1V1", (x1 + 50.8, y_lx + 7.62), rot=180, footprint=TP, in_bom=False,
                 fields={"Manufacturer": "", "MPN": "", "LCSC": ""}, ref_at=(x1 + 53.34, y_lx + 10.16), value_at=(x1 + 53.34, y_lx + 12.7))
    s.wire((x1 + 50.8, y_lx), t.pin("1"))
    s.cap("C18", "4.7u", (x1 + 7.62, y_lx), fp=C0402S, decouples="U3.50")
    s.cap("C19", "4.7u", (x1 + 17.78, y_lx), decouples="U3.23")
    for x, ref, pin in ((x1 + 27.94, "C20", "6"), (x1 + 38.1, "C21", "39")):
        s.cap(ref, "100n", (x, y_lx), decouples=f"U3.{pin}")
    s.text("C18 COUT at L1; C19 at DVDD 23;\nC20, C21 at DVDD 6, 39", (x1 + 5.08, y_lx - 10.16))
    s.text("Regulator: C16 CIN, C18 COUT, L1's polarity and copper\nfollow chips/rp2350.md", (lx[0] - 38.1, 55.88))
    for name in ("VREG_PGND", "GND"):
        s.power("power:GND", u.pin(name))
    s.text("VREG_PGND joins GND at one point", (Ux - 15.24, 200.66))

    # GPIO to the right, by what they do.
    used = {2: "ACC_SDA", 3: "ACC_SCL", 4: "I2C_SDA", 5: "I2C_SCL", 6: "SDB1", 7: "SDB2", 8: "INTB1", 9: "INTB2",
            10: "ACC_INT", 11: "BTN", 12: "CHG", 13: "PGOOD", 14: "VBAT_EN"}
    if VARIANT == "c":
        used.update({23: "CLED_R", 24: "CLED_G", 25: "CLED_B"})
    gl = {"I2C_SDA", "I2C_SCL", "SDB1", "SDB2", "INTB1", "INTB2", "CHG", "PGOOD", "VBAT_EN"}
    px = None
    for i in range(30):
        nm = f"GPIO{i}" if i < 26 else f"GPIO{i}/ADC{i - 26}"
        p = u.pin(nm)
        px = p[0]
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
    # I2C0 pull-ups live here, at the master.
    s.text("I2C0 to both drivers, 1 MHz:\n12 mA drive, LGC = 1 (drivers.md).\nUnused GPIOs are left open; firmware\nclears latched pull-downs before\nsleep on GPIO 2-5, 8, 9, 12, 13, 26.", (218.44, 91.44))
    # RUN and SWD go to the test pads block.
    for nm in ("RUN", "SWCLK", "SWDIO"):
        p = u.pin(nm)
        s.wire(p, (p[0] - 7.62, p[1]))
        s.label(nm, (p[0] - 7.62, p[1]), rot=180)
    # USB.
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

    # Flash.
    ss = u.pin("~{QSPI_SS}")
    fx, fy = 93.98, ss[1] + 7.62
    u4 = s.symbol("Memory_Flash:W25Q128JVS", "U4", "W25Q128JVPIQ", (fx, fy), mirror="y",
                  footprint="round_pendant:WSON-8_6x5mm_P1.27mm_NoEPCopper",
                  fields={"LCSC": "C190862", "MPN": "W25Q128JVPIQ", "Manufacturer": "Winbond"},
                  ref_at=(fx - 8.89, fy + 13.97), value_at=(fx - 8.89, fy + 16.51), justify="right")
    for fpin, upin, lab in (("1", "~{QSPI_SS}", "QSPI_SS"), ("6", "QSPI_SCLK", "QSPI_SCLK"), ("5", "QSPI_SD0", "QSPI_SD0"),
                            ("2", "QSPI_SD1", "QSPI_SD1"), ("3", "QSPI_SD2", "QSPI_SD2"), ("7", "QSPI_SD3", "QSPI_SD3")):
        a, b = u4.pin(fpin), u.pin(upin)
        assert abs(a[1] - b[1]) < 1e-6, (fpin, a, b)
        s.wire(a, b)
        s.label(lab, (a[0] + 2.54, a[1]))
    vcc, gnd = u4.pin("8"), u4.pin("4")
    s.wire(vcc, (vcc[0] - 12.7, vcc[1]))
    s.power("power:+3V3", (vcc[0] - 12.7, vcc[1]))
    s.cap("C22", "100n", (vcc[0] - 12.7, vcc[1]), text_left=True, decouples="U4.8")
    s.power("power:GND", gnd)
    s.text("Flash pad: float (no internal connection)", (fx - 27.94, fy + 30.48))
    # Crystal.
    xin, xout = u.pin("XIN"), u.pin("XOUT")
    xa, xb = 111.76, 119.38
    yc = (xin[1] + xout[1]) / 2
    y1 = s.symbol("Device:Crystal_GND24", "Y1", "12MHz", ((xa + xb) / 2, yc),
                  footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
                  fields={"LCSC": "C20625731", "MPN": "ABM8-272-T3", "Manufacturer": "Abracon"},
                  ref_at=((xa + xb) / 2, xin[1] - 5.08), value_at=((xa + xb) / 2, xin[1] - 2.54), justify="")
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

    # Accelerometer.
    ax, ay = 317.5, 96.52
    u9 = s.symbol("round_pendant:LIS2DW12", "U9", "LIS2DW12", (ax, ay), footprint="Package_LGA:LGA-12_2x2mm_P0.5mm",
                  fields={"LCSC": "C189624", "MPN": "LIS2DW12TR", "Manufacturer": "STMicroelectronics"},
                  ref_at=(ax + 12.7, ay + 5.08), value_at=(ax + 12.7, ay + 7.62))
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
    # CS and SA0 high: their ~20 k internal pull-ups draw nothing tied high (accel.md).
    s.wire(cs, (hx, cs[1]))
    s.wire(sa, (hx, sa[1]))
    s.wire((hx, top), (hx, sa[1]))
    # SCL and SDA leave to the left under the pull-ups, which sit at the sensor.
    bx0 = hx - 22.86
    # hx carries 3V3 down the left side of the chip, so the bus pins jog under it on a
    # pair of labels: SCL and SDA run to their pull-ups without crossing it twice.
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
    g = u9.pin("GND")
    s.power("power:GND", g)
    s.no_connect(u9.pin("NC"))
    s.text("Address 0x19. CS, SA0 tied high: ~20 k internal pull-ups\nwould draw 160 uA if strapped low.", (ax - 40.64, ay + 24.13))
    s.box((271.78, 66.04), (381.0, 132.08), "ACCELEROMETER (WAKE)")

    # Buttons.
    y = 147.32
    s.label("BTN", (284.48, y), rot=180)
    r = s.res_h("R18", "1k", (284.48, y))
    sw1 = s.symbol("Switch:SW_Push", "SW1", "USER / WAKE", (306.07, y), footprint=BTN_FP,
                   fields=BTN_FIELDS,
                   ref_at=(306.07, y - 5.08), value_at=(306.07, y - 2.54), justify="")
    s.wire(r.pin("2"), sw1.pin("1"))
    q = sw1.pin("2")
    s.wire(q, (q[0] + 2.54, q[1]))
    s.power("power:GND", (q[0] + 2.54, q[1]))
    y = 160.02
    s.label("QSPI_SS", (284.48, y), rot=180)
    r = s.res_h("R16", "1k", (284.48, y), text_below=True)
    sw2 = s.symbol("Switch:SW_Push", "SW2", "BOOTSEL", (306.07, y), footprint=BTN_FP,
                   fields=BTN_FIELDS,
                   ref_at=(306.07, y + 2.54), value_at=(306.07, y + 5.08), justify="")
    s.wire(r.pin("2"), sw2.pin("1"))
    q = sw2.pin("2")
    s.wire(q, (q[0] + 2.54, q[1]))
    s.power("power:GND", (q[0] + 2.54, q[1]))
    s.text("Internal pull-up; wake on low. Hold SW2, tap SW1 for BOOTSEL.", (322.58, 152.4))
    s.box((271.78, 134.62), (381.0, 170.18), "BUTTONS")

    # Test pads. RUN's pad sits beside a GND pad, so tweezers reset it.
    y = 203.2
    for ref, net, x in (("TP5", "RUN", 287.02), ("TP8", "GND", 299.72), ("TP6", "SWCLK", 317.5), ("TP7", "SWDIO", 330.2)):
        t = s.symbol("Connector:TestPoint", ref, net, (x, y), footprint=TP, in_bom=False,
                     fields={"Manufacturer": "", "MPN": "", "LCSC": ""},
                     ref_at=(x + 1.27, y - 6.35), value_at=(x + 1.27, y - 3.81))
        p = t.pin("1")
        if net == "GND":
            s.wire(p, (p[0] + 2.54, p[1]), (p[0] + 2.54, p[1] + 2.54))
            s.power("power:GND", (p[0] + 2.54, p[1] + 2.54))
        else:
            s.wire(p, (p[0], p[1] + 2.54))
            s.label(net, (p[0], p[1] + 2.54), rot=270)
    s.box((271.78, 193.04), (381.0, 218.44), "TEST PADS")

    # I2C0 pull-ups.
    y = 187.96
    for ref, net, x in (("R21", "I2C_SDA", 314.96), ("R22", "I2C_SCL", 345.44)):
        s.res_v(ref, "1k", (x, y - 7.62), text_left=True)
        s.power("power:+3V3", (x, y - 7.62))
        s.wire((x, y), (x + 7.62, y))
        s.label(net, (x + 7.62, y), **GL)
    s.box((271.78, 171.45), (381.0, 191.77), "I2C0 PULL-UPS")
    if VARIANT == "c":
        # The centre LED, past the 234 matrix cells, sinks into three GPIOs. Off means pin high, not hi-Z with the reset pull-down on.
        led = s.symbol("round_pendant:XL-1010RGB", "D235", "RGB", (360.68, 241.3), footprint="round_pendant:LED_XL-1010RGB",
                       fields={"LCSC": "C965834", "MPN": "XL-1010RGB-YG", "Manufacturer": "XINGLIGHT", "Cell": "RP2350 GPIO23-25"},
                       ref_at=(365.76, 233.68), value_at=(365.76, 236.22), justify="left")
        s.power("power:+3V3", led.pin("3"))
        for ref, val, net, pin_, y in (("R40", "1k", "CLED_R", "1", 256.54), ("R41", "470R", "CLED_G", "2", 264.16), ("R42", "470R", "CLED_B", "4", 271.78)):
            s.label(net, (279.4, y), rot=180)
            r = s.res_h(ref, val, (279.4, y))
            q = led.pin(pin_)
            s.wire(r.pin("2"), (q[0], y), q)
        s.text("Average about 1.5 mA per die at full, near a matrix LED's 1.25 mA.\nFirmware: GPIO high is off; clear pull-downs before sleep.", (279.4, 233.68))
        s.box((271.78, 220.98), (381.0, 279.4), "CENTRE LED")
    return s


# ---------------------------------------------------------------- matrix sheets

def matrix(n: int, first_led: int, first_ref: int) -> Sheet:
    """One driver and its 13 x 9 matrix. R = CS(3k), G = CS(3k-1), B = CS(3k-2), datasheet Figure 2."""
    s = Sheet(f"driver {n} and matrix", "IS31FL3741A, 13 x 9 RGB. LED references are cell order only")
    r = first_ref
    Ux, Uy = 81.28, 142.24
    u = s.symbol("round_pendant:IS31FL3741A", f"U{n}", "IS31FL3741A", (Ux, Uy),
                 footprint="round_pendant:QFN-60-1EP_7x7mm_P0.4mm_EP5.4x5.4mm",
                 fields={"LCSC": "C2940604", "MPN": "IS31FL3741A-QFLS4-TR", "Manufacturer": "ISSI"},
                 ref_at=(Ux + 14.0, 72.0), value_at=(Ux + 14.0, 74.54))
    p15, p25, p14 = u.pin("15"), u.pin("25"), u.pin("14")
    rail = p15[1] - 17.78
    cn = 30 + (n - 1) * 10
    x0 = p15[0] - 33.02
    s.power("round_pendant:VSYS", (x0, rail))
    s.wire((x0, rail), (p14[0] + 30.48, rail))
    s.wire(p15, (p15[0], rail))
    s.wire(p25, (p25[0], rail))
    s.wire(p14, (p14[0], rail))
    for ref, val, x, pin, fp in ((f"C{cn}", "22u", x0 + 5.08, "15", C0603), (f"C{cn+1}", "1u", x0 + 15.24, "15", C0402),
                                 (f"C{cn+2}", "100n", x0 + 25.4, "15", C0402), (f"C{cn+3}", "1u", p14[0] + 7.62, "25", C0402),
                                 (f"C{cn+4}", "100n", p14[0] + 15.24, "25", C0402), (f"C{cn+5}", "1u", p14[0] + 22.86, "14", C0402),
                                 (f"C{cn+6}", "100n", p14[0] + 30.48, "14", C0402)):
        s.cap(ref, val, (x, rail), fp=fp, decouples=f"U{n}.{pin}")
    s.text("Caps at PVCC 15 and 25 and AVCC 14; ground to the chip's GND.\n22 uF bulk: edges only. 494 mA scan peak (drivers.md).", (x0 - 2.54, rail - 10.16))
    # Control.
    sda, scl, intb, sdb, addr, iset = (u.pin(k) for k in ("SDA", "SCL", "INTB", "SDB", "ADDR", "ISET"))
    lx = sda[0] - 38.1
    for p, net in ((sda, "I2C_SDA"), (scl, "I2C_SCL")):
        s.wire(p, (lx, p[1]))
        s.label(net, (lx, p[1]), rot=180, **GL)
    # INTB pull-up, SDB pull-down + cap.
    s.wire(intb, (lx, intb[1]))
    s.label(f"INTB{n}", (lx, intb[1]), rot=180, **GL)
    s.res_v(f"R{r}", "100k", (lx + 7.62, intb[1] - 20.32 + 5.08), text_left=True)
    s.power("power:+3V3", (lx + 7.62, intb[1] - 15.24))
    s.wire((lx + 7.62, intb[1] - 7.62), (lx + 7.62, intb[1]))
    s.wire(sdb, (lx, sdb[1]))
    s.label(f"SDB{n}", (lx, sdb[1]), rot=180, **GL)
    s.res_v(f"R{r+1}", "100k", (lx + 22.86, sdb[1]), text_left=True, to_gnd=True)
    s.cap(f"C{cn+7}", "100n", (lx + 10.16, sdb[1]), text_left=True)
    # Address: U1 GND, U2 VSYS.
    if n == 1:
        s.wire(addr, (addr[0] - 2.54, addr[1]), (addr[0] - 2.54, addr[1] + 2.54))
        s.power("power:GND", (addr[0] - 2.54, addr[1] + 2.54))
        s.text("ADDR GND: 0x30", (addr[0] - 20.32, addr[1] + 12.7))
    else:
        s.wire(addr, (addr[0] - 5.08, addr[1]))
        s.power("round_pendant:VSYS", (addr[0] - 5.08, addr[1]))
        s.text("ADDR VSYS: 0x33", (addr[0] - 20.32, addr[1] + 12.7))
    s.wire(iset, (iset[0] - 12.7, iset[1]))
    s.res_v(f"R{r+2}", "30k", (iset[0] - 12.7, iset[1]), to_gnd=True)
    s.text("30 k: 12.67 mA peak,\n1.25 mA average per die", (iset[0] - 40.64, iset[1] + 17.78))
    s.power("power:GND", u.pin("GND"))
    # SW / CS labels at the driver.
    rx = u.pin("SW1")[0] + 5.08
    for i in range(1, 10):
        p = u.pin(f"SW{i}")
        s.wire(p, (rx, p[1]))
        s.label(f"SW{n}_{i}", (rx, p[1]))
    for i in range(1, 40):
        p = u.pin(f"CS{i}")
        s.wire(p, (rx, p[1]))
        s.label(f"CS{n}_{i}", (rx, p[1]))
    s.box((11.43, 25.4), (142.24, 243.84), f"DRIVER {n}")
    # The matrix.
    mx, my, dx, dy = 165.1, 38.1, 12.7, 19.05
    mx = round(mx / 1.27) * 1.27
    d = first_led
    for row in range(13):
        k = row + 1
        y = my + row * dy
        yr, yg, yb = y + 6.35, y + 8.89, y + 11.43
        last = mx + 8 * dx
        for yy, c, off in ((yr, 3 * k, -2.54), (yg, 3 * k - 1, 0), (yb, 3 * k - 2, 2.54)):
            s.wire((mx - 10.16, yy), (last + off, yy))
            s.label(f"CS{n}_{c}", (mx - 10.16, yy), rot=180)
        for col in range(9):
            x = mx + col * dx
            led = s.symbol("round_pendant:XL-1010RGB", f"D{d}", "RGB", (x, y),
                           footprint="round_pendant:LED_XL-1010RGB",
                           fields={"LCSC": "C965834", "MPN": "XL-1010RGB-YG", "Manufacturer": "XINGLIGHT", "Cell": f"U{n} SW{col+1} / triplet {k}"},
                           ref_at=(x + 1.27, y - 5.08), value_at=(x, y), justify="")
            pr, pg, pb, pa = led.pin("1"), led.pin("2"), led.pin("4"), led.pin("3")
            s.wire(pr, (pr[0], yr))
            s.wire(pg, (pg[0], yg))
            s.wire(pb, (pb[0], yb))
            s.wire(pa, (pa[0], pa[1] - 1.27), (x - 5.08, pa[1] - 1.27))
            d += 1
    for col in range(9):
        x = mx + col * dx - 5.08
        top_y = my - 8.89
        s.wire((x, top_y), (x, my + 12 * dy - 6.35))
        s.label(f"SW{n}_{col+1}", (x, top_y), rot=90)
    s.box((143.51, 13.97), (287.02, 281.94), "13 x 9 RGB MATRIX: R = CS(3k), G = CS(3k-1), B = CS(3k-2)")
    return s


# ---------------------------------------------------------------- hierarchy

def child_save(sheet: Sheet, path: Path, root_uuid: str, sheet_uuid: str):
    """Save a child sheet with its symbols' instance paths under the root."""
    sheet.save(path)
    t = path.read_text()
    t = t.replace(f'(path "/{sheet.uuid}"', f'(path "/{root_uuid}/{sheet_uuid}"')
    t = re.sub(r'\n?\s*\(sheet_instances\s*\(path "/"\s*\(page "1"\)\s*\)\s*\)', "", t)
    path.write_text(t)


def sheet_node(name, file, uuid, at, size, page, root_uuid):
    def p(k, v, y):
        return S("property", k, v, S("at", at[0], y, 0), [Sym("effects"), S("font", S("size", 1.27, 1.27)), [Sym("justify"), Sym("left"), Sym("bottom")]])
    return [Sym("sheet"), S("at", at[0], at[1]), S("size", size[0], size[1]), S("exclude_from_sim", yes(False)),
            S("in_bom", yes(True)), S("on_board", yes(True)), S("dnp", yes(False)), S("fields_autoplaced", yes(True)),
            S("stroke", S("width", 0.1524), S("type", Sym("solid"))),
            S("fill", S("color", 0, 0, 0, 0.0)), S("uuid", uuid),
            p("Sheetname", name, at[1] - 0.7), p("Sheetfile", file, at[1] + size[1] + 1.8),
            S("instances", S("project", PROJECT, S("path", "/" + root_uuid, S("page", str(page)))))]


def main():
    root = Sheet("top", "234 RGB LEDs on a 38 mm round board", paper="A4")
    sheets = [("Power", "power.kicad_sch", power()), ("MCU", "mcu.kicad_sch", mcu()),
              ("Driver 1 and matrix", "matrix1.kicad_sch", matrix(1, 1, 30)),
              ("Driver 2 and matrix", "matrix2.kicad_sch", matrix(2, 118, 33))]
    nodes = []
    places = [((25.4, 55.88), (50.8, 50.8)), ((96.52, 55.88), (50.8, 50.8)), ((167.64, 40.64), (63.5, 35.56)), ((167.64, 88.9), (63.5, 35.56))]
    for i, ((name, file, sh), (at, size)) in enumerate(zip(sheets, places)):
        u = new_uuid()
        child_save(sh, HW / file, root.uuid, u)
        nodes.append(sheet_node(name, file, u, at, size, i + 2, root.uuid))
    root.text("Rails: VBUS -> VSYS 3.0-4.5 V (LED SW lines) -> +3V3 -> +1V1 at the RP2350.\n"
              "Nets between sheets are global labels; rails are power symbols.\n"
              "Requirements: design/intent.md. Parts: design/parts/. Decisions: design/decisions.md.", (25.4, 135.0))
    path = HW / f"{PROJECT}.kicad_sch"
    root._cleanup()
    tree = [Sym("kicad_sch"), S("version", Sym("20250114")), S("generator", "eeschema"), S("generator_version", "9.0"),
            S("uuid", root.uuid), S("paper", root.paper), [Sym("title_block"), *[t for t in root.title if t[-1] != ""]],
            [Sym("lib_symbols")], *root.items, *nodes, S("sheet_instances", S("path", "/", S("page", "1"))),
            S("embedded_fonts", yes(False))]
    path.write_text(dump(tree) + "\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
