#!/usr/bin/env python3
"""add_sensor.py IN OUT --site X Y ANG --adc PIN [--r X Y ANG] [--vias]: add the light sensor Q2 (earring footprint), load resistor R43, optional filter cap C70 to a finished board.
Mm from centre. Sensor on F.Cu with its pad 1 (collector) and pad 2 (emitter) where ANG puts them: pad 2 at site - 0.75*(cos, sin) ... printed.
Vias in pad: Q2.1 +3V3, Q2.2 ALS_OUT. R43 on B.Cu, 0402: pad 1 ALS_OUT on the emitter via, pad 2 GND with a via in pad. U3.PIN goes on net /MCU/LIGHT.
Needs the variant's lib; run with a .kicad_pro beside OUT, with net class pattern for /MCU/LIGHT if ANALOG is wanted."""
import argparse, math, os, sys
import pcbnew
ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--site", nargs=3, type=float, required=True); ap.add_argument("--adc", default="41")
ap.add_argument("--r", nargs=3, type=float); ap.add_argument("--lib", required=True); ap.add_argument("--value", default="22k"); ap.add_argument("--c", nargs=3, type=float, help="C70 on B.Cu, pad 1 LIGHT, pad 2 GND"); ap.add_argument("--cvalue", default="10n"); ap.add_argument("--power-pin", help="U3 pad to power the sensor instead of +3V3, net /MCU/LIGHT_PWR")
a = ap.parse_args()
b = pcbnew.LoadBoard(a.inp); C = 100e6; V = pcbnew.VECTOR2I
P = lambda x, y: V(int(x*1e6+C), int(y*1e6+C))
for r in ("Q2", "R43"):
    if b.FindFootprintByReference(r): sys.exit(f"{r} already on the board")
net = pcbnew.NETINFO_ITEM(b, "/MCU/LIGHT"); b.Add(net); light = b.FindNet("/MCU/LIGHT")
n3 = b.FindNet("+3V3")
if a.power_pin:
    b.Add(pcbnew.NETINFO_ITEM(b, "/MCU/LIGHT_PWR")); n3 = b.FindNet("/MCU/LIGHT_PWR")
    [p for p in b.FindFootprintByReference("U3").Pads() if p.GetNumber() == a.power_pin][0].SetNet(n3)
gnd = b.FindNet("GND")
q = pcbnew.FootprintLoad(a.lib, "SENSOR_ALS-PT19"); q.SetReference("Q2"); q.SetValue("ALS-PT19"); b.Add(q)
x, y, ang = a.site; q.SetPosition(P(x, y)); q.SetOrientationDegrees(ang)
pad = {p.GetNumber(): p for p in q.Pads()}; pad["1"].SetNet(n3); pad["2"].SetNet(light)
pc, pe = pad["1"].GetPosition(), pad["2"].GetPosition()
print("Q2 collector", round(pc.x/1e6-100, 3), round(pc.y/1e6-100, 3), "emitter", round(pe.x/1e6-100, 3), round(pe.y/1e6-100, 3))
tmpl = b.FindFootprintByReference("R8")
rr = pcbnew.Cast_to_FOOTPRINT(tmpl.Duplicate()); rr.SetParent(b); rr.SetReference("R43"); rr.SetValue(a.value); b.Add(rr)
if a.r: rx, ry, ra = a.r
else: rx, ry, ra = pe.x/1e6-100+.48, pe.y/1e6-100, 0.
rr.SetOrientationDegrees(ra); rr.SetPosition(P(rx, ry))
rp = {p.GetNumber(): p for p in rr.Pads()}
print("R43 side", "back" if rr.IsFlipped() else "FRONT", "pads", {k: (round(v.GetPosition().x/1e6-100, 3), round(v.GetPosition().y/1e6-100, 3), round(v.GetSizeX()/1e6, 2), round(v.GetSizeY()/1e6, 2)) for k, v in rp.items()})
rp["1"].SetNet(light); rp["2"].SetNet(gnd)
for pos, nt in ((pc, n3), (pe, light), (rp["2"].GetPosition(), gnd)):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(pcbnew.FromMM(.25)); v.SetDrill(pcbnew.FromMM(.15)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nt.GetNetCode()); v.SetLocked(True); b.Add(v)
if a.c:
    if b.FindFootprintByReference("C70"): sys.exit("C70 already on the board")
    cc = pcbnew.Cast_to_FOOTPRINT(tmpl.Duplicate()); cc.SetParent(b); cc.SetReference("C70"); cc.SetValue(a.cvalue); b.Add(cc)
    cc.SetOrientationDegrees(a.c[2]); cc.SetPosition(P(a.c[0], a.c[1]))
    cp = {p.GetNumber(): p for p in cc.Pads()}; cp["1"].SetNet(light); cp["2"].SetNet(gnd)
    print("C70 pads", {k: (round(v.GetPosition().x/1e6-100, 3), round(v.GetPosition().y/1e6-100, 3)) for k, v in cp.items()})
    v = pcbnew.PCB_VIA(b); v.SetPosition(cp["2"].GetPosition()); v.SetWidth(pcbnew.FromMM(.25)); v.SetDrill(pcbnew.FromMM(.15)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(gnd.GetNetCode()); v.SetLocked(True); b.Add(v)
u = [p for p in b.FindFootprintByReference("U3").Pads() if p.GetNumber() == a.adc][0]; u.SetNet(light)
pcbnew.SaveBoard(a.out, b); print("saved", a.out)
