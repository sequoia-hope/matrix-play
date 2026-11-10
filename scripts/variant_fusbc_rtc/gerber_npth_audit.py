#!/usr/bin/env python3
"""gerber_npth_audit.py — Independent 8-layer Gerber + split Excellon PTH/NPTH audit via gerbonara + Chrome
for round-pendant-f-usbc-rtc.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

warnings.simplefilter("ignore")
from gerbonara import LayerStack  # noqa: E402

ORDER_8L = [
    ("top", "silk"),
    ("top", "paste"),
    ("top", "mask"),
    ("top", "copper"),
    ("inner_1", "copper"),
    ("inner_2", "copper"),
    ("inner_3", "copper"),
    ("inner_4", "copper"),
    ("inner_5", "copper"),
    ("inner_6", "copper"),
    ("bottom", "copper"),
    ("bottom", "mask"),
    ("bottom", "paste"),
    ("bottom", "silk"),
]


def chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        if shutil.which(name):
            return name
    sys.exit("Needs Chrome or Chromium for headless SVG rasterization")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gerbers", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--width", type=int, default=420)
    args = ap.parse_args()

    browser = chrome()
    st = LayerStack.open(args.gerbers)
    args.out.mkdir(parents=True, exist_ok=True)

    layers = [(f"{s}_{u}", st.graphic_layers[(s, u)]) for s, u in ORDER_8L if (s, u) in st.graphic_layers]
    layers += [(f"drill_{d.original_path.stem}", d) for d in st.drill_layers]
    if st.outline:
        layers.append(("outline", st.outline))

    print(f"gerber_npth_audit: {args.gerbers} (board {st.board_name})")
    pngs = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, layer in layers:
            src = layer.original_path.name if layer.original_path else "?"
            print(f"  {name:28s} {src:36s} {len(layer.objects):5d} objects")
            if not layer.objects:
                continue
            svg = str(layer.to_svg(fg="black", bg="white", margin=1))
            w = re.search(r'width="([\d.]+)mm"', svg)
            h = re.search(r'height="([\d.]+)mm"', svg)
            ph = int(args.width * float(h.group(1)) / float(w.group(1))) if w and h else args.width
            svg = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{args.width}" height="{ph}"', svg, 1)
            f = Path(tmp) / f"{name}.svg"
            f.write_text(svg)
            png = args.out / f"{name}.png"
            subprocess.run(
                [
                    browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    f"--window-size={args.width},{ph}", f"--screenshot={png}", f.as_uri(),
                ],
                capture_output=True,
                timeout=120,
            )
            if png.exists():
                pngs.append(png)

        npth_holes = []
        for d in st.drill_layers:
            if "NPTH" in d.original_path.name.upper():
                for obj in d.objects:
                    npth_holes.append((float(obj.x), float(obj.y), float(getattr(obj.aperture, "diameter", 0.65))))

        print(f"\n=== INDEPENDENT GERBONARA NPTH DRILL AUDIT ({len(npth_holes)} holes in NPTH.drl) ===")
        for idx, (hx, hy, hd) in enumerate(npth_holes, 1):
            print(f"  NPTH #{idx}: Gerber (X={hx:.4f} mm, Y={hy:.4f} mm) => KiCad ({hx:.3f}, {-hy:.3f}) mm, dia={hd:.3f} mm")

        f_cu = st.graphic_layers[("top", "copper")]
        f_silk = st.graphic_layers[("top", "silk")]
        b_paste = st.graphic_layers[("bottom", "paste")]

        def raw_gerber_elems(layer, fg_col: str) -> str:
            s = str(layer.to_svg(fg=fg_col, bg="none", margin=0))
            s = re.sub(r"^.*?<svg[^>]*>\s*<g[^>]*>", "", s, count=1, flags=re.S)
            s = re.sub(r"</g>\s*</svg>\s*$", "", s, count=1, flags=re.S)
            return s

        overlays = []
        for idx, (hx, hy, hd) in enumerate(npth_holes, 1):
            sy = -hy
            if not (102.0 <= hx <= 114.0 and 106.2 <= sy <= 114.7):
                continue
            r = hd / 2.0
            r_clr = r + 0.200
            overlays.append(
                f'<circle cx="{hx:.4f}" cy="{sy:.4f}" r="{r:.4f}" fill="#ff1744" fill-opacity="0.58" stroke="#ff1744" stroke-width="0.035"/>'
                f'<circle cx="{hx:.4f}" cy="{sy:.4f}" r="{r_clr:.4f}" fill="none" stroke="#00e676" stroke-width="0.035" stroke-dasharray="0.09,0.06"/>'
                f'<text x="{hx + 0.62:.3f}" y="{sy + 0.12:.3f}" fill="#00e676" font-family="monospace" font-size="0.34" font-weight="bold">NPTH #{idx} Ø0.65 (+0.20 clr)</text>'
            )

        zoom_w, zoom_h = 1200, 850
        composite_svg = f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{zoom_w}" height="{zoom_h}" viewBox="102.0 106.2 12.0 8.5">
  <rect x="102.0" y="106.2" width="12.0" height="8.5" fill="#14181f"/>
  <g transform="scale(1, -1)" opacity="0.95">{raw_gerber_elems(f_cu, "#e6a800")}</g>
  <g transform="scale(1, -1)" opacity="0.78">{raw_gerber_elems(f_silk, "#f0f4ff")}</g>
  <g transform="scale(1, -1)" opacity="0.35">{raw_gerber_elems(b_paste, "#40c4ff")}</g>
  <g>{"".join(overlays)}</g>
</svg>
"""
        zsvg = Path(tmp) / "npth_zoom.svg"
        zsvg.write_text(composite_svg)
        zpng = args.out.parent / "npth-gerber-zoom.png"
        subprocess.run(
            [
                browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                f"--window-size={zoom_w},{zoom_h}", f"--screenshot={zpng}", zsvg.as_uri(),
            ],
            capture_output=True,
            timeout=120,
        )
        print(f"  Rendered NPTH vs F.Cu/F.Silk/B.Paste Gerber zoom -> {zpng}")

    if pngs and shutil.which("magick"):
        subprocess.run(["magick", *map(str, pngs), "+append", str(args.out / "sheet.png")], check=False)
    print(f"  {len(pngs)} Gerber layer PNGs + sheet.png written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
