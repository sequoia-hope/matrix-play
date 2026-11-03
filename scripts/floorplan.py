#!/usr/bin/env python3
"""floorplan.py -- phase 4 drawing: LED sites, anode vias and proposed bottom-side blocks, seen through the board from the top.

Writes design/study/floorplan.svg and sites.json. Grid offset (1, 1): 4-fold symmetric, 256 sites fit.
USB-C mouth at the bottom of the drawing (+y). Chip centres sit on the via grid (via_study.py).
"""
import itertools, json, math
from pathlib import Path
R = 19.0; LAND = 0.625; EDGE = 0.35
AX = 0.25 - 0.0  # connector axis offset, from via_study
sites = [(2*i+1, 2*j+1) for i, j in itertools.product(range(-12, 12), repeat=2)
         if math.hypot(abs(2*i+1)+LAND, abs(2*j+1)+LAND) <= R-EDGE]
# Connector: mouth at the edge, origin chosen so the front legs stay on the board.
def lost(jx, jy):
    return [s for s in sites if any(abs(jx+f[0]-s[0]) < f[2]+LAND+f[4] and abs(jy+f[1]-s[1]) < f[3]+LAND+f[4] for f in feat)]
# half width, half height, clearance: plated legs 0.09 from their pad; NPTH pegs 0.2 from the hole.
feat = [(-4.32, 1.05, .5, .8, .09), (4.32, 1.05, .5, .8, .09), (-4.32, -3.13, .5, 1.05, .09), (4.32, -3.13, .5, 1.05, .09), (-2.89, -2.6, .325, .325, .2), (2.89, -2.6, .325, .325, .2)]
# Search the connector's position: fewest sites lost, then fewest away from the rim. Front legs stay 0.2 mm inside the edge.
def score(jx, jy):
    l = lost(jx, jy)
    return (sum(1 for s in l if math.hypot(*s) < 15.5), len(l), abs(jx))
cands = [(a/20, b/20) for a in range(-40, 41) for b in range(305, 335)
         if max(math.hypot(a/20+sx*4.82, b/20+1.85) for sx in (-1, 1)) <= R-.2]
Jx, Jy = min(cands, key=lambda c: score(*c))
def blocked(x, y):
    return (x, y) in set(lost(Jx, Jy))
# Buttons: actuator outward, pegs +-2.125 mm tangentially, 0.9 mm holes. Centre radius puts the actuator 0.4 mm past the edge.
BTN_R = 17.13  # MP pad corners 0.2 mm from the edge; actuator tip 0.17 mm past it
def btn_pegs(deg):
    a = math.radians(deg); cx, cy = BTN_R*math.cos(a), BTN_R*math.sin(a); tx, ty = -math.sin(a), math.cos(a)
    return [(cx+tx*d, cy+ty*d) for d in (-2.125, 2.125)]
def peg_sites(deg):
    return {t for t in sites for x, y in btn_pegs(deg) if abs(x-t[0]) < .45+LAND+.2 and abs(y-t[1]) < .45+LAND+.2}
def clash(deg):
    return all(math.hypot(x, y) < R-.6 for x, y in btn_pegs(deg)) is False
candidates = {d: peg_sites(d) for d in range(-180, 180, 2) if not clash(d) and not (45 < d < 135)}
east = min((d for d in candidates if -70 <= d <= 30), key=lambda d: (len(candidates[d]), abs(d+20)))
west = min((d for d in candidates if d >= 150 or d <= -110), key=lambda d: (len(candidates[d]), abs(abs(d)-160)))
BTN = {"SW1": east, "SW2": west}
lost_btn = candidates[east] | candidates[west]
keep = sorted([s for s in sites if not blocked(*s) and s not in lost_btn], key=lambda s: (round(math.hypot(*s), 6), s))
lost_interior = [s for s in sites if blocked(*s)]
chosen = keep[:234]
spare = keep[234:]
def via(s): return (s[0]-0.4, s[1]+0.4)
blocks = [("U3 RP2350A", -1.4, -6.6, 7.8, 7.8, "#e8c547"), ("L1 + regulator", 2.2, -12.6, 9, 4.4, "#e8a547"), ("U4 flash", -8.6, -12.0, 6, 5, "#c7d36f"),
          ("U1 IS31FL3741A", -9.4, 3.4, 7.8, 7.8, "#7fb6e8"), ("U2 IS31FL3741A", 8.6, 3.4, 7.8, 7.8, "#7fb6e8"),
          ("U5 charger", -0.75, 6.0, 5, 4.5, "#e88f7f"), ("U6 LDO, U8, Q1", -5.6, 10.6, 5, 3.4, "#e8b0a0"), ("U9 accel", 8.0, -7.0, 3.5, 3.5, "#b6a3e8"),
          ("BT1 pads", 8.0, 10.6, 6.5, 3.2, "#bbbbbb")]
W = 760; S = 18; C = W/2
def X(v): return C+v*S
def Y(v): return C+v*S
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W+80}" font-family="sans-serif" font-size="11">',
     f'<rect width="{W}" height="{W+80}" fill="white"/><circle cx="{C}" cy="{C}" r="{R*S}" fill="#f2f6ef" stroke="#222" stroke-width="2"/>']
for n, x, y, w, h, c in blocks:
    o.append(f'<rect x="{X(x-w/2)}" y="{Y(y-h/2)}" width="{w*S}" height="{h*S}" fill="{c}" fill-opacity=".55" stroke="#555"/>')
    o.append(f'<text x="{X(x)}" y="{Y(y-h/2)+13}" text-anchor="middle" font-weight="600">{n}</text>')
for n, px in (("U3", (-1.4, -6.6)), ("U1", (-9.4, 3.4)), ("U2", (8.6, 3.4))):
    ep = 1.7 if n == "U3" else 2.7
    o.append(f'<rect x="{X(px[0]-ep)}" y="{Y(px[1]-ep)}" width="{2*ep*S}" height="{2*ep*S}" fill="none" stroke="#333" stroke-dasharray="4 3"/>')
for s in chosen:
    o.append(f'<rect x="{X(s[0]-.5)}" y="{Y(s[1]-.5)}" width="{S}" height="{S}" fill="#ddd" stroke="#999" stroke-width=".5"/>')
    v = via(s)
    o.append(f'<circle cx="{X(v[0])}" cy="{Y(v[1])}" r="{0.15*S+1}" fill="#c0203a"/>')
for s in spare:
    o.append(f'<rect x="{X(s[0]-.5)}" y="{Y(s[1]-.5)}" width="{S}" height="{S}" fill="none" stroke="#2a8" stroke-dasharray="2 2"/>')
for s in lost_interior:
    o.append(f'<rect x="{X(s[0]-.5)}" y="{Y(s[1]-.5)}" width="{S}" height="{S}" fill="#ffd0d0" stroke="#c00"/><line x1="{X(s[0]-.5)}" y1="{Y(s[1]-.5)}" x2="{X(s[0]+.5)}" y2="{Y(s[1]+.5)}" stroke="#c00"/>')
for fx, fy, hx, hy, _ in feat:
    o.append(f'<rect x="{X(Jx+fx-hx)}" y="{Y(Jy+fy-hy)}" width="{2*hx*S}" height="{2*hy*S}" fill="#333"/>')
for ref, deg in BTN.items():
    a = math.radians(deg); cx, cy = BTN_R*math.cos(a), BTN_R*math.sin(a)
    o.append(f'<g transform="translate({X(cx)} {Y(cy)}) rotate({deg+90})"><rect x="{-2.25*S}" y="{-1.21*S}" width="{4.5*S}" height="{2.56*S}" fill="#999" fill-opacity=".5" stroke="#333"/><text text-anchor="middle" y="4">{ref}</text></g>')
    for x, y in btn_pegs(deg):
        o.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{.45*S}" fill="#333"/>')
for s_ in lost_btn:
    o.append(f'<rect x="{X(s_[0]-.5)}" y="{Y(s_[1]-.5)}" width="{S}" height="{S}" fill="#ffd0d0" stroke="#c00"/>')
for i in range(16):
    px = Jx + (i-7.5)*0.5
    o.append(f'<rect x="{X(px-.15)}" y="{Y(Jy-4.045-.55)}" width="{.3*S}" height="{1.1*S}" fill="#c58a2c"/>')
o.append(f'<rect x="{X(Jx-4.47)}" y="{Y(Jy-4)}" width="{8.94*S}" height="{7.35*S}" fill="none" stroke="#333" stroke-width="1.5"/><text x="{X(Jx)}" y="{Y(Jy+3.0)}" text-anchor="middle" font-weight="600">J1 USB-C</text>')
o.append(f'<text x="14" y="{W+24}" font-size="13">Seen through the board from the LED side. Grey: 234 LEDs. Red dot: anode via. Dashed green: spare sites. Red cross: sites lost to USB-C holes.</text>')
o.append(f'<text x="14" y="{W+44}" font-size="13">Black: USB-C holes. Dashed square: exposed pad. Blocks are rough regions, not placed parts.</text>')
o.append('</svg>')
Path("design/study/floorplan.svg").write_text("\n".join(o))
under = {}
for n, px, ep in (("U3", (-1.4, -6.6), 3.85), ("U1", (-9.4, 3.4), 3.8), ("U2", (8.6, 3.4), 3.8)):
    under[n] = sum(1 for s in chosen if max(abs(via(s)[0]-px[0]), abs(via(s)[1]-px[1])) < ep)
Path("design/study/sites.json").write_text(json.dumps({"sites": chosen, "spare": spare, "lost_to_usb": lost_interior, "lost_to_buttons": sorted(lost_btn), "buttons_deg": BTN, "button_radius": BTN_R, "j1": [Jx, Jy]}, indent=0))
smt = [v for v in (via(t) for t in chosen) if abs(v[0]-Jx) < 3.75+.215 and abs(v[1]-(Jy-4.045)) < .55+.215]
print("buttons", BTN, "sites lost to buttons", sorted(lost_btn), "anode vias on USB SMT row", smt)
print("J1", Jx, Jy)
print(f"sites {len(sites)}, lost to USB {len(lost_interior)} at {lost_interior}, chosen {len(chosen)}, spare left {len(spare)}, radius of chosen corner {max(math.hypot(abs(a)+LAND, abs(b)+LAND) for a,b in chosen):.2f}, vias under chips {under}")
print("via on chip centre grid check:", [(round((p[0]-via((1,1))[0])%2,3), round((p[1]-via((1,1))[1])%2,3)) for p in ((-1.4,-6.6),(-9.4,3.4),(8.6,3.4))])
