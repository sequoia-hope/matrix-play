#!/usr/bin/env bash
# mkvar.sh NAME [BOARD]: make hw/round-pendant/c-router-NAME from the crunch starting point (or BOARD)
set -euo pipefail
cd "$(dirname "$0")/../../.."
V=c-router-$1; D=hw/round-pendant/$V; S=hw/round-pendant/c
[ -e "$D" ] && { echo "exists: $D" >&2; exit 1; }
mkdir -p $D
cp $S/*.kicad_sch $S/route/preroute_v3.kicad_dru $S/fp-lib-table $S/sym-lib-table $D/
mv $D/preroute_v3.kicad_dru $D/round-pendant.kicad_dru; cp $S/route/preroute_v3.kicad_pro $D/round-pendant.kicad_pro
cp -r $S/lib $D/lib
cp "${2:-$S/route/preroute_v3.kicad_pcb}" $D/round-pendant.kicad_pcb
echo $D
