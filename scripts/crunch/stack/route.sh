#!/usr/bin/env bash
# route.sh VARIANT PLANES_LAYERS TIMEOUT [extra router flags]: book 4 cores and route, score from autoroute.json
set -uo pipefail
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
V=$1; P=$2; T=$3; X="${4:---prefanout-mode inner}"; D=hw/round-pendant/$V
~/.claude/bin/reserve -c 4 --here -l "round-pendant crunch: stack $V ${T}s" -- python3 .claude/skills/pcb-design/scripts/autoroute.py $D --planes "$P" --seeds 1 --timeout $T --threads 4 --memory 12G --extra "$X" > $D/route/run.out 2>&1
rc=$?
python3 - "$D/route/autoroute.json" "$V" "$rc" >> design/study/crunch/stack/runs.tsv <<'P'
import json,sys
try:
    j=json.load(open(sys.argv[1])); r=j["runs"][j.get("best") or 0]
    print(sys.argv[2],sys.argv[3],r["open"],r["plane_open"],r["new_errors"],r["vias"],sep="\t")
except Exception as e: print(sys.argv[2],sys.argv[3],"FAIL",e,sep="\t")
P
tail -1 design/study/crunch/stack/runs.tsv
