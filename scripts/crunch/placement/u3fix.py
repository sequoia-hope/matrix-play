#!/usr/bin/env python3
"""u3fix.py VARIANT_DIR: make U3's copper real on an 8-layer board, in place. Recorded in the variant by being run on it. Parts don't move.

Band: outline +-3.5 mm so its fill reaches each 3V3 pad's centre, which is what KiCad connectivity needs (pad inner ends are at +-3.0; +-2.8 touched none). Fill stays out of foreign pads by clearance.
1V1: a 0.2 mm zone finger from the ring to each DVDD pin 6, 23, 39, 50, on B.Cu.
Pad ring: "no tracks" becomes a named area that keeps out only foreign nets (LESSONS.md): chip's own power and GND may go inward.
Regulator: the vendor's LX, 1V1, 3V3, PGND zones, FB finger from pin 50 to the COUT zone, PGND's two vias, CFILT's own GND via.
LX cut: on In6 and In5, the copper next to the part; In2 GND stays whole. L1 window: foreign nets kept off B.Cu under L1.
A via to the 3V3 plane in each band piece that has none."""
import json, math, os as _os, sys
from pathlib import Path
import pcbnew
D = Path(sys.argv[1]); PCB = D/"round-pendant.kicad_pcb"; DRU = D/"round-pendant.kicad_dru"
b = pcbnew.LoadBoard(str(PCB)); mm = pcbnew.FromMM; um = pcbnew.ToMM; OX = OY = 100.0
fps = {f.GetReference(): f for f in b.GetFootprints()}
lid = {b.GetLayerName(l): l for l in range(0, 64) if b.GetLayerName(l).endswith(".Cu")}
u = fps["U3"].GetPosition(); ux, uy = um(u.x)-OX, um(u.y)-OY
def poly(pts):
    p = pcbnew.SHAPE_POLY_SET(); p.NewOutline()
    for x, y in pts: p.Append(mm(OX+x), mm(OY+y))
    p.thisown = False; return p
def add(name, layer, net, pts, prio, minw=.1, clear=.09):
    z = pcbnew.ZONE(b); z.SetZoneName(name); z.SetLayer(layer); z.SetNet(b.FindNet(net)); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetMinThickness(mm(minw)); z.SetThermalReliefGap(mm(.2)); z.SetThermalReliefSpokeWidth(mm(.2)); z.SetLocalClearance(mm(clear))
    z.SetOutline(poly(pts)); b.Add(z); return z
def area(name, layer, pts, tracks=False, pour=False):
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetZoneName(name); k.SetLayer(layer)
    k.SetDoNotAllowCopperPour(pour); k.SetDoNotAllowTracks(tracks); k.SetDoNotAllowVias(False); k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    k.SetOutline(poly(pts)); b.Add(k); return k
sq = lambda h: [(ux-h, uy-h), (ux+h, uy-h), (ux+h, uy+h), (ux-h, uy+h)]
B = lid["B.Cu"]
keep = []
lx = None
for z in list(b.Zones()):
    n = z.GetZoneName()
    if n == "RP2350 band":
        z.SetOutline(poly(sq(3.5))); z.SetMinThickness(mm(.1))
    if n == "RP2350 ring":
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    if n == "U3 no tracks inside pads":
        z.SetDoNotAllowTracks(False); z.SetZoneName("U3 ring")
    if n == "LX no plane":
        q = z.GetBoundingBox(); lx = (um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY)
        z.SetLayer(lid["In5.Cu"])
q = fps["L1"].GetCourtyard(B).BBox()
if _os.environ.get("RINGVIAS"):
    area("U3 ring vias", B, sq(2.3))
# Regulator corner: chip frame x 0.95 to 3.45, y -8.1 to -3.0, foreign nets out, so nothing cuts the narrow zones.
area("reg corner", B, [(ux+.95, uy+3.0), (ux+3.45, uy+3.0), (ux+3.45, uy+8.1), (ux+.95, uy+8.1)])
area("L1 window", B, [(um(q.GetLeft())-OX, um(q.GetTop())-OY), (um(q.GetRight())-OX, um(q.GetTop())-OY), (um(q.GetRight())-OX, um(q.GetBottom())-OY), (um(q.GetLeft())-OX, um(q.GetBottom())-OY)])
box = [(lx[0], lx[1]), (lx[2], lx[1]), (lx[2], lx[3]), (lx[0], lx[3])]
area("LX no copper In6", lid["In6.Cu"], box, tracks=True, pour=True)
if _os.environ.get("IN6GND"):
    # Option: local GND on In6 under the regulator block, joined by PGND's vias. The LX rule area above keeps it off LX.
    add("In6 GND under regulator", lid["In6.Cu"], "GND", [(ux-.2, uy+3.3), (ux+5.6, uy+3.3), (ux+5.6, uy+8.4), (ux-.2, uy+8.4)], 0, minw=.1, clear=.2)
# Fingers: chip-frame direction from the pad's own position.
for p in fps["U3"].Pads():
    if p.GetNumber() in ("6", "23", "39", "50"):
        c = p.GetPosition(); x, y = um(c.x)-OX-ux, um(c.y)-OY-uy
        if abs(x) > abs(y):
            s = 1 if x > 0 else -1; pts = [(ux+s*2.1, uy+y-.1), (ux+s*3.5, uy+y-.1), (ux+s*3.5, uy+y+.1), (ux+s*2.1, uy+y+.1)]
        else:
            s = 1 if y > 0 else -1; pts = [(ux+x-.1, uy+s*2.1), (ux+x+.1, uy+s*2.1), (ux+x+.1, uy+s*3.5), (ux+x-.1, uy+s*3.5)]
        add(f"DVDD finger {p.GetNumber()}", B, "+1V1", pts, 2, minw=.1)
# Each DVDD pin to its capacitor as a 0.2 mm zone, as the reference's top-layer traces, so the capacitor isn't left to a long wire (the router doesn't count the ring).
for pin, cap in (("6", "C20"), ("23", "C19"), ("39", "C21")):
    a = [p for p in fps["U3"].Pads() if p.GetNumber() == pin][0].GetPosition(); c_ = [p for p in fps[cap].Pads() if p.GetNetname() == "+1V1"][0].GetPosition()
    ax, ay, cx_, cy_ = um(a.x)-OX, um(a.y)-OY, um(c_.x)-OX, um(c_.y)-OY
    # Straight out past the pad row first (0.25 mm beyond the pad tips), so the neighbours' pads don't cut it; then to the capacitor.
    if abs(ax-ux) > abs(ay-uy):
        ox_, oy_ = ux+(1 if ax > ux else -1)*4.15, ay
        add(f"DVDD out {pin}", B, "+1V1", [(ax, ay-.1), (ox_, ay-.1), (ox_, ay+.1), (ax, ay+.1)], 9, minw=.1)
    else:
        ox_, oy_ = ax, uy+(1 if ay > uy else -1)*4.15
        add(f"DVDD out {pin}", B, "+1V1", [(ax-.1, ay), (ax-.1, oy_), (ax+.1, oy_), (ax+.1, ay)], 9, minw=.1)
    d_ = math.hypot(cx_-ox_, cy_-oy_); nx, ny = -(cy_-oy_)/d_*.1, (cx_-ox_)/d_*.1
    add(f"DVDD cap {pin}", B, "+1V1", [(ox_+nx, oy_+ny), (cx_+nx, cy_+ny), (cx_-nx, cy_-ny), (ox_-nx, oy_-ny)], 10, minw=.1)
if _os.environ.get("CAPS3V3"):
    # Each IOVDD pin to its 100 nF the same way. The band joins the pins; this joins the capacitor to its own pin, not to whatever the router finds.
    for pin, cap in (("1", "C8"), ("11", "C9"), ("20", "C10"), ("30", "C11"), ("38", "C12"), ("44", "C14"), ("54", "C13")):
        a = [p for p in fps["U3"].Pads() if p.GetNumber() == pin][0].GetPosition(); c_ = [p for p in fps[cap].Pads() if p.GetNetname() == "+3V3"][0].GetPosition()
        ax, ay, cx_, cy_ = um(a.x)-OX, um(a.y)-OY, um(c_.x)-OX, um(c_.y)-OY
        if abs(ax-ux) > abs(ay-uy):
            ox_, oy_ = ux+(1 if ax > ux else -1)*4.15, ay
            add(f"IOVDD out {pin}", B, "+3V3", [(ax, ay-.1), (ox_, ay-.1), (ox_, ay+.1), (ax, ay+.1)], 9, minw=.1)
        else:
            ox_, oy_ = ax, uy+(1 if ay > uy else -1)*4.15
            add(f"IOVDD out {pin}", B, "+3V3", [(ax-.1, ay), (ax-.1, oy_), (ax+.1, oy_), (ax+.1, ay)], 9, minw=.1)
        d_ = math.hypot(cx_-ox_, cy_-oy_); nx, ny = -(cy_-oy_)/d_*.1, (cx_-ox_)/d_*.1
        add(f"IOVDD cap {pin}", B, "+3V3", [(ox_+nx, oy_+ny), (cx_+nx, cy_+ny), (cx_-nx, cy_-ny), (ox_-nx, oy_-ny)], 10, minw=.1)
# Drivers: each GND pin joined straight to the exposed pad by a short zone, and the pad-ring rule limited to foreign nets, as on U3.
for ref in ("U1", "U2"):
    f = fps[ref]; c = f.GetPosition(); cx, cy = um(c.x)-OX, um(c.y)-OY
    for z in list(b.Zones()):
        if z.GetZoneName() == f"{ref} no tracks inside pads":
            z.SetDoNotAllowTracks(False); z.SetZoneName(f"{ref} ring")
    for p in f.Pads():
        if p.GetNumber() in ("8", "12", "36", "55") and p.GetNetname() == "GND":  # U2's pin 8 is ADDR, on VSYS
            q = p.GetPosition(); x, y = um(q.x)-OX-cx, um(q.y)-OY-cy
            if abs(x) > abs(y):
                s_ = 1 if x > 0 else -1; pts = [(cx+s_*2.45, cy+y-.1), (cx+s_*abs(x), cy+y-.1), (cx+s_*abs(x), cy+y+.1), (cx+s_*2.45, cy+y+.1)]
            else:
                s_ = 1 if y > 0 else -1; pts = [(cx+x-.1, cy+s_*2.45), (cx+x+.1, cy+s_*2.45), (cx+x+.1, cy+s_*abs(y)), (cx+x-.1, cy+s_*abs(y))]
            add(f"{ref} GND finger {p.GetNumber()}", B, "GND", pts, 2, minw=.1)
# Vendor regulator zones, flipped to the back: board = U3 + (dx, -dy).
for q in json.loads((Path(__file__).parent/"vendor_zones.json").read_text()):
    if q["prio"] <= 3: continue
    net = {"/VREG_LX": "/MCU/VREG_LX"}.get(q["net"], q["net"])
    add(f"vendor {net}", B, net, [(ux+x, uy-y) for x, y in q["pts"]], q["prio"], minw=min(q["minw"], .1), clear=.12)
# FB: pin 50 (frame x 1.2) to the COUT zone (frame y -4.9), past pin 51's escape and the CIN zone.
add("FB finger", B, "+1V1", [(ux+x, uy-y) for x, y in [(1.1, -3.35), (1.3, -3.35), (1.3, -3.9), (1.1, -4.05), (1.1, -5.0), (.98, -5.0), (.98, -3.95), (1.1, -3.85)]], 8, minw=.09)
gnd = b.FindNet("GND").GetNetCode()
def via(x, y, net, w=.25, d=.15):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(OX+x), mm(OY+y))); v.SetWidth(mm(w)); v.SetDrill(mm(d)); v.SetLayerPair(lid["F.Cu"], B); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
# Free-site test for everything we add.
leds = []
for f in b.GetFootprints():
    if f.GetReference()[0] == "D":
        a = math.radians(-f.GetOrientationDegrees())
        for p in f.Pads():
            c = p.GetPosition(); leds.append((um(c.x)-OX, um(c.y)-OY, math.cos(a), math.sin(a)))
pads = [(um(q.GetLeft())-OX, um(q.GetTop())-OY, um(q.GetRight())-OX, um(q.GetBottom())-OY, p.GetNetname()) for f in b.GetFootprints() if f.GetReference()[0] != "D" for p in f.Pads() for q in [p.GetBoundingBox()]]
vias = [(um(t.GetPosition().x)-OX, um(t.GetPosition().y)-OY) for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
stubs = [(um(t.GetStart().x)-OX, um(t.GetStart().y)-OY, um(t.GetEnd().x)-OX, um(t.GetEnd().y)-OY) for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
def sd(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay; n = vx*vx+vy*vy; t = 0 if n == 0 else max(0, min(1, ((px-ax)*vx+(py-ay)*vy)/n)); return math.hypot(px-ax-t*vx, py-ay-t*vy)
def free(x, y, net, R=.275, sep=.41):
    for lx_, ly, c, s in leds:
        if abs(lx_-x) < 1.2 and abs(ly-y) < 1.2:
            du = abs(c*(x-lx_)+s*(y-ly))-.225; dv = abs(-s*(x-lx_)+c*(y-ly))-.225
            if math.hypot(max(du, 0), max(dv, 0)) < R: return False
    for a, e, g, h, n in pads:
        if n != net and math.hypot(max(a-x, 0, x-g), max(e-y, 0, y-h)) < R: return False
    if any(math.hypot(x-a, y-e) < sep for a, e in vias): return False
    if any(sd(x, y, *t) < R+.06 for t in stubs): return False
    return True
frames = lambda px, py: (ux+px, uy-py)
# PGND's two vias: as near the vendor's spot as an LED allows. Search the vendor GND zone, pick the closest free pair >= 0.41 apart.
gz = [q for q in json.loads((Path(__file__).parent/"vendor_zones.json").read_text()) if q["prio"] == 4][0]["pts"]
def inp(px, py, P):
    c = False
    for i in range(len(P)):
        a, e = P[i], P[i-1]
        if (a[1] > py) != (e[1] > py) and px < (e[0]-a[0])*(py-a[1])/(e[1]-a[1])+a[0]: c = not c
    return c
sites = []
for i in range(0, 90):
    for j in range(0, 80):
        fx, fy = 2.3+i*.0125, -5.8+j*.0375
        if inp(fx, fy, gz):
            x, y = frames(fx, fy)
            if free(x, y, "GND", R=.275): sites.append((math.hypot(fx-3.1, fy+5.2), x, y))
sites.sort(); pair = None
for s_, x, y in sites:
    for t_, x2, y2 in sites:
        if .41 <= math.hypot(x-x2, y-y2) <= .8 and t_ >= s_:
            pair = ((x, y), (x2, y2)); break
    if pair: break
print("PGND vias", pair, "sites", len(sites))
if pair:
    for x, y in pair: via(x, y, gnd); vias.append((x, y))
# CFILT: its own GND via, by C17's GND pad.
pd = [p for p in fps["C17"].Pads() if p.GetNetname() == "GND"][0].GetPosition(); px, py = um(pd.x)-OX, um(pd.y)-OY
best = None
for i in range(-20, 21):
    for j in range(-20, 21):
        x, y = px+i*.05, py+j*.05
        if math.hypot(i*.05, j*.05) < 1.2 and free(x, y, "GND") and (best is None or math.hypot(i, j) < best[0]): best = (math.hypot(i, j), x, y)
print("CFILT via", best)
if best:
    via(best[1], best[2], gnd); vias.append(best[1:])
b.BuildConnectivity(); filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
if _os.environ.get("RING6"):
    v1 = b.FindNet("+1V1").GetNetCode()
    for z in list(b.Zones()):
        if z.GetZoneName() == "RP2350 ring" or z.GetZoneName().startswith("DVDD finger"):
            keep.append(z); b.Remove(z)
    I6 = lid["In6.Cu"]; h = 4.4
    add("1V1 pour In6", I6, "+1V1", [(ux-h, uy-h), (ux+h, uy-h), (ux+h, uy+h), (ux+1.65, uy+h), (ux+1.65, uy+6.3), (ux+.2, uy+6.3), (ux+.2, uy+h), (ux-h, uy+h)], 1, minw=.1, clear=.09)
    # A via where each DVDD pin's zone ends, and in the COUT zone.
    spots = []
    for pin in ("6", "23", "39"):
        c = [p for p in fps["U3"].Pads() if p.GetNumber() == pin][0].GetPosition(); spots.append((um(c.x)-OX, um(c.y)-OY, pin))
    def sitefor(x0, y0, reach=1.1):
        opts = []
        for i in range(-28, 29):
            for j in range(-28, 29):
                x, y = x0+i*.04, y0+j*.04
                d_ = math.hypot(i*.04, j*.04)
                if max(abs(x-ux), abs(y-uy)) >= 3.95 and d_ <= reach+1.2 and free(x, y, "+1V1", R=.275, sep=.41): opts.append((d_, x, y))
        return min(opts) if opts else None
    for x0, y0, pin in spots:
        q = sitefor(x0, y0)
        print("1V1 via for pin", pin, q)
        if q:
            via(q[1], q[2], v1); vias.append(q[1:])
    # COUT zone, chip frame about (0.9, -5.6).
    x0, y0 = frames(.9, -5.6); best = None
    for i in range(-25, 26):
        for j in range(-25, 26):
            x, y = x0+i*.03, y0+j*.03
            if free(x, y, "+1V1") and (best is None or math.hypot(i, j) < best[0]): best = (math.hypot(i, j), x, y)
    print("1V1 via at COUT", best)
    if best: via(best[1], best[2], v1); vias.append(best[1:])
pcbnew.SaveBoard(str(PCB), b)
t = DRU.read_text()
if _os.environ.get("RINGVIAS"):
    t += """
(rule "U3 ring foreign vias"
  (condition "A.intersectsArea('U3 ring vias') && A.NetName != '+1V1' && A.NetName != 'GND'")
  (constraint disallow via))
"""
t += """
# U3 and regulator keep-outs from scripts/crunch/placement/u3fix.py: foreign nets only (LESSONS.md, a part's own power may pass).
(rule "U3 ring foreign tracks"
  (condition "A.intersectsArea('U3 ring') && A.NetName != '+3V3' && A.NetName != '+1V1' && A.NetName != 'GND'")
  (constraint disallow track))
(rule "U1 ring foreign tracks"
  (condition "A.intersectsArea('U1 ring') && A.NetName != 'GND' && A.NetName != 'VSYS'")
  (constraint disallow track))
(rule "U2 ring foreign tracks"
  (condition "A.intersectsArea('U2 ring') && A.NetName != 'GND' && A.NetName != 'VSYS'")
  (constraint disallow track))
(rule "reg corner foreign"
  (condition "A.intersectsArea('reg corner') && A.NetName != '/MCU/VREG_LX' && A.NetName != '+1V1' && A.NetName != '+3V3' && A.NetName != 'GND' && A.NetName != '/MCU/VREG_AVDD'")
  (constraint disallow track via))
(rule "L1 window foreign"
  (condition "A.intersectsArea('L1 window') && A.NetName != '/MCU/VREG_LX' && A.NetName != '+1V1'")
  (constraint disallow track via))
"""
DRU.write_text(t)
import os, subprocess; sys.stdout.flush()
subprocess.run([sys.executable, str(Path(__file__).parent/"u3fix2.py"), str(D)]); os._exit(0)
