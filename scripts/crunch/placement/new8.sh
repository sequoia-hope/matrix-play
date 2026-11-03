#!/usr/bin/env bash
# new8.sh NAME: fresh variant from the shared 8-layer start. Nothing else changed.
set -euo pipefail
cd "$(dirname "$0")/../../.."; V=$1; D=hw/round-pendant/$V; S=hw/round-pendant/c
[ -e "$D" ] && { echo "$D exists" >&2; exit 1; }
mkdir -p "$D"; cp $S/*.kicad_sch $S/fp-lib-table $S/sym-lib-table "$D/"; cp -r $S/lib "$D/lib"
for x in kicad_pcb kicad_pro kicad_dru; do cp $S/route/preroute_8L.$x $D/round-pendant.$x; done
