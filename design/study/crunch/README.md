# Routing crunch: variant c

Goal: a complete, clean route of `hw/round-pendant/c` that a person could still sign off. It's a tech demo and a board the owner truly wants, so try bold ideas, but report numbers honestly. A failed attack with clear evidence is a useful result.

## The board

38 mm round, 6 layers, 0.1/0.09 mm tracks, through vias, via-in-pad, JLC. 235 RGB LEDs on the LED side in a sunflower, everything else on the back. 234 sit in two IS31FL3741A matrices (13 triplets × 9 SW each, one per half of the disc). D235 sits near the centre at (0.05, -0.65), on RP2350 GPIO23-25 through R40-42. Each matrix LED has an anode (SW) and three cathodes (CS).

Coordinates are mm from the board centre (KiCad absolute 100, 100), y down, viewed from the LED side.

Read first, in this order:
- `design/decisions.md`: what was tried and why. Trials 1-7 all stalled at 100+ signal connections open.
- `.claude/skills/pcb-design/LESSONS.md`, then `.claude/skills/pcb-design/references/routing.md`.
- `.claude/skills/pcb-design/chips/rp2350.md` before touching anything near U3.
- `scripts/build_board_b.sh`, `scripts/board.py` (`place_b`, `place_c`, `anodes_b`, `zones_b`), `scripts/sunflower.py`, `scripts/spiral_map.py`.

## Known so far

| Trial | Map | Signal open | Plane open | Route-added errors | Vias |
|---|---|---:|---:|---:|---:|
| 5 | Annealed tree length | 122 | 82 | 49 | 921 |
| 6 | Spiral strips | 146 | 73 | 72 | 928 |
| 7 | Fan round each driver | 118 | 67 | 51 | 922 |

All on variant b with 234 LEDs, 1200 s, 4 threads, `--prefanout-mode inner`. Most opens are CS nets, and rip-up runs out of time with low yield. Plane-open figures here are inflated by a since-fixed 0.5 mm zone clearance bug: refilling trial 7 at 0.2 mm gives 2, with signal opens unchanged. Control-only routing (matrix pads off net) reaches 8 open in about 20 s, so the control nets alone aren't the problem. These logs also have about 450 "narrow pad joint" lines nobody has checked yet: `pad_joints.py` judges them.

Current plane layers: In2 GND; In4 VSYS with a +3V3 island. On B.Cu, U3 has a 1V1 ring and a 3V3 band. Rule areas: no In2 plane under LX; no tracks inside the U1, U2, U3 pad rings.

## Starting point

**Focus is now 8 layers (owner, 2026-11-03).** New work starts from `hw/round-pendant/c/route/preroute_8L.kicad_pcb` with its `.kicad_pro` and `.kicad_dru`: same as v3, with planes GND on In2 and VSYS/+3V3 on In5, routed with `--planes In2.Cu,In5.Cu`. Copy those three files over the v3 ones in the recipe below. Best so far, for comparison: 56 signal open, 9 plane, 55 errors, 961 vias at 1200 s (`c-layers-v3-8a`). Dielectric thicknesses are estimates; JLC publishes no 8-layer table.

The 6-layer starting point, for reference:

`hw/round-pendant/c/route/preroute_v3.kicad_pcb`, with `preroute_v3.kicad_pro` and `preroute_v3.kicad_dru` beside it (unrouted, fan map, 235 LEDs, zone clearances fixed, SW lines in class SW_SCAN at 0.1 mm). Older `preroute` and `preroute_v2` lack these fixes. Don't change anything under `hw/round-pendant/c`.

Make your own variant, named for your attack:

```bash
V=c-myattack-1; D=hw/round-pendant/$V; mkdir -p $D
cp hw/round-pendant/c/*.kicad_sch hw/round-pendant/c/fp-lib-table hw/round-pendant/c/sym-lib-table $D/
cp -r hw/round-pendant/c/lib $D/lib
cp hw/round-pendant/c/route/preroute_v3.kicad_pcb $D/round-pendant.kicad_pcb        # or rebuild it:
cp hw/round-pendant/c/route/preroute_v3.kicad_pro $D/round-pendant.kicad_pro
cp hw/round-pendant/c/route/preroute_v3.kicad_dru $D/round-pendant.kicad_dru
# PENDANT_VARIANT=$V PENDANT_PLACE=place_c PENDANT_MAP=design/study/b/spiral/build/chip_lsa.csv scripts/build_board_b.sh
```

## Routing and scoring

```bash
~/.claude/bin/reserve -c 4 --here -l "round-pendant crunch: <what>" -- python3 .claude/skills/pcb-design/scripts/autoroute.py hw/round-pendant/$V --planes In2.Cu,In4.Cu --seeds 1 --timeout 1200 --threads 4 --memory 12G --extra "--prefanout-mode inner"
```

Results go to `hw/round-pendant/$V/route/autoroute.json` and `s0.log`. KiCad's judgement in that JSON is the score, not the router's count: `open`, `plane_open`, `new_errors`, `vias`. The target is all of the first three at 0. Also run `.claude/skills/pcb-design/scripts/pad_joints.py` on your best boards. Router flags: `scripts/route.sh --build` prints the binary path; run it with `route --help`.

A variant's result only counts for comparison if you record exactly what differs from the starting point. Keep every trial's board; never overwrite one.

## Rules

- **Machine**: this host is shared. Every route or sweep goes through `~/.claude/bin/reserve`, at most 5 cores per booking, and use `--here` (the project isn't on the second build machine). Exit 75 means it didn't run: say so, don't rerun unbooked. Use `run_in_background` for anything long, and don't poll with sleep. Don't start more than 2 bookings at once.
- **Budget**: up to about 3 hours of wall clock. Stop earlier on a clean route, or when more runs clearly won't change your conclusion. Prefer short, comparable runs first, then spend long runs only on what's working.
- **Stay in your lane**: write only under `hw/round-pendant/c-<attack>-*`, `scripts/crunch/<attack>/` and `design/study/crunch/<attack>/`. Copy a shared script into your folder to change it. Don't edit `scripts/*.py` or `*.sh` directly, `vendor/`, `viewer/`, `.claude/`, `design/status.json`, `design/decisions.md`, or any `hw/` folder you didn't create. Don't commit.
- **Keep the design true**: 235 LEDs, the same schematic connectivity, 38 mm, 6 or 8 layers (owner approved 8 on 2026-11-03; 6 is still better if it works), through vias only (blind and buried vias ruled out by the owner), JLC limits, no new parts. Pad-gap minimum of 0.30 mm between LED lands. The owner's look matters, so any LED move over 0.3 mm or visible change to the sunflower gets called out in your report. Never move D235 without saying so: the owner picked that spot.
- **No quiet waivers**: don't relax a rule to get a number. If a relaxation seems worth it, try it, label it clearly, and report the number with and without it. Any change to the RP2350 reference layout goes in your report with what it risks.
- **Tool limits**: if ultraroute itself seems to be the limit (a bug, a missing option), note it with a repro for the owner rather than editing it.

- **No risky deletes**: no `rm -rf`, recursive or wildcard deletes. Make a new numbered folder, or `mv` old work into an `old/` folder inside your own variant.
- **Assume it can be done**: a stalled router run says the router stalled, not that no route exists. Don't report infeasibility without a real counting argument across a specific cut. When something stalls, try a bolder idea. Optimism goes into what you try, never into the numbers you report.

## Report

Keep a running table in `design/study/crunch/<attack>/report.md`. End with: best board path; its `open / plane_open / new_errors / vias`; `pad_joints` result; exact steps to reproduce; what changed from the starting point; electrical or visual cost; what you'd try next. Say plainly what didn't work and what you didn't check.
