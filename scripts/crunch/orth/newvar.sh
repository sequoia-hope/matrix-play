#!/usr/bin/env bash
# newvar.sh FROM_VARIANT NEW_VARIANT: copy project files from a built variant (not the board). Refuses an existing variant.
set -euo pipefail; cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/hw/round-pendant"
[ -e "$2" ] && { echo "$2 exists" >&2; exit 2; }
mkdir -p $2/route; cp $1/*.kicad_sch $1/fp-lib-table $1/sym-lib-table $1/round-pendant.kicad_pro $1/round-pendant.kicad_dru $2/; cp -r $1/lib $2/lib; [ -e $1/map.csv ] && cp $1/map.csv $2/ || true
