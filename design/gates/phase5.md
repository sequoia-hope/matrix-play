# Gate 5: stackup and rules

Status: **passed**, main-model review per protocol.

- `stackup.md`: source and date recorded. Layer thicknesses are an estimate to be read from JLC's quote tool before fab.
- Impedance: no target. USB FS under the class widths, not impedance controlled.
- Fab minimums in the `.kicad_pro`; thresholds in `checks.toml`.
- Net classes: all classes from nets.csv exist. Script check of `pcbnew` net class against nets.csv for every row: 0 mismatches.
- `nets_check.py --rules` reports 149 `[netclass]` errors: it reads the class from `kicad-cli sch export netlist`, which returns Default for every net on this hierarchical schematic although the board and DRC see the right class. Cause not found; `sheets` list and explicit assignments don't change it. Logged in decisions.md. `[clearance]` at 0.09 vs derived 0.10 for SIGNAL: 0.09 is the fab floor, needed by R21.
- Custom rules in `.kicad_dru`, each citing its source. Rule areas added at phase 6.
- Severities listed in `stackup.md`.
- DRC on the stacked, unplaced board: no rule-definition errors; other findings meaningless until placement.
