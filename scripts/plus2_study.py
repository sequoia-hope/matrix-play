#!/usr/bin/env python3
"""plus2_study.py -- the plain sunflower with two extra LEDs in the middle. A study: it doesn't touch hw/ or the matrix maps.

    "fixed": the two best spots with no other LED moved.
    "eased": neighbours within EASE_R mm may shift to reach a pad gap of GOAL, the plain sunflower's tightest.
    plus2_study.py one: one extra LED, nothing moved.
    plus2_study.py tweak: the eased pair slid up the page, lower LED turned, neighbours making room.
Gaps are between LED land squares, as in center_study. Writes design/study/center-plus2/. Deterministic.
"""
import json, math, random, sys
from pathlib import Path
import pattern_study as ps
from center_study import base, min_gap, near_gap, svg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design/study/center-plus2"
GOAL, EASE_R = .36, 7.5


def spot_gap(p, pts):
    return min(near_gap(p, q) for q in pts)


def fixed(src):
    """Best pair on a 0.1 mm grid, each at any turn in 15 degree steps; gap to the old LEDs and to each other."""
    near = [p for p in src if math.hypot(p[0], p[1]) < 6]
    cands = []
    for i in range(-30, 31):
        for j in range(-30, 31):
            x, y = i/10, j/10
            if math.hypot(x, y) > 3:
                continue
            best = max(((spot_gap((x, y, math.radians(a)), near), a) for a in range(0, 90, 15)), key=lambda t: t[0])
            cands.append((best[0], (x, y, math.radians(best[1]))))
    cands.sort(key=lambda c: -c[0])
    top = cands[:250]; res = None
    for g1, a in top:
        for g2, b in top:
            g = min(g1, g2, near_gap(a, b))
            if res is None or g > res[0]:
                res = (g, a, b)
    return res


def eased(src, start, nudged, seed, iters=40000, pinned=False):
    rnd = random.Random(seed)
    move = {i: src[i] for i in range(len(src)) if math.hypot(src[i][0], src[i][1]) < EASE_R and i not in nudged}
    home = dict(move)
    rest = [src[i] for i in range(len(src)) if i not in move and math.hypot(src[i][0], src[i][1]) < EASE_R+3.5]
    new = list(start)
    def pen(p, others):
        return sum(max(0, GOAL-near_gap(p, q))**2 for q in others)
    keys = list(move)
    for it in range(iters):
        T = .2*(1-it/iters)+.004
        k = rnd.randrange(len(keys)+2*len(keys)//3)
        if k >= len(keys):
            if pinned:
                continue
            w = rnd.randrange(2); old = new[w]
            cand = (old[0]+rnd.gauss(0, T), old[1]+rnd.gauss(0, T), old[2]+rnd.gauss(0, T))
            others = list(move.values())+rest+[new[1-w]]
            if pen(cand, others) <= pen(old, others):
                new[w] = cand
        else:
            i = keys[k]; old = move[i]
            cand = (old[0]+rnd.gauss(0, T), old[1]+rnd.gauss(0, T), old[2])
            others = [q for j, q in move.items() if j != i]+rest+new
            d = pen(cand, others)-pen(old, others)+.002*(math.dist(cand[:2], home[i][:2])**2-math.dist(old[:2], home[i][:2])**2)
            if d <= 0:
                move[i] = cand
    pts = [move.get(i, src[i]) for i in range(len(src))]
    shift = [math.dist(pts[i][:2], src[i][:2]) for i in move]
    return new, pts, shift


def page(res):
    rows = "".join(f'<tr><td>{r["title"]}</td><td class="n">{r["count"]}</td><td class="n">{r["gap"]:.2f}</td><td class="n">{r["moved"]}</td><td class="n">{r["worst"]:.2f}</td></tr>' for r in res)
    cards = "".join(f'<figure><a href="{r["name"]}-zoom.svg"><img src="{r["name"]}-zoom.svg" alt="{r["title"]}, centre"></a><a href="{r["name"]}.svg"><img src="{r["name"]}.svg" alt="{r["title"]}, whole board"></a><figcaption><b>{r["title"]}</b><br>Tightest pad gap {r["gap"]:.2f} mm.</figcaption></figure>' for r in res)
    (OUT/"index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>round-pendant: sunflower plus 1 or 2 LEDs</title><style>
body{{margin:0;background:#0e1116;color:#e6e9ee;font:15px/1.5 system-ui,sans-serif;padding:1.2rem}}main{{max-width:1200px;margin:auto}}h1{{font-size:1.4rem;margin:.2rem 0}}p{{color:#a8b1bd;max-width:62rem}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}th,td{{padding:.35rem .6rem;border-bottom:1px solid #262c36;text-align:left}}.n{{text-align:right;font-variant-numeric:tabular-nums}}th{{color:#8b94a3;font-weight:600;font-size:.85rem}}
.g{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}}figure{{margin:0;background:#171b22;border:1px solid #262c36;border-radius:10px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:.6rem .8rem;font-size:.9rem;color:#c6ccd5}}figcaption b{{color:#fff}}
</style></head><body><main><h1>Plain sunflower plus 1 or 2 LEDs</h1>
<p>A study only: no board has changed. Extra LEDs are pink; each plan shows the centre, then the whole board. The two drivers have exactly 234 LED positions, so extra LEDs aren't wired to anything yet.</p>
<table><tr><th>Plan</th><th class="n">LEDs</th><th class="n">Min pad gap, mm</th><th class="n">Other LEDs moved</th><th class="n">Largest move, mm</th></tr>{rows}</table>
<div class="g">{cards}</div></main></body></html>""")


def tweak():
    """The eased pair slid up the page and the lower LED turned; the pair stays put and neighbours make room. Up is -y, as drawn."""
    src, nudged = base()
    old = json.load(open(OUT/"eased.json")); top, bot = old[0], old[1]
    res = [r for r in json.load(open(OUT/"results.json")) if not r["name"].startswith("slide")]
    for name, title, slide, deg in (("slide-a", "Slide 0.3 mm, lower LED parallel to upper", .3, None), ("slide-b", "Slide 0.5 mm, lower LED parallel to upper", .5, None), ("slide-c", "Slide 0.3 mm, lower LED at 60 degrees", .3, 60)):
        T = (top[0], top[1]-slide, top[2])
        B = (bot[0], bot[1]-slide, top[2] if deg is None else math.radians(deg))
        best = None
        for seed in (1, 2, 3, 4):
            new, pts, shift = eased(src, [T, B], nudged, seed, pinned=True)
            all_ = new+pts; gp = min_gap(all_)
            if best is None or (round(gp, 2), -sum(shift)) > (round(best[0], 2), -sum(best[2])):
                best = (gp, all_, shift)
        gp, all_, shift = best
        svg(OUT/f"{name}.svg", all_, (2,), False); svg(OUT/f"{name}-zoom.svg", all_, (2,), True)
        (OUT/f"{name}.json").write_text(json.dumps(all_))
        res.append(dict(name=name, title=title, count=236, gap=round(gp, 3), moved=sum(d > .01 for d in shift), worst=round(max(shift), 2)))
        print(res[-1], flush=True)
    (OUT/"results.json").write_text(json.dumps(res, indent=1))
    page(res)


def one():
    """One extra LED, nothing else moved: the widest gap on a fine grid of spots and turns."""
    src, _ = base()
    near = [q for q in src if math.hypot(q[0], q[1]) < 6]
    best = max(((spot_gap((i/20, j/20, math.radians(a)), near), (i/20, j/20, math.radians(a))) for i in range(-50, 51) for j in range(-50, 51) if i*i+j*j <= 2500 for a in range(0, 90, 5)), key=lambda t: t[0])
    pts = [best[1]]+src
    svg(OUT/"one.svg", pts, (1,), False); svg(OUT/"one-zoom.svg", pts, (1,), True)
    res = [r for r in json.load(open(OUT/"results.json")) if r["name"] != "one"]
    res.insert(1, dict(name="one", title="Plus 1, nothing else moved", count=235, gap=round(min_gap(pts), 3), moved=0, worst=0.0))
    (OUT/"results.json").write_text(json.dumps(res, indent=1))
    page(res)
    print(res[1], "at", [round(best[1][0], 2), round(best[1][1], 2), round(math.degrees(best[1][2]))], "gap to its neighbours", round(best[0], 3), "from centre", round(math.hypot(best[1][0], best[1][1]), 2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src, nudged = base()
    g, a, b = fixed(src)
    res = [dict(name="now", title="Now: plain sunflower, 234 LEDs", count=234, gap=round(min_gap(src), 3), moved=0, worst=0.0)]
    svg(OUT/"now.svg", src, (), False); svg(OUT/"now-zoom.svg", src, (), True)
    p = [a, b]+src
    svg(OUT/"fixed.svg", p, (2,), False); svg(OUT/"fixed-zoom.svg", p, (2,), True)
    res.append(dict(name="fixed", title="Plus 2, nothing else moved", count=236, gap=round(min_gap(p), 3), moved=0, worst=0.0))
    print(res[-1], flush=True)
    best = None
    for seed in (1, 2, 3, 4):
        new, pts, shift = eased(src, [a, b], nudged, seed)
        all_ = new+pts; gp = min_gap(all_); n = sum(d > .01 for d in shift)
        print(seed, round(gp, 3), n, round(max(shift), 2), flush=True)
        if best is None or (round(gp, 2), -sum(shift)) > (round(best[0], 2), -sum(best[2])):
            best = (gp, all_, shift)
    gp, all_, shift = best
    svg(OUT/"eased.svg", all_, (2,), False); svg(OUT/"eased-zoom.svg", all_, (2,), True)
    (OUT/"eased.json").write_text(json.dumps(all_))
    res.append(dict(name="eased", title="Plus 2, neighbours eased", count=236, gap=round(gp, 3), moved=sum(d > .01 for d in shift), worst=round(max(shift), 2)))
    (OUT/"results.json").write_text(json.dumps(res, indent=1))
    page(res)
    print(res)


if __name__ == "__main__":
    {"tweak": tweak, "one": one}.get(sys.argv[1] if sys.argv[1:] else "", main)()
