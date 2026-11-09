#!/usr/bin/env bash
# build.sh VARIANT MAP_CSV LAYERS PLANES : unrouted two-board LED board. Env: STACK_U1, STACK_U2 (x,y,rot; default both SW sides north), and board_stack's CATHODE_VIAS, EP_VIAS, PREF_STUB. LAYERS 4 or 6; PLANES gnd1|none|6ref.
set -euo pipefail
R="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"; cd $R
export PENDANT_VARIANT=$1 PENDANT_MAP=$(realpath $2) PENDANT_PLACE=place_c PLANES=$4
export STACK_U1=${STACK_U1:--9,8,0} STACK_U2=${STACK_U2:-8,8,0}
D=hw/round-pendant/$1; S=hw/round-pendant/c; B=scripts/crunch/stack/board_stack.py
[ -e "$D" ] && { echo "build.sh: $D exists" >&2; exit 2; }
mkdir -p $D/route; cp $S/*.kicad_sch $S/round-pendant.kicad_pro $S/round-pendant.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/; cp -r $S/lib $D/lib; cp $2 $D/map.csv
python3 scripts/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_c | tail -1
python3 $B prune | tail -1
python3 $B anodes_b | grep -E 'anode vias|cathode|turns|U1' | cut -c1-200
python3 $B zones_led | tail -1
python3 $B rules
[ "$3" = 4 ] && python3 scripts/crunch/stack/to4.py $D/round-pendant.kicad_pcb
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
echo "built $1: U1 $STACK_U1 U2 $STACK_U2 layers $3 planes $4" | tee $D/variant.txt
