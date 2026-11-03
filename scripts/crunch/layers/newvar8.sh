#!/usr/bin/env bash
# newvar8.sh NAME [--necks] : make hw/round-pendant/c-layers-NAME from the shared 8-layer start board; --necks appends the router's own courtyard neck rules (scripts/crunch/layers/necks.dru), a labelled relaxation.
set -euo pipefail
cd "$(dirname "$0")/../../.."
V=c-layers-$1; D=hw/round-pendant/$V
[[ -e $D ]] && { echo "$D exists; never overwrite a trial" >&2; exit 1; }
mkdir -p $D
S=hw/round-pendant/c
cp $S/*.kicad_sch $S/fp-lib-table $S/sym-lib-table $D/
cp -r $S/lib $D/lib
for x in kicad_pcb kicad_pro kicad_dru; do cp $S/route/preroute_8L.$x $D/round-pendant.$x; done
if [[ "${2:-}" == --necks ]]; then { echo; echo "# Necks the router reported: no wider leg reaches the pin. A relaxation, inside each part's courtyard only; see design/study/crunch/layers/report.md."; cat scripts/crunch/layers/necks.dru; } >> $D/round-pendant.kicad_dru; fi
echo $D
