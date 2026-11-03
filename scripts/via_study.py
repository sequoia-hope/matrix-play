#!/usr/bin/env python3
"""via_study.py -- phase 4: where do through vias for 234 LED anodes land under the bottom-side QFNs?

Every LED has one anode via at pad 3 (-0.4, +0.4 from the LED centre, top view). The grid is periodic at
2 mm, so a chip's conflicts depend only on its centre modulo 2 mm. For each chip this finds the centre
(mod 2 mm) with the fewest vias touching a signal pad, for a via 0.30/0.15 mm and 0.09 mm clearance.
A via that touches no pad lands either in the exposed pad's zone or in clear board.
"""
import itertools, json, math
from pathlib import Path

CLEAR = 0.09; VIA_R = 0.15

def qfn_pads(pad_center=3.395, length=0.74, width=0.22, pitch=0.4, n=15):
    """Signal pads of a 60-pin QFN, as rectangles (cx, cy, hx, hy) around the chip centre."""
    out = []
    for i in range(n):
        t = (i - (n - 1) / 2) * pitch
        out += [(-pad_center, t, length / 2, width / 2), (pad_center, t, length / 2, width / 2),
                (t, -pad_center, width / 2, length / 2), (t, pad_center, width / 2, length / 2)]
    return out

def hit(px, py, r):
    return max(abs(px - r[0]) - r[2], 0) ** 2 + max(abs(py - r[1]) - r[3], 0) ** 2 < (VIA_R + CLEAR) ** 2

CHIPS = {"IS31FL3741A": (qfn_pads(), 2.7), "RP2350A": (qfn_pads(3.45, 0.8, 0.2), 1.7)}

def conflicts(chip, cx, cy, slide=0.0):
    """Vias under a chip whose centre is (cx, cy) relative to a via. Returns (on pads, inside the EP, in the ring between)."""
    pads, ep = CHIPS[chip]
    on, in_ep, ring = 0, 0, 0
    for i, j in itertools.product(range(-3, 4), repeat=2):
        vx, vy = i * 2 - cx, j * 2 - cy
        if max(abs(vx), abs(vy)) > 4.2:
            continue
        spots = [(vx + dx, vy + dy) for dx in (-slide, 0, slide) for dy in (-slide, 0, slide)] if slide else [(vx, vy)]
        if all(any(hit(a, b, r) for r in pads) for a, b in spots):
            on += 1
        elif max(abs(vx), abs(vy)) <= ep + VIA_R + CLEAR:
            in_ep += 1
        elif max(abs(vx), abs(vy)) <= 3.0:
            ring += 1
    return on, in_ep, ring

result = {}
for chip in CHIPS:
    for slide, tag in ((0.0, "via in pad, centred"), (0.075, "via in pad, up to 0.075 off centre"), (0.5, "via on a stub up to 0.5 mm off the pad")):
        best = None
        for a, b in itertools.product(range(0, 40), repeat=2):
            cx, cy = a * 0.05, b * 0.05
            c = conflicts(chip, cx, cy, slide)
            key = (c[0], c[1], c[2])
            if best is None or key < best[0]:
                best = (key, (round(cx, 2), round(cy, 2)))
        result[f"{chip} | {tag}"] = {"on_pads": best[0][0], "in_exposed_pad": best[0][1], "in_ring": best[0][2], "centre_mod_2mm": best[1]}
for k, v in result.items():
    print(k, v)

# USB-C HRO TYPE-C-31-M-12 through features relative to LED land squares, connector axis x, best offset.
LAND = 0.625
features = [(-4.32, 1.05, 0.5, 0.8), (4.32, 1.05, 0.5, 0.8), (-4.32, -3.13, 0.5, 1.05), (4.32, -3.13, 0.5, 1.05), (-2.89, -2.6, 0.325, 0.325), (2.89, -2.6, 0.325, 0.325)]
clr = 0.15
def usb_hits(ox, oy):
    n = set()
    for fx, fy, hx, hy in features:
        for i, j in itertools.product(range(-6, 7), repeat=2):
            lx, ly = i * 2 - ox, j * 2 - oy
            if abs(fx - lx) < hx + LAND + clr and abs(fy - ly) < hy + LAND + clr:
                n.add((i, j))
    return len(n)
best = min(((usb_hits(a * 0.05, b * 0.05), round(a * 0.05, 2), round(b * 0.05, 2)) for a, b in itertools.product(range(40), repeat=2)))
print("USB-C HRO M-12: fewest LED sites displaced", best[0], "at connector axis offset mod 2 mm", best[1:], "worst", max(usb_hits(a * 0.05, b * 0.05) for a, b in itertools.product(range(40), repeat=2)))
result["usb"] = {"min_sites": best[0], "offset": best[1:]}
Path("design/study/via_study.json").write_text(json.dumps(result, indent=1))
