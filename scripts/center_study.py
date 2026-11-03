#!/usr/bin/env python3
"""center_study.py -- rotationally symmetric centres for the turned sunflower. A study: it doesn't touch hw/ or the matrix maps.

The innermost LEDs of the lattice become concentric rings, the same count of them, so 234 stays 234. The rim, the button nudges and the LEDs outside the transition
band don't move. A hill climb sets ring radii and phases (one value per ring, so the symmetry stays exact) and eases the band next to the rings to open up pad gaps.
Gaps are between LED land squares, as in pattern_study. Writes design/study/center/. Deterministic.
"""
import json, math, random
from pathlib import Path
import pattern_study as ps
from sunflower import lattice, nudge, RMAX, BUTTONS, PEG_R, PEG_SPAN

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/center"
GOAL = .42
PLANS = [
    ("c5-small", "5-fold, 5 + 10", (5, 10), 5),
    ("c5", "5-fold, 5 + 10 + 15", (5, 10, 15), 5),
    ("c6", "6-fold, 6 + 12 + 18", (6, 12, 18), 6),
    ("c8", "8-fold, 8 + 16", (8, 16), 8),
    ("fib", "Fibonacci rings, 5 + 8 + 13", (5, 8, 13), 1),
]


def base():
    pts = lattice(); moved = nudge(pts)
    return [tuple(p) for p in pts], set(moved)


def ring_pts(count, r, phi):
    return [(r*math.cos(phi+2*math.pi*k/count), r*math.sin(phi+2*math.pi*k/count), phi+2*math.pi*k/count+math.radians(45)) for k in range(count)]


def near_gap(p, q):
    return 9.0 if math.hypot(p[0]-q[0], p[1]-q[1]) > 3.4 else ps.sat_gap(ps.land(*p), ps.land(*q))


def min_gap(pts):
    return min(near_gap(pts[i], pts[j]) for i in range(len(pts)) for j in range(i+1, len(pts)))


def penalty(p, others):
    return sum(max(0, GOAL-near_gap(p, q))**2 for q in others)


def solve(rings, frozen, seed=11, iters=15000):
    rnd = random.Random(seed)
    src, nudged = base()
    m = sum(rings); c = RMAX/math.sqrt(235)
    params = []; a = 1
    for k, n in enumerate(rings):
        params.append([c*math.sqrt(a+(n-1)/2), k*.3]); a += n
    outer = src[m:]
    # The band that may ease: the next two rings' worth of LEDs, nudged LEDs excluded.
    band = [i for i in range(min(int(m*1.5), len(outer))) if i+m not in nudged]
    fixed = [outer[i] for i in range(len(outer)) if i not in band and math.hypot(*outer[i][:2]) < params[-1][0]+7]
    pos = {i: outer[i] for i in band}; home = dict(pos)
    def ring_list():
        return [q for (r, ph), n in zip(params, rings) for q in ring_pts(n, r, ph)]
    def total():
        rs = ring_list(); ps_ = list(pos.values())
        all_ = rs+ps_; t = 0
        for i in range(len(all_)):
            for j in range(i+1, len(all_)):
                t += max(0, GOAL-near_gap(all_[i], all_[j]))**2
            t += penalty(all_[i], fixed)
        return t
    for it in range(iters):
        T = .15*(1-it/iters)+.005
        if rnd.random() < .25:
            k = rnd.randrange(len(rings)); old = params[k][:]; cost = total()
            params[k][0] += rnd.gauss(0, T); params[k][1] += rnd.gauss(0, T/max(params[k][0], 1))
            new = total()
            if new > cost: params[k] = old
        else:
            i = rnd.choice(band); old = pos[i]
            x, y = old[0]+rnd.gauss(0, T), old[1]+rnd.gauss(0, T)
            cand = (x, y, old[2])
            others = [q for j, q in pos.items() if j != i]+ring_list()+fixed
            d = penalty(cand, others)-penalty(old, others)
            d += .002*(math.dist(cand[:2], home[i][:2])**2-math.dist(old[:2], home[i][:2])**2)
            if d <= 0:
                pos[i] = cand
    outer2 = [pos.get(i, outer[i]) for i in range(len(outer))]
    r_list = ring_list()
    moved = [math.dist(outer2[i][:2], outer[i][:2]) for i in band]
    return r_list, outer2, params, moved


def symmetric_radius(pts, fold):
    """Largest radius within which turning by 360/fold lands every LED on another, to 0.05 mm."""
    if fold < 2:
        return 0.0
    a = 2*math.pi/fold; best = 0
    order = sorted(pts, key=lambda p: math.hypot(p[0], p[1]))
    for p in order:
        x, y = p[0]*math.cos(a)-p[1]*math.sin(a), p[0]*math.sin(a)+p[1]*math.cos(a)
        if min(math.hypot(x-q[0], y-q[1]) for q in pts) > .05:
            break
        best = math.hypot(p[0], p[1])
    return best


def svg(path, pts, rings_n, zoom):
    half = 19.5 if not zoom else 8.5; S = 380/half; C = 380; X = lambda v: C+v*S
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 760">', '<rect width="760" height="760" fill="#0b0d10"/>',
         f'<circle cx="{C}" cy="{C}" r="{19*S}" fill="#14181d" stroke="#6b7480" stroke-width="2"/>']
    if not zoom:
        for deg, rc in BUTTONS.values():
            t = math.radians(deg)
            for d in (-1, 1):
                o.append(f'<circle cx="{X((rc+d*PEG_SPAN)*math.cos(t)):.1f}" cy="{X((rc+d*PEG_SPAN)*math.sin(t)):.1f}" r="{PEG_R*S:.1f}" fill="#000" stroke="#d8dde3"/>')
    a = 0; marks = []
    for n in rings_n:
        marks += [["#ff6b8a", "#5fd0ff", "#ffd166"][len(marks) and rings_n.index(n) % 3 or 0]]*n; a += n
    for i, p in enumerate(pts):
        col = marks[i] if i < len(marks) else "#59626e"
        o.append('<polygon points="'+" ".join(f"{X(u):.1f},{X(v):.1f}" for u, v in ps.land(*p))+f'" fill="{col}"/>')
    o.append('</svg>')
    path.write_text("\n".join(o))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src, _ = base()
    res = [dict(name="now", title="Now: plain sunflower", rings=[], count=234, gap=round(min_gap(src), 3), centre=round(2*(min(math.hypot(p[0], p[1]) for p in src)-.884), 2), sym=0.0, moved=0, worst=0.0)]
    svg(OUT/"now.svg", src, (), False); svg(OUT/"now-zoom.svg", src, (), True)
    for name, title, rings, fold in PLANS:
        r_list, outer, params, moved = solve(rings, fold)
        pts = r_list+outer
        assert len(pts) == 234
        svg(OUT/f"{name}.svg", pts, rings, False); svg(OUT/f"{name}-zoom.svg", pts, rings, True)
        (OUT/f"{name}.json").write_text(json.dumps(pts))
        sym = symmetric_radius(pts, fold)
        res.append(dict(name=name, title=title, rings=list(rings), count=len(pts), gap=round(min_gap(pts), 3), centre=round(2*(min(math.hypot(p[0], p[1]) for p in pts)-.884), 2),
                        sym=round(sym, 1), moved=sum(d > .01 for d in moved), worst=round(max(moved or [0]), 2)))
        print(res[-1], flush=True)
    (OUT/"results.json").write_text(json.dumps(res, indent=1))
    rows = "".join(f'<tr><td>{r["title"]}</td><td class="n">{r["count"]}</td><td class="n">{r["gap"]:.2f}</td><td class="n">{r["centre"]:.1f}</td><td class="n">{r["sym"] or "none"}</td><td class="n">{r["moved"]}</td><td class="n">{r["worst"]:.2f}</td></tr>' for r in res)
    cards = "".join(f'<figure><a href="{r["name"]}-zoom.svg"><img src="{r["name"]}-zoom.svg" alt="{r["title"]}, centre"></a><a href="{r["name"]}.svg"><img src="{r["name"]}.svg" alt="{r["title"]}, whole board"></a><figcaption><b>{r["title"]}</b><br>Tightest pad gap {r["gap"]:.2f} mm, clear centre {r["centre"]:.1f} mm.</figcaption></figure>' for r in res)
    (OUT/"index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>round-pendant: symmetric centres</title><style>
body{{margin:0;background:#0e1116;color:#e6e9ee;font:15px/1.5 system-ui,sans-serif;padding:1.2rem}}main{{max-width:1200px;margin:auto}}h1{{font-size:1.4rem;margin:.2rem 0}}p{{color:#a8b1bd;max-width:62rem}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}th,td{{padding:.35rem .6rem;border-bottom:1px solid #262c36;text-align:left}}.n{{text-align:right;font-variant-numeric:tabular-nums}}th{{color:#8b94a3;font-weight:600;font-size:.85rem}}
.g{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}figure{{margin:0;background:#171b22;border:1px solid #262c36;border-radius:10px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:.6rem .8rem;font-size:.9rem;color:#c6ccd5}}figcaption b{{color:#fff}}
</style></head><body><main><h1>Symmetric centres for the sunflower</h1>
<p>A study only: no board has changed. Coloured LEDs are the new rings; each plan shows the centre, then the whole board. Gaps come from a geometry model, and nothing has been routed.</p>
<table><tr><th>Plan</th><th class="n">LEDs</th><th class="n">Min pad gap, mm</th><th class="n">Clear centre, mm</th><th class="n">Exactly symmetric out to, mm radius</th><th class="n">Sunflower LEDs eased</th><th class="n">Largest move, mm</th></tr>{rows}</table>
<div class="g">{cards}</div></main></body></html>""")


if __name__ == "__main__":
    main()
