# Two-board stack: report

Saved from crunch-stack's final message, because the harness blocked it from writing this file. Numbers are the agent's and haven't been rechecked. The run table is in `runs.tsv`.

**Recommendation: shelve the two-board idea and keep 8 layers as the main effort.** The owner hasn't decided yet.

LED board only, 1200 s:

| Board | Open | Plane | Errors | Vias |
|---|---:|---:|---:|---:|
| `c-stack-4a`, GND on In1 | 91 | 10 | 44 | 776 |
| `c-stack-4b`, no plane | 56 | 0 | 68 | 764 |

- **What's in the 56:** 37 CS, 6 SW, 13 VSYS, GND and control. 4b has no plane: GND is 144 mm of 0.2 mm track, and 78 of VSYS's 89 mm is under the 0.3 mm rule. The drivers' heat path and return are unsolved.
- **Reach and drop:** farthest LED 26.4 mm, was 23.1. SW nets hold up to 0.83 Ω of copper on this incomplete route, against a 0.16 V path budget at 494 mA. Needs checking.
- **Processor half:** all 75 parts fit by bounding box (389 of 511 mm²), but not acceptably: the LDO and its caps moved about 9-11 mm, with 15 courtyard overlaps. Its one real gain is no foreign vias around the RP2350.
- **Crossings:** 16 pads: 3 VSYS, 3 GND, +3V3, I2C ×2, SDB ×2, INTB ×2, D235 ×3. D235 is under 1 mm from a seam on the diameter. The two boards' pad lists still need matching.
- **JLC join:** castellations need Standard PCBA and a board of at least 0.6 mm. No board-on-board service found, so assume hand soldering.
- **Cost:** extra setup and stencil $33.77 per order; extra X-ray $1.64 per board if charged per board; 4-layer via-in-pad charged per a 2022 notice, price unknown; bare-board prices unknown, no live quote.
- **Height and drop:** about 0.7-0.9 mm taller (estimate). Drop survival untested; a straight-edge joint probably needs adhesive.

**What would change the recommendation:** under 10 opens with a real GND path, plus a quote showing a clear saving.

**Not done:** 6-layer reference (`c-stack-6r`), LED-board improvements, any routing of the processor half (`c-stack-p1`), `pad_joints`.

Files: this folder and `hw/round-pendant/c-stack-4b/`.
