#!/usr/bin/env python3
"""offboard_study.py -- turned sunflower on 38 mm with USB-C off the board and pads only. A study: it doesn't touch hw/.

Compares button choices and how many innermost lattice points are skipped. skip removes the crowded first points of the sunflower; the
same 234 LEDs then spread a little further. Writes design/study/usb-offboard/. Pad and button positions are indicative, not placed.
"""
import json, math
from pathlib import Path
import pattern_study as ps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/usb-offboard"
R = 19.0
RMAX = R - ps.EDGE - ps.LAND*math.sqrt(2)
PADS = ("VBUS", "D+", "D-", "CC1", "CC2", "GND")

def pegs(rc, deg, tan, rad, hr):
    t = math.radians(deg); ux, uy = math.cos(t), math.sin(t); tx, ty = -uy, ux
    return [(ux*(rc+d*rad)+tx*d*tan, uy*(rc+d*rad)+ty*d*tan, hr, hr) for d in (-1, 1)]

def peg_margin(pts, holes):
    """Peg hole edge to the nearest LED land: nothing is moved or dropped for the pegs."""
    out = 9.0
    for hx, hy, hr, _ in holes:
        for x, y, a in pts:
            c, s_ = math.cos(a), math.sin(a); dx, dy = hx-x, hy-y
            u, v = abs(c*dx+s_*dy)-ps.LAND, abs(-s_*dx+c*dy)-ps.LAND
            out = min(out, math.hypot(max(u, 0), max(v, 0))-hr)
    return round(out, 2)

def lattice(skip, rot=0.0):
    c = RMAX/math.sqrt(skip+ps.TARGET); pts = []
    for n in range(skip, skip+ps.TARGET):
        r, t = c*math.sqrt(n+.5), n*ps.GA+rot
        x, y = r*math.cos(t), r*math.sin(t)
        pts.append((x, y, t+math.radians(45)))
        ps.ARM[(round(x, 4), round(y, 4))] = (n % 21 % 3 == 0, n % 34 % 3 == 0)
    return pts, c*math.sqrt(skip+.5)

def svg(path, pts, holes, button):
    S = 19.5; C = 380; X = lambda v: C+v*S
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 760" font-family="system-ui,sans-serif" font-size="13">',
         f'<rect width="760" height="760" fill="#0b0d10"/><circle cx="{C}" cy="{C}" r="{R*S}" fill="#14181d" stroke="#6b7480" stroke-width="2"/>',
         f'<circle cx="{C}" cy="{C}" r="{17.5*S}" fill="none" stroke="#7dff9a" stroke-width="1.5" stroke-dasharray="8 5"/>']
    for i, name in enumerate(PADS):
        x = (i-2.5)*1.7
        o.append(f'<rect x="{X(x-.6):.1f}" y="{X(15.6):.1f}" width="{1.2*S:.1f}" height="{1.8*S:.1f}" fill="#2fb7ff" fill-opacity=".55"/>')
    for d in (-22, -162):
        t = math.radians(d); cx, cy = 17.3*math.cos(t), 17.3*math.sin(t)
        o.append(f'<circle cx="{X(cx):.1f}" cy="{X(cy):.1f}" r="{button*S:.1f}" fill="#ffb020" fill-opacity=".15" stroke="#ffb020" stroke-dasharray="5 4"/>')
    for hx, hy, a, b in holes:
        o.append(f'<rect x="{X(hx-a):.1f}" y="{X(hy-b):.1f}" width="{2*a*S:.1f}" height="{2*b*S:.1f}" rx="{a*S:.1f}" fill="#000" stroke="#d8dde3"/>')
    for p in pts:
        a, b = ps.fam(p)
        col = {(0, 0): "#3b4149", (1, 0): "#ff6b8a", (0, 1): "#5fd0ff", (1, 1): "#ffffff"}[(int(a), int(b))]
        o.append('<polygon points="' + " ".join(f"{X(u):.1f},{X(v):.1f}" for u, v in ps.land(*p)) + f'" fill="{col}"/>')
    o.append('</svg>')
    path.write_text("\n".join(o))

def measure(pts):
    st = ps.stats(pts)
    return dict(count=st["count"], gap=st["land_gap"], pitch=st["spacing_min"], mean=st["spacing_mean"], edge=st["edge"])

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ps.R, ps.RMAX = R, RMAX
    ps.Jx, ps.Jy, ps.HOLES, ps.BTN_R = 0, 99, [], 17.13
    far = [(99, 99, .1, .1)]*6
    res = []
    for name, title, skip in (("no-holes-1", "No holes, smallest centre gap", 1), ("no-holes-4", "No holes, wider pad gaps, larger centre gap", 4)):
        ps.HOLE_LIST = far
        pts, inner = lattice(skip)
        svg(OUT/f"{name}.svg", pts, [], 1.9)
        res.append(dict(name=name, title=title, holes=0, centre_clear=round(2*(inner-.884), 1), **measure(pts)))
    # Pegs dodging the LEDs: the same lattice, turned so the buttons sit mirrored about north (positions from a search of all angles).
    for name, title, rot, rcs, tan, rad, hr in (("dodge-skrt", "Current buttons, pegs between the LEDs", -67.25, (17.12, 17.12), 2.125, 0, .45),
                                                ("dodge-evq", "EVQP7C01P, pegs between the LEDs", -82.75, (17.32, 17.38), 0, .9, .325)):
        ps.HOLE_LIST = far
        pts, inner = lattice(1, math.radians(rot))
        holes = pegs(rcs[0], 201.25, tan, rad, hr) + pegs(rcs[1], 338.75, tan, rad, hr)
        svg(OUT/f"{name}.svg", pts, holes, 2.3 if tan else 1.9)
        res.append(dict(name=name, title=title, holes=4, peg=peg_margin(pts, holes), centre_clear=round(2*(inner-.884), 1), **measure(pts)))
    ps.HOLE_LIST = ps.holes()
    pts, rot = ps.best_rotation(lambda r: ps.vogel("holes", .6, True, r))
    holes = list(ps.HOLE_LIST)
    inner = min(math.hypot(p[0], p[1]) for p in pts)
    ps.HOLE_LIST = holes + far
    svg(OUT/"button-pegs.svg", pts, holes, 2.3)
    res.append(dict(name="button-pegs", title="Current buttons, LEDs kept 0.6 mm from pegs", holes=4, centre_clear=round(2*(inner-.884), 1), **measure(pts)))
    print(json.dumps(res, indent=1))
    (OUT/"results.json").write_text(json.dumps(res, indent=1))
    rows = "".join(f'<tr><td>{r_["title"]}</td><td class="n">{r_["holes"]}</td><td class="n">{r_["count"]}</td><td class="n">{r_["pitch"]:.2f}</td><td class="n">{r_["gap"]:.2f}</td><td class="n">{r_["centre_clear"]:.1f}</td><td class="n">{r_.get("peg", "")}</td></tr>' for r_ in res)
    cards = "".join(f'<figure><a href="{r_["name"]}.svg"><img src="{r_["name"]}.svg" alt="{r_["title"]}"></a><figcaption><b>{r_["title"]}</b><br>Tightest pad gap {r_["gap"]:.2f} mm, clear centre {r_["centre_clear"]:.1f} mm across.</figcaption></figure>' for r_ in res)
    (OUT/"index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>round-pendant: off-board USB-C</title><style>
body{{margin:0;background:#0e1116;color:#e6e9ee;font:15px/1.5 system-ui,sans-serif;padding:1.2rem}}main{{max-width:1200px;margin:auto}}h1{{font-size:1.4rem;margin:.2rem 0}}p{{color:#a8b1bd;max-width:62rem}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}th,td{{padding:.35rem .6rem;border-bottom:1px solid #262c36;text-align:left}}.n{{text-align:right;font-variant-numeric:tabular-nums}}th{{color:#8b94a3;font-weight:600;font-size:.85rem}}
.g{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}figure{{margin:0;background:#171b22;border:1px solid #262c36;border-radius:10px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:.6rem .8rem;font-size:.9rem;color:#c6ccd5}}figcaption b{{color:#fff}}
.k span{{display:inline-block;margin-right:1rem}}.s{{display:inline-block;width:.8em;height:.8em;margin-right:.3em;border-radius:2px}}
</style></head><body><main><h1>Turned sunflower, 38 mm, USB-C off the board</h1>
<p>A study only: the board in hw/ is unchanged. Seen from the LED side, with back-side parts drawn through the board. USB pads and buttons show rough positions, not placements. Gaps come from a geometry model, and nothing has been routed.</p>
<p class="k"><span><i class="s" style="background:#ff6b8a"></i>one wind</span><span><i class="s" style="background:#5fd0ff"></i>opposing wind</span><span><i class="s" style="background:#fff"></i>both</span><span><i class="s" style="background:#3b4149"></i>other LEDs</span><span><i class="s" style="background:#000;border:1px solid #d8dde3"></i>through-hole</span><span><i class="s" style="background:#2fb7ff"></i>USB pads, back</span><span><i class="s" style="background:#ffb020"></i>button, back</span><span><i class="s" style="background:#7dff9a"></i>cell, back</span></p>
<table><tr><th>Plan</th><th class="n">Holes in LED side</th><th class="n">LEDs</th><th class="n">Min pitch, mm</th><th class="n">Min pad gap, mm</th><th class="n">Clear centre, mm across</th><th class="n">Peg hole to LED, mm</th></tr>{rows}</table>
<div class="g">{cards}</div></main></body></html>""")

if __name__ == "__main__":
    main()
