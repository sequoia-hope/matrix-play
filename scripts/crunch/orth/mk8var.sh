#!/usr/bin/env bash
# mk8var.sh NEW BASE_VARIANT SEED.json [fix1]: 8-layer variant: BASE's board (6-layer, unrouted), through layers' mk8.py, optional fix1, then the seed copper.
set -euo pipefail; R=/home/sequoia/pcb/round-pendant; cd $R; O=scripts/crunch/orth; D=hw/round-pendant/$1; S=hw/round-pendant/c/route
$O/newvar.sh $2 $1
cp $S/preroute_8L.kicad_pro $D/round-pendant.kicad_pro; cp $S/preroute_8L.kicad_dru $D/round-pendant.kicad_dru
cp hw/round-pendant/$2/route/preroute.kicad_pcb $D/round-pendant.kicad_pcb
python3 scripts/crunch/layers/mk8.py $D/round-pendant.kicad_pcb --plane-clear .2 --rp-clear .09 | tail -1
[ "${4:-}" = fix1 ] && python3 $O/fix1.py $D/round-pendant.kicad_pcb $D/round-pendant.kicad_pcb $D/round-pendant.kicad_dru
if [ "$3" != none ]; then python3 $O/apply_seed.py $D/round-pendant.kicad_pcb $3 $D/round-pendant.kicad_pcb; cp $3 $D/seed.json; fi
cp $D/round-pendant.kicad_pcb $D/route/seeded.kicad_pcb
