#!/usr/bin/env bash
# build.sh VARIANT MAP_CSV: build a new c-map variant's unrouted board. Same stages as scripts/build_board_b.sh with place_c, using this folder's board_map.py.
# Map CSV may carry a `turn` column (0-3): preferred LED turn, used if the anode via still fits (see board_map.anodes_b).
# Refuses a variant that already exists: every trial gets a new numbered folder, nothing is overwritten or deleted.
set -euo pipefail
R="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"; cd $R
export PENDANT_VARIANT=$1 PENDANT_MAP=$2 PENDANT_PLACE=place_c
D=hw/round-pendant/$1; S=hw/round-pendant/c; B=scripts/crunch/map/board_map.py
[ -e "$D" ] && { echo "build.sh: $D exists; use a new number" >&2; exit 2; }
mkdir -p $D/route; cp $S/*.kicad_sch $S/round-pendant.kicad_pro $S/round-pendant.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/; cp -r $S/lib $D/lib
cp $2 $D/map.csv
python3 scripts/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_c | tail -1
python3 $B anodes_b | grep -E 'anode vias|cathode|turns|tiles'
python3 $B zones_b | tail -1
python3 scripts/crunch/layers/zoneclear.py $D/round-pendant.kicad_pcb $D/round-pendant.kicad_pcb 0.2 0.09 | tail -1   # the v2 zone fix
python3 $B rules
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
