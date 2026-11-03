#!/usr/bin/env python3
"""usb_back_study.py -- vertical USB-C out of the back, with the turned sunflower on the LED side.

A study only: it doesn't touch hw/. Writes design/study/usb-back/. Reuses pattern_study.py's LED model and gap checks.

Connector: LAILAN LAIL-TYPE-C-16PIN-05-LT, C55591234, from its drawing (design/datasheets/usbv/C55591234.pdf, layout for T = 1.00 mm).
Legs at (+-2.40, +-2.15), plated slot 1.15 x 0.80, pad about 1.7 x 1.3 (scaled from the drawing, not dimensioned). Pegs 0.66 NPTH at (+-3.75, 0).
Signal rows at y = +-(1.28 - 0.87/2), pads 0.30 x 0.87, x = +-2.75, +-1.25, +-0.75, +-0.25. Body 8.94 x 3.16, 10.5 tall.
"""
import json, math
from pathlib import Path
import pattern_study as ps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/usb-back"

LEGS = [(s*2.40, t*2.15, .85, .65) for s in (-1, 1) for t in (-1, 1)]
PEGS = [(s*3.75, 0.0, .33, .33) for s in (-1, 1)]
SIG_X = (-2.75, -1.25, -.75, -.25, .25, .75, 1.25, 2.75)
SIG_Y = 1.28 - .87/2
BODY = (4.47, 1.58)
EDGE_PAD = .3         # J1 leg pad to board edge, as elsewhere on this board
CELL_RIM = .3         # cell to board edge at the north
CELL_GAP = .5         # cell to connector body: pouch swell and leads
ZONE = 3.3            # tallest back part with J1 gone: SKRTLAE010 button, drawing p.2
Jx = 0.0

def j_y(R):
    return math.sqrt((R-EDGE_PAD)**2 - 3.25**2) - 2.8

def cell_limit(R):
    return j_y(R) - BODY[1] - CELL_GAP

def max_round(R):
    return R - CELL_RIM + cell_limit(R)

def board_for(depth):
    R = 19.0
    while -R + CELL_RIM + depth > cell_limit(R):
        R += .01
    return R

def max_rect(R):
    """Largest rectangle north of the connector, inside the rim."""
    lim = cell_limit(R); r = R - CELL_RIM; best = (0, 0, 0)
    for k in range(0, 2000):
        y0 = -r + k*.01
        if y0 >= lim:
            break
        w = 2*min(math.sqrt(max(r*r-y0*y0, 0)), math.sqrt(max(r*r-lim*lim, 0)))
        if w*(lim-y0) > best[0]:
            best = (w*(lim-y0), w, lim-y0)
    return best

def setup(R):
    ps.R = R
    ps.RMAX = R - ps.EDGE - ps.LAND*math.sqrt(2)
    ps.Jx, ps.Jy = Jx, j_y(R)
    ps.HOLES = LEGS + PEGS
    ps.BTN_R = R - 1.87
    ps.HOLE_LIST = ps.holes()

def over_signal(pts, jy):
    n = 0
    for x, y, _ in pts:
        if abs(x-Jx) < 2.9+.625 and abs(y-jy) < 1.28+.625:
            n += 1
    return n

def svg(path, pts, R, margin, cell, jy):
    S = 760/(2*R+2); C = 380
    X = lambda v: C+v*S
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 760" font-family="system-ui,sans-serif" font-size="14">',
         f'<rect width="760" height="760" fill="#0b0d10"/><circle cx="{C}" cy="{C}" r="{R*S:.1f}" fill="#14181d" stroke="#6b7480" stroke-width="2"/>']
    if cell:
        w, d, name = cell
        cy = -R+CELL_RIM+d/2
        o.append(f'<ellipse cx="{C}" cy="{X(cy):.1f}" rx="{w/2*S:.1f}" ry="{d/2*S:.1f}" fill="#7dff9a" fill-opacity=".05" stroke="#7dff9a" stroke-width="1.5" stroke-dasharray="8 5"/>')
    o.append(f'<rect x="{X(Jx-BODY[0]):.1f}" y="{X(jy-BODY[1]):.1f}" width="{2*BODY[0]*S:.1f}" height="{2*BODY[1]*S:.1f}" rx="{BODY[1]*S:.1f}" fill="#2fb7ff" fill-opacity=".14" stroke="#2fb7ff" stroke-width="1.5" stroke-dasharray="6 4"/>')
    for sx in SIG_X:
        for sy in (-SIG_Y, SIG_Y):
            o.append(f'<rect x="{X(Jx+sx-.15):.1f}" y="{X(jy+sy-.435):.1f}" width="{.3*S:.1f}" height="{.87*S:.1f}" fill="#2fb7ff" fill-opacity=".55"/>')
    for hx, hy, a, b in ps.HOLE_LIST:
        o.append(f'<rect x="{X(hx-a-margin):.1f}" y="{X(hy-b-margin):.1f}" width="{2*(a+margin)*S:.1f}" height="{2*(b+margin)*S:.1f}" rx="{margin*S:.1f}" fill="#ffb020" fill-opacity=".2" stroke="#ffb020"/>')
        o.append(f'<rect x="{X(hx-a):.1f}" y="{X(hy-b):.1f}" width="{2*a*S:.1f}" height="{2*b*S:.1f}" rx="{min(a,b)*S:.1f}" fill="#000" stroke="#d8dde3"/>')
    for p in pts:
        a, b = ps.fam(p)
        col = {(0, 0): "#3b4149", (1, 0): "#ff6b8a", (0, 1): "#5fd0ff", (1, 1): "#ffffff"}[(int(a), int(b))]
        c = " ".join(f"{X(u):.1f},{X(v):.1f}" for u, v in ps.land(*p))
        o.append(f'<polygon points="{c}" fill="{col}"/>')
    o.append('</svg>')
    path.write_text("\n".join(o))

def side(path):
    """Section through the connector and cell, 41 mm plan, board at the top: LED face up."""
    S = 15; x0 = 40; z0 = 70; R = 20.5; jy = j_y(R)
    X = lambda y: x0 + (y+R)*S
    Z = lambda z: z0 + z*S
    r = lambda x, y, w, h, f, extra="": f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{f}" {extra}/>'
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 340" font-family="system-ui,sans-serif" font-size="13" fill="#d8dde3">', '<rect width="700" height="340" fill="#0b0d10"/>']
    o.append(r(X(-R), Z(-1.0), 2*R*S, 1.0*S, "#2f6b4f"))
    o.append(r(X(-R), Z(-1.4), 2*R*S, .4*S, "#ff6b8a"))
    o.append(r(X(-R+.3), Z(ZONE), 35.1*S, 5.45*S, "#7dff9a", 'fill-opacity=".35" stroke="#7dff9a"'))
    o.append(r(X(-R+1), Z(0), 1.0*S*3.4, ZONE*S, "#6b7480"))
    o.append(r(X(jy-1.58), Z(0), 3.16*S, 10.5*S, "#2fb7ff", 'fill-opacity=".55" stroke="#2fb7ff"'))
    o.append(r(X(jy-3.25), Z(10.5), 6.5*S, 6.8*S, "#a8b1bd", 'fill-opacity=".35" stroke="#a8b1bd" stroke-dasharray="5 4"'))
    o.append(f'<line x1="{X(-R)}" y1="{Z(9.75)}" x2="{X(R)+8}" y2="{Z(9.75)}" stroke="#ffb020" stroke-dasharray="7 5"/>')
    o.append(f'<text x="{X(-R)}" y="{Z(-1.4)-6}">LEDs 0.4, board 1.0</text>')
    o.append(f'<text x="{X(-R+7)}" y="{Z(ZONE+3)}" fill="#07140c">cell 5.45 thick, back at {ZONE+5.45:.2f} mm</text>')
    o.append(f'<text x="{X(-R+7)}" y="{Z(1.9)}">parts: tallest is the 3.3 mm button</text>')
    o.append(f'<text x="{X(-R)}" y="{Z(9.75)+18}" fill="#ffb020">housing back, about 1 mm wall at 9.75 mm</text>')
    o.append(f'<text x="{X(jy-3.25)-160}" y="{Z(14)}">plug overmould, typical</text>')
    o.append(f'<text x="{X(jy)+30}" y="{Z(5)}" fill="#8fd8ff">J1 10.5</text>')
    o.append('</svg>')
    path.write_text("\n".join(o))

CELLS = [
    ("Grepow 5435035 (chosen)", 35.0, 35.1, 5.45, "610 mAh listed"),
    ("Grepow GRP4435035", 35.0, 33.5, 4.4, "465 mAh, 4.2 V"),
    ("Grepow GRP7535035", 35.0, 33.5, 7.15, "845 mAh, 4.4 V"),
    ("Grepow GRP6530027", 30.0, 27.7, 6.35, "430 mAh, 4.35 V"),
]

PLANS = [
    ("v38-60", "38 mm, smaller cell, 0.6 mm hole margin", 19.0, .6, (30.0, 27.7, "GRP6530027")),
    ("v38-100", "38 mm, smaller cell, 1.0 mm hole margin", 19.0, 1.0, (30.0, 27.7, "GRP6530027")),
    ("v41-60", "41 mm, keeps the chosen cell, 0.6 mm hole margin", 20.5, .6, (35.0, 35.1, "5435035")),
    ("v41-100", "41 mm, keeps the chosen cell, 1.0 mm hole margin", 20.5, 1.0, (35.0, 35.1, "5435035")),
]

def page():
    d = json.loads((OUT/"results.json").read_text())
    base = next(x for x in json.loads((ROOT/"design/study/patterns/results.json").read_text()) if x["name"] == "vogel-turned")
    row = lambda t, c, s: f'<tr><td>{t}</td><td>{c}</td><td class="n">{s["count"]}</td><td class="n">{s["spacing_min"]:.2f}</td><td class="n">{s["land_gap"]:.2f}</td><td class="n">{s["usb_hole_gap"]:.2f}</td></tr>'
    rows = row("Edge-mount USB-C, 38 mm (plan C, for comparison)", "5435035", base)
    rows += "".join(row(p["title"], p["cell"], p) for p in d["plans"])
    cells = "".join(f'<tr><td>{c["name"]}</td><td class="n">{c["w"]:g} × {c["d"]:g} × {c["t"]:g}</td><td>{c["cap"]}</td><td class="n">{c["board_dia"]:.1f}</td><td class="n">{c["back"]:.2f}</td></tr>' for c in d["fit"]["cells"])
    cards = "".join(f'<figure><a href="{p["name"]}.svg"><img src="{p["name"]}.svg" alt="{p["title"]}"></a><figcaption><b>{p["title"]}</b><br>Tightest pad gap {p["land_gap"]:.2f} mm, LED to USB-C hole {p["usb_hole_gap"]:.2f} mm.</figcaption></figure>' for p in d["plans"])
    (OUT/"index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>round-pendant: USB-C out of the back</title><style>
body{{margin:0;background:#0e1116;color:#e6e9ee;font:15px/1.5 system-ui,sans-serif;padding:1.2rem}}main{{max-width:1200px;margin:auto}}
h1{{font-size:1.4rem;margin:.2rem 0}}h2{{font-size:1.1rem;margin:1.6rem 0 .3rem}}p{{color:#a8b1bd;max-width:62rem}}table{{border-collapse:collapse;margin:1rem 0;width:100%}}th,td{{padding:.35rem .6rem;border-bottom:1px solid #262c36;text-align:left}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}th{{color:#8b94a3;font-weight:600;font-size:.85rem}}
.g{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}figure{{margin:0;background:#171b22;border:1px solid #262c36;border-radius:10px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:.6rem .8rem;font-size:.9rem;color:#c6ccd5}}figcaption b{{color:#fff}}
.k span{{display:inline-block;margin-right:1rem}}.s{{display:inline-block;width:.8em;height:.8em;margin-right:.3em;border-radius:2px}}
</style></head><body><main><h1>Vertical USB-C out of the back, with the turned sunflower</h1>
<p>A study only: the board in hw/ is unchanged. Seen from the LED side, with the back-side connector and cell drawn through the board. Gaps come from a geometry model, and nothing has been routed. Connector: LAILAN LAIL-TYPE-C-16PIN-05-LT (C55591234), 10.5 mm tall.</p>
<p class="k"><span><i class="s" style="background:#ff6b8a"></i>one wind</span><span><i class="s" style="background:#5fd0ff"></i>opposing wind</span><span><i class="s" style="background:#fff"></i>both</span><span><i class="s" style="background:#3b4149"></i>other LEDs</span><span><i class="s" style="background:#000;border:1px solid #d8dde3"></i>through-hole</span><span><i class="s" style="background:#ffb020"></i>LED keepout</span><span><i class="s" style="background:#2fb7ff"></i>USB-C, back</span><span><i class="s" style="background:#7dff9a"></i>cell, back</span></p>
<table><tr><th>Plan</th><th>Cell</th><th class="n">LEDs</th><th class="n">Min pitch, mm</th><th class="n">Min pad gap, mm</th><th class="n">LED to USB-C hole, mm</th></tr>{rows}</table>
<div class="g">{cards}</div>
<h2>Why the board size and the cell are linked</h2>
<p>The plug has to come out beside the cell, not through it. On a 38 mm board, the largest round cell that leaves room for the connector is {d["fit"]["max_round_38"]} mm across; the chosen cell is 35 mm. Cell depth is measured north to south, with the cell pushed against the north rim, 0.5 mm from the connector. Grepow's guide says these cells aren't perfect circles; the listed sizes are from that guide and reseller listings, without maker datasheets, and capacities are at each listed full-charge voltage. This board charges to 4.2 V, so cells listed above that give less.</p>
<table><tr><th>Cell</th><th class="n">Size, mm</th><th>Listed</th><th class="n">Board needed, mm</th><th class="n">Cell back above board, mm</th></tr>{cells}</table>
<h2>Section through the connector, 41 mm plan</h2><figure style="max-width:760px"><img src="section.svg" alt="Section through board, cell, connector and plug"></figure>
</main></body></html>""")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = []
    for name, title, R, margin, cell in PLANS:
        setup(R)
        pts, rot = ps.best_rotation(lambda r: ps.vogel("holes", margin, True, r))
        st = ps.stats(pts)
        jy = j_y(R)
        svg(OUT/f"{name}.svg", pts, R, margin, cell, jy)
        res.append(dict(name=name, title=title, dia=2*R, margin=margin, rotation=rot, j_y=round(jy, 2), over_signal=over_signal(pts, jy), cell=cell[2], **st))
        print(name, res[-1], flush=True)
    fit = dict(j_y_38=round(j_y(19), 2), cell_limit_38=round(cell_limit(19), 2), max_round_38=round(max_round(19), 1),
               cells=[dict(name=c[0], w=c[1], d=c[2], t=c[3], cap=c[4], board_dia=round(2*board_for(c[2]), 1), back=round(ZONE+c[3], 2)) for c in CELLS],
               rect_38=[round(v, 1) for v in max_rect(19)], round_area=round(math.pi*17.5**2))
    print(fit)
    (OUT/"results.json").write_text(json.dumps(dict(plans=res, fit=fit), indent=1))
    side(OUT/"section.svg")
    page()

if __name__ == "__main__":
    main()
