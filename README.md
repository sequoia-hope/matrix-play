# Matrix Play

Small pocket boards covered in RGB LEDs, made to be played with. Each one is a KiCad design built
around an RP2350A, a LiPo cell and LED matrix drivers. This is a work in progress.

**Project site: <https://sequoia-hope.github.io/matrix-play/>**

The site shows every board family with interactive 3D and layer views, routing status and cost:

- [Board viewer index](https://sequoia-hope.github.io/matrix-play/viewer/index.html)
- [Pattern Explorer](https://sequoia-hope.github.io/matrix-play/design/study/pattern-explorer/):
  LED layout patterns (sunflower, Penrose, Voronoi, halftone, Lissajous) on the round and
  parallelogram outlines

## Board families

| Family | Size | LEDs | Example |
|---|---|---|---|
| Sunflower, 4-layer | Ø 38 mm round | 66–132 XL-1615 | [s2-110](https://sequoia-hope.github.io/matrix-play/viewer/sunflower-s2-110.html) |
| Round pendant | Ø 38 mm round | up to 235 | [round-pendant-e](https://sequoia-hope.github.io/matrix-play/viewer/round-pendant-e.html) |
| Skewed parallelogram, 4-layer | density sweep | 66–264 | [p2-132](https://sequoia-hope.github.io/matrix-play/viewer/parallelogram-p2-132.html) |
| Ultra-dense square | 20 × 20 mm window | 225–256 MHPA0808 | [s16-256](https://sequoia-hope.github.io/matrix-play/viewer/dense-square-s16-256.html) |

## Layout

- `hw/<family>/<variant>/`: KiCad projects
- `design/`: decisions log, status, parts, studies, renders
- `scripts/`: board generators, routing and checking scripts
- `index.html`: the project page (also served locally with `./serve.sh`)
- `vendor/`: pinned pcbview viewer and ultraroute router
