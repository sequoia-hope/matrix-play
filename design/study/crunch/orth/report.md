# Seeded orthogonal pattern: report

Saved from crunch-orth's final message, because the harness blocked it from writing this file. Numbers are the agent's and haven't been rechecked.

**Conclusion:** the seeded pattern saves vias but doesn't finish the route, and it's not worth more runs for this revision. `c-placement-y17` stays the board.

| Variant | Time | Open | Plane | Errors | Vias |
|---|---|---:|---:|---:|---:|
| c-orth-0 (v3, 6-layer) | 600 s | 109 | 3 | 63 | 940 |
| c-orth-8a (seed) | 600 s | 84 | 11 | 59 | 672 |
| c-orth-8b (seed + B.Cu fan-in) | 600 s | 85 | 20 | 70 | 654 |
| c-orth-8c (seed + pin vias) | 600 s | 72 | 18 | 82 | 710 |
| c-orth-y0 (y5 base, grid map, no seed) | 1200 s | 35 | 6 | 210 | 892 |
| c-orth-y1 (y5 base, seeded) | 1200 s | 59 | 7 | 104 | 781 |
| c-placement-y5, for comparison | 1200 s | 22 | 5 | 76 | 865 |

- **Best board:** none is complete. The lowest opens are `hw/round-pendant/c-orth-y0`. All boards checked (8a, 8b, 8c, y0, y1) pass `pad_joints`.
- **Gemini's premise:** false on v3, with a 3.3 mm median link, 15.7 mm max, and chains not monotonic in radius. The true grid map, `grid_c.csv` in this folder, has a 2.09 mm median and 3.85 mm max, with lands moved 0.0 mm.
- **Why it stalls:** the seed takes the driver via sites, so prefanout fails on 24 pins on y1 against 5 on y0. The seed lays 446-509 of 624 F.Cu links. On y1, 672/1471 mm of F.Cu and 515/721 mm of In1 survive unchanged, and tightening rewrites much of the rest.
- **`--adopt`:** works as documented.
- **Neck relaxation:** didn't clear the power `track_width` errors.

**For a later revision:** try the grid map unseeded on y17's placement, though y0 cost no fewer vias (892 against y17's 898), so a gain isn't shown yet. The seed only saves vias (781 against 892 on the same base). Seed only away from driver rings and reserve via sites first; reservation found only 51-55 of 96 sites.

**Not checked:** seeds other than 0, the unrouted c-orth-1 fix, SW IR drop, and the optical effect of turns. y1's seeded board starts with 3 DRC errors, which the score doesn't count.

Scripts are in `scripts/crunch/orth/`.
