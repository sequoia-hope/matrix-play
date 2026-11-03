# Gate 6: placement

Status: **awaiting user review of the render**. Two independent reviews done; fixes from the second verified by script, not re-reviewed.

## Checks (2026-11-02)
`kicad-cli pcb drc --severity-error`: silk_overlap 165, silk_over_copper 61 (phase 9), 499 unconnected (not routed). No courtyard, clearance, hole or short errors.
`placement_check.py`: PASS: 0 errors, 0 warnings, with decoupler limit 7 mm (decisions.md).
`sync_check.py`: PASS: 0 errors, 0 warnings.
`check_sch.py`: 0 ERC violations; matrix ok.
Vias: 234 anode vias, 8 of them 0.20/0.10 mm in U3's band. Thermal vias at LED channel crossings: U1 9, U2 9, U3 4, U5 1.
Triplet numbering by assignment: mean pin-to-triplet distance U1 6.93 mm, U2 4.09 mm.

## Datasheet layout guidance
RP2350 regulator block at reference offsets, mirrored, with C17 and R13 0.5 mm further out and R14, R15, C13 1.2 mm closer to the chip. Driver caps at PVCC and AVCC, RISET by its pin; thermal vias 9 against Lumissil's 16–25, phase 8. Charger: IN toward USB; caps within ~3 mm. XB9901A with R8, C6 close.

**Not yet on the board:** RP2350 reference zones and rule areas (1V1 ring, 3V3 band, LX, PGND, L1 window). First step of phase 7. The vendor's E spoke via will have to slide ~0.5 mm along the ring, off an anode via.

## Review findings (Fable, fresh context)
| Round | Sev | Finding | Resolution |
|---|---|---|---|
| 1 | BLOCKER | Crystal load caps on wrong pads | Fixed |
| 1 | BLOCKER | R32, C22 overlap | Fixed |
| 1 | MAJOR | CS pins didn't face their LEDs | Fixed: drivers turned so CS faces inward; triplets by assignment |
| 1 | MAJOR | 3V3 band severed by 0.25 mm vias | Fixed: 0.20/0.10 mm |
| 1 | MAJOR | No zones or rule areas | Phase 7 first step |
| 1 | MAJOR | Charger block | Fixed: turned, caps moved, EP whole. Reviewer's 4 thermal vias impossible, decisions.md |
| 1 | MAJOR | Fan-in blocked by bulk caps | Fixed: SW edge clear |
| 2 | MAJOR | U1 triplets mirrored | Fixed: assignment, 6.93 mm, equal to reviewer's optimum |
| 2 | MAJOR | Foreign via in LX corridor | Fixed: corridor keepout; C17, R13 moved |
| 2 | MAJOR | U3's south side walled | Fixed: R14, R15, C13 moved north 1.2 mm; flash moved south 0.2 mm |
| 2 | MINOR | R6, R7, TP3, TP5 far from their nets; R3 tight to U5; rim parts | Accepted: slow nets; DRC passes |
| 2 | NOTE | 12 vias under the flash, brief said 2 | Brief predates U4's final position; no EP copper there, so harmless |
