#!/usr/bin/env bash
# atrial.sh NAME SRC_DIR BOARD TIMEOUT "EXTRA" : one booked continuation pass; errors counted against $AR_BASE (the stripped board)
set -uo pipefail
cd "$(dirname "$0")/../../.."
N=$1; S=$2; BD=$3; T=$4; X=$5
D=$(scripts/crunch/router/mkfrom.sh "$N" "$S" "$BD") || exit 1
export AR_CONT=1
~/.claude/bin/reserve -c 2 --here -l "round-pendant crunch: router adopt $N" -- python3 scripts/crunch/router/autoroute_a.py $D --planes In2.Cu,In5.Cu --seeds 1 --timeout $T --threads 2 --memory 12G --extra "$X --report $D/route/report.json" > $D/route.out 2>&1
python3 - "$N" "$T" "$X" "$D" <<'PY' >> design/study/crunch/router/adopt.tsv
import json,sys
n,t,x,d=sys.argv[1:]
try:
    r=json.load(open(f"{d}/route/autoroute.json"))["runs"][0]
    print("\t".join(map(str,[n,t,r["open"],r["plane_open"],r["new_errors"],r["vias"],x])))
except Exception as e:
    print("\t".join(map(str,[n,t,"FAIL","","","",x])))
PY
