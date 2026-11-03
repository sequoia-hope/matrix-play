#!/usr/bin/env python3
"""pattern_study.py -- test LED-side floor plans: spiral patterns with the back-side USB-C and its clearance overlaid.

A study only: it doesn't touch hw/. Writes design/study/patterns/*.svg, results.json and index.html.

Keepouts: "holes" keeps LED lands a margin from the through-holes of J1 and the buttons. "bay" clears the whole connector
footprint, so the gap reads as deliberate. LEDs are 1.25 mm square lands, either axis-aligned or turned along their spiral.
"""
import json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/patterns"
R, EDGE, LAND = 19.0, 0.35, 0.625
RMAX = R - EDGE - LAND * math.sqrt(2)
PHI = (1 + 5**.5) / 2
GA = math.pi * (3 - 5**.5)
B = math.log(PHI) / (math.pi / 2)   # true golden spiral: grows by phi every quarter turn
TARGET = 234
THIN = 1.9
MIN_GAP = 0.25                      # land to land: room for one track and clearance is 0.28; below this it won't route

Jx, Jy = 0.0, 15.9                  # USB-C centred
HOLES = [(-4.32, 1.05, .5, .8), (4.32, 1.05, .5, .8), (-4.32, -3.13, .5, 1.05), (4.32, -3.13, .5, 1.05), (-2.89, -2.6, .325, .325), (2.89, -2.6, .325, .325)]
BTN_R, BTN_DEG = 17.13, (-22, -162)

def holes():
    out = [(Jx + x, Jy + y, a, b) for x, y, a, b in HOLES]
    for d in BTN_DEG:
        t = math.radians(d); cx, cy = BTN_R * math.cos(t), BTN_R * math.sin(t); tx, ty = -math.sin(t), math.cos(t)
        out += [(cx + tx * s, cy + ty * s, .45, .45) for s in (-2.125, 2.125)]
    return out
HOLE_LIST = holes()

def land(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return [(x + c*u - s*v, y + s*u + c*v) for u, v in ((-LAND, -LAND), (LAND, -LAND), (LAND, LAND), (-LAND, LAND))]

def sat_gap(p, q):
    """Separating-axis gap between convex polygons: > 0 when apart, a good lower bound on the distance."""
    best = -1e9
    for poly in (p, q):
        for i in range(len(poly)):
            ex, ey = poly[(i+1) % len(poly)][0] - poly[i][0], poly[(i+1) % len(poly)][1] - poly[i][1]
            n = math.hypot(ex, ey); nx, ny = -ey/n, ex/n
            a = [nx*x + ny*y for x, y in p]; b = [nx*x + ny*y for x, y in q]
            best = max(best, min(b) - max(a), min(a) - max(b))
    return best

def rect(x, y, a, b):
    return [(x-a, y-b), (x+a, y-b), (x+a, y+b), (x-a, y+b)]

def keep_ok(pt, mode, margin):
    x, y, a = pt
    L = land(x, y, a)
    if mode == "bay":
        ly = min(q[1] for q in L); hx = max(abs(q[0] - Jx) for q in L)
        if max(q[1] for q in L) > Jy - 4.045 - .55 - margin and min(abs(q[0] - Jx) for q in L) < 4.82 + margin:
            return False
    for hx, hy, ha, hb in HOLE_LIST:
        if sat_gap(L, rect(hx, hy, ha, hb)) < margin:
            return False
    return True

def stats(pts):
    arr = np.array([(p[0], p[1]) for p in pts])
    gap = 9.0
    for i in range(len(pts)):
        d = np.hypot(arr[:, 0]-arr[i, 0], arr[:, 1]-arr[i, 1])
        for j in np.where((d < 3.2) & (d > 0))[0]:
            if j > i:
                gap = min(gap, sat_gap(land(*pts[i]), land(*pts[int(j)])))
    usb = min(sat_gap(land(*p), rect(h[0], h[1], h[2], h[3])) for p in pts for h in HOLE_LIST[:6])
    edge = min(R - max(math.hypot(*q) for q in land(*p)) for p in pts)
    nn = []
    for i in range(len(arr)):
        d = np.hypot(arr[:, 0]-arr[i, 0], arr[:, 1]-arr[i, 1]); d[i] = 99; nn.append(d.min())
    # Anode vias under the current chips, if those stayed: a rough measure of how much the back side must change.
    chips = {"U1": (-11.4, 3.4), "U2": (10.6, 3.4), "U3": (-1.4, -6.6)}
    under = sum(1 for p in pts for c in chips.values() if max(abs(p[0]-c[0]), abs(p[1]-c[1])) < 3.9)
    return dict(count=len(pts), land_gap=round(gap, 3), usb_hole_gap=round(usb, 2), edge=round(edge, 2), spacing_min=round(float(min(nn)), 2), spacing_mean=round(float(np.mean(nn)), 2), leds_over_chips=under)

# ---------------------------------------------------------------- patterns

def grid(mode, margin):
    sites = [(2*i+1, 2*j+1, 0.0) for i in range(-10, 10) for j in range(-10, 10)]
    ok = [s for s in sites if max(math.hypot(*q) for q in land(*s)) <= R-EDGE and keep_ok(s, mode, margin)]
    ok.sort(key=lambda s: math.hypot(s[0], s[1]))
    return ok[:TARGET]

def vogel(mode, margin, turn, rot=0.0):
    """Golden-angle lattice. Its neighbours form opposing spirals, 13, 21 and 34 of them, in both winds."""
    for total in range(TARGET, TARGET + 60):
        c = RMAX / math.sqrt(total)
        pts = []
        for n in range(total):
            r = c * math.sqrt(n + .5); t = n * GA + rot
            a = t + math.radians(45) if turn else 0.0
            x_, y_ = r*math.cos(t), r*math.sin(t)
            pts.append((x_, y_, a))
            ARM[(round(x_, 4), round(y_, 4))] = (n % 21 % 3 == 0, n % 34 % 3 == 0)
        keep = [p for p in pts if keep_ok(p, mode, margin)]
        if len(keep) >= TARGET:
            return keep[:TARGET] if len(keep) == TARGET else keep[-TARGET:]
    return keep

def best_rotation(fn):
    best = None
    for d in range(0, 360, 5):
        pts = fn(math.radians(d))
        s = stats(pts)
        key = (s["land_gap"] >= MIN_GAP, s["count"], s["land_gap"])
        if best is None or key > best[0]:
            best = (key, pts, d)
    return best[1], best[2]

def thin(raw, spacing, count):
    """Keep points in order, dropping any too close to one kept already."""
    kept = []
    for p in raw:
        if all(math.hypot(p[0]-k[0], p[1]-k[1]) >= spacing for k in kept):
            kept.append(p)
    return kept

def nested(mode, margin, rot=0.0):
    """Nested golden spirals: Fibonacci zones, 8, 13, 21 arms of each wind, one LED at every crossing of opposing arms."""
    best = []
    for scale in np.arange(.60, 1.2, .01):
        raw = []
        zones = [(1.6, 3.6*scale, 5), (3.6*scale, 6.6*scale, 8), (6.6*scale, 11.0*scale, 13), (11.0*scale, 20, 21)]
        for lo, hi, m in zones:
            step = B * math.pi / m
            k = 0
            for k in range(-400, 400):
                r = math.exp(k * step)
                if lo <= r < hi and r <= RMAX:
                    for i in range(m):
                        t = (i + (k % 2) / 2) * 2*math.pi/m + rot
                        raw.append((r*math.cos(t), r*math.sin(t), t + math.radians(45)))
        raw = [p for p in raw if keep_ok(p, mode, margin)]
        raw.sort(key=lambda p: -math.hypot(p[0], p[1]))
        kept = thin(raw, THIN, TARGET)
        if len(kept) >= TARGET or len(kept) > len(best):
            best = kept
        if len(kept) >= TARGET:
            break
    best.sort(key=lambda p: math.hypot(p[0], p[1]))
    return best[-TARGET:] if len(best) > TARGET else best

def arms(mode, margin, m, rot=0.0):
    """Overlaid golden spirals: m arms of each wind, LEDs strung along the arms, so the arcs themselves show."""
    best = []
    for sp in np.arange(1.9, 3.2, .05):
        raw = []
        for w in (1, -1):
            for i in range(m):
                phase = i * 2*math.pi/m + rot
                s, r = 0.0, RMAX
                while r > 1.5:
                    t = w * math.log(r) / B + phase
                    raw.append((r*math.cos(t), r*math.sin(t), t + w*math.atan(1/B) + math.radians(45)))
                    r -= sp * B / math.sqrt(1 + B*B)
        raw.sort(key=lambda p: -math.hypot(p[0], p[1]))
        raw = [p for p in raw if keep_ok(p, mode, margin)]
        kept = thin(raw, THIN, TARGET)
        if len(kept) >= TARGET:
            best = kept
        elif len(kept) > len(best):
            best = kept
    return best[:TARGET]

# ---------------------------------------------------------------- drawing

ARM = {}

def fam(p):
    """Colour for the lit preview: by spiral arm, 13 of one wind, so the eye sees what firmware could do."""
    k = (round(p[0], 4), round(p[1], 4))
    if k in ARM:
        return ARM[k]
    r, t = math.hypot(p[0], p[1]), math.atan2(p[1], p[0])
    u = (t - math.log(max(r, .5)) / B) / (2*math.pi) * 13
    v = (t + math.log(max(r, .5)) / B) / (2*math.pi) * 13
    return (math.floor(u) % 3 == 0, math.floor(v) % 3 == 0)

def svg(name, title, pts, st, mode, margin):
    S, W = 19, 800
    C = W/2
    X = lambda v: C + v*S
    Y = lambda v: C + v*S
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" font-family="system-ui,sans-serif" font-size="13">',
         f'<rect width="{W}" height="{W}" fill="#0b0d10"/><circle cx="{C}" cy="{C}" r="{R*S}" fill="#14181d" stroke="#6b7480" stroke-width="2"/>']
    # back-side connector, seen through the board
    o.append(f'<rect x="{X(Jx-4.47)}" y="{Y(Jy-4.0)}" width="{8.94*S}" height="{7.65*S}" fill="#2fb7ff" fill-opacity=".10" stroke="#2fb7ff" stroke-width="1.5" stroke-dasharray="6 4"/>')
    for i in range(16):
        px = Jx + (i-7.5)*.5
        o.append(f'<rect x="{X(px-.15)}" y="{Y(Jy-4.6)}" width="{.3*S}" height="{1.1*S}" fill="#2fb7ff" fill-opacity=".45"/>')
    if mode == "bay":
        y0 = Jy-4.045-.55-margin
        o.append(f'<rect x="{X(Jx-4.82-margin)}" y="{Y(y0)}" width="{(9.64+2*margin)*S}" height="{(R-y0+1)*S}" fill="none" stroke="#ffb020" stroke-width="1.5"/>')
    for h in HOLE_LIST:
        o.append(f'<rect x="{X(h[0]-h[2]-margin)}" y="{Y(h[1]-h[3]-margin)}" width="{2*(h[2]+margin)*S}" height="{2*(h[3]+margin)*S}" rx="{margin*S}" fill="#ffb020" fill-opacity=".20" stroke="#ffb020" stroke-width="1"/>')
        o.append(f'<rect x="{X(h[0]-h[2])}" y="{Y(h[1]-h[3])}" width="{2*h[2]*S}" height="{2*h[3]*S}" rx="{min(h[2],h[3])*S}" fill="#000" stroke="#d8dde3"/>')
    for p in pts:
        a, b = fam(p)
        col = {(0, 0): "#3b4149", (1, 0): "#ff6b8a", (0, 1): "#5fd0ff", (1, 1): "#ffffff"}[(int(a), int(b))]
        c = " ".join(f"{X(u):.1f},{Y(v):.1f}" for u, v in land(p[0], p[1], p[2]))
        o.append(f'<polygon points="{c}" fill="{col}"/>')
    o.append(f'<text x="{X(Jx)}" y="{Y(Jy+1.2)}" text-anchor="middle" fill="#8fd8ff">USB-C on the back</text>')
    o.append('</svg>')
    (OUT / f"{name}.svg").write_text("\n".join(o))

PLANS = [
    ("grid-holes", "A. 2 mm grid, wider hole margin", lambda: grid("holes", .6), "holes", .6, "Straight columns and rows; the routing plan already worked out still applies."),
    ("grid-bay", "B. 2 mm grid, clear bay over USB-C", lambda: grid("bay", .3), "bay", .3, "A clean notch instead of scattered gaps. Only 228 sites fit on this grid."),
    ("vogel-turned", "C. Sunflower, LEDs turned with their angle", None, "holes", .6, "Golden angle. Opposing spirals appear by themselves, 21 and 34 of each wind near the rim, 8 and 13 near the centre. Pink and blue mark every third arm of each wind."),
    ("vogel-turned-bay", "D. Sunflower, turned, clear bay over USB-C", None, "bay", .3, "Same lattice with a deliberate notch: it packs tighter to make up the 234."),
    ("vogel-holes", "E. Sunflower, LEDs all square to the board", None, "holes", .6, "Simplest to assemble, but corners nearly touch, too tight to route."),
    ("nested", "F. Nested golden spirals", None, "holes", .6, "True golden spirals with 5, 8, 13 then 21 arms in nested zones; an LED at each crossing of opposing arms."),
    ("arms-13", "G. Overlaid opposing arms, 13 each way", None, "holes", .6, "LEDs strung along true golden arcs, clockwise and anticlockwise. The arcs show as lines, with diamond gaps between."),
    ("arms-21", "H. Overlaid opposing arms, 21 each way", None, "holes", .6, "Finer weave of the same idea."),
]

def page(res):
    rows = ""
    cards = ""
    for r_ in res:
        ok = r_["land_gap"] >= MIN_GAP
        verdict = "routable gap" if ok else "too tight to route"
        short = TARGET - r_["count"]
        cnt = f'{r_["count"]}' + (f' <span class="bad">({short} short)</span>' if short else "")
        rows += (f'<tr><td>{r_["title"]}</td><td class="n">{cnt}</td><td class="n">{r_["spacing_min"]:.2f}</td><td class="n {"" if ok else "bad"}">{r_["land_gap"]:.2f}</td>'
                 f'<td class="n">{r_["usb_hole_gap"]:.2f}</td><td class="n">{r_["edge"]:.2f}</td><td class="{"" if ok else "bad"}">{verdict}</td></tr>')
        cards += (f'<figure><a href="{r_["name"]}.svg"><img src="{r_["name"]}.svg" alt="{r_["title"]}"></a><figcaption><b>{r_["title"]}</b>'
                  f'<br>{cnt} LEDs. {r_["note"]}</figcaption></figure>')
    (OUT / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>round-pendant: LED pattern study</title><style>
body{{margin:0;background:#0e1116;color:#e6e9ee;font:15px/1.5 system-ui,sans-serif;padding:1.2rem}}main{{max-width:1200px;margin:auto}}
h1{{font-size:1.4rem;margin:.2rem 0}}p{{color:#a8b1bd;max-width:62rem}}table{{border-collapse:collapse;margin:1rem 0;width:100%}}th,td{{padding:.35rem .6rem;border-bottom:1px solid #262c36;text-align:left}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}th{{color:#8b94a3;font-weight:600;font-size:.85rem}}.bad{{color:#ff8f70}}
.g{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}figure{{margin:0;background:#171b22;border:1px solid #262c36;border-radius:10px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:.6rem .8rem;font-size:.9rem;color:#c6ccd5}}figcaption b{{color:#fff}}
.k span{{display:inline-block;margin-right:1rem}}.s{{display:inline-block;width:.8em;height:.8em;margin-right:.3em;border-radius:2px}}
</style></head><body><main><h1>LED pattern study</h1>
<p>38 mm board, seen from the LED side, with the back-side USB-C drawn through it. A study only: the board in hw/ is unchanged. Colours mark spiral arms, as firmware could light them. Land gaps come from a geometry model, and none of these has been routed. Grid plans use a 2 mm pitch.</p>
<p class="k"><span><i class="s" style="background:#ff6b8a"></i>one wind</span><span><i class="s" style="background:#5fd0ff"></i>opposing wind</span><span><i class="s" style="background:#fff"></i>both</span><span><i class="s" style="background:#3b4149"></i>other LEDs</span><span><i class="s" style="background:#000;border:1px solid #d8dde3"></i>through-hole</span><span><i class="s" style="background:#ffb020"></i>LED keepout</span><span><i class="s" style="background:#2fb7ff"></i>USB-C, back</span></p>
<table><tr><th>Plan</th><th class="n">LEDs</th><th class="n">Min pitch, mm</th><th class="n">Min pad gap, mm</th><th class="n">LED to USB-C hole, mm</th><th class="n">LED to edge, mm</th><th>Pad gap</th></tr>{rows}</table>
<div class="g">{cards}</div></main></body></html>""")


def main():
    res = []
    for name, title, fn, mode, margin, note in PLANS:
        if fn:
            pts, rot = fn(), 0
        elif name.startswith("vogel"):
            pts, rot = best_rotation(lambda r: vogel(mode, margin, "turned" in name, r))
        elif name == "nested":
            pts, rot = nested(mode, margin), 0
        else:
            pts, rot = arms(mode, margin, int(name.split("-")[1])), 0
        st = stats(pts)
        svg(name, title, pts, st, mode, margin)
        res.append(dict(name=name, title=title, note=note, mode=mode, margin=margin, rotation=rot, **st))
        print(name, st, "rot", rot, flush=True)
    res = json.loads(json.dumps(res, default=float))
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    page(res)

if __name__ == "__main__":
    main()
