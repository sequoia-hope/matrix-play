#!/usr/bin/env bash
# build_proc.sh VARIANT: unrouted processor half, 4 layers. Thermal vias and EP as the footprint gives them (no foreign vias here, so EP solid; the skill's stitch step isn't run).
set -euo pipefail
R=/home/sequoia/pcb/round-pendant; cd $R
export PENDANT_VARIANT=$1 PENDANT_MAP=$R/design/study/crunch/stack/fan_s.csv PENDANT_PLACE=place_c STACK_U1=-9,8,0 STACK_U2=8,8,0
D=hw/round-pendant/$1; S=hw/round-pendant/c; B=scripts/crunch/stack/board_stack.py
[ -e "$D" ] && { echo "exists $D" >&2; exit 2; }
mkdir -p $D/route; cp $S/*.kicad_sch $S/round-pendant.kicad_pro $S/round-pendant.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/; cp -r $S/lib $D/lib
python3 scripts/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1; python3 $B place_c | tail -1
python3 scripts/crunch/stack/proc_place.py place | grep -E "legal|placed"
python3 scripts/crunch/stack/proc_place.py zones | tail -1
python3 $B rules
python3 scripts/crunch/stack/to4.py $D/round-pendant.kicad_pcb 0.8
cp $D/round-pendant.kicad_pcb $D/route/preroute.kicad_pcb
