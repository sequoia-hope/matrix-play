#!/usr/bin/env bash
# trial.sh NAME TIMEOUT "EXTRA" [THREADS] [BIN] [BOARD]: one booked trial; appends to runs8.tsv
set -uo pipefail
cd "$(dirname "$0")/../../.."
N=$1; T=$2; X=$3; TH=${4:-4}; BIN=${5:-}; BOARD=${6:-}
V=c-router-8-$N; D=hw/round-pendant/$V
scripts/crunch/router/mkvar8.sh "$N" $BOARD >/dev/null || exit 1
[ -n "$BOARD" ] && export AR_CONT=1
[ -n "$BIN" ] && export ULTRAROUTE=$PWD/$BIN
~/.claude/bin/reserve -c $TH --here -l "round-pendant crunch: router 8L $N" -- python3 scripts/crunch/router/autoroute_t8.py $D --planes In2.Cu,In5.Cu --seeds 1 --timeout $T --threads $TH --memory 12G --extra "$X --report $D/route/report.json" > $D/route.out 2>&1
rc=$?
python3 - "$N" "$T" "$X" "$TH" "${BIN:-pin}" "$rc" <<'PY' >> design/study/crunch/router/runs8.tsv
import json,sys,re
n,t,x,th,b,rc=sys.argv[1:]
try:
    r=json.load(open(f"hw/round-pendant/c-router-8-{n}/route/autoroute.json"))["runs"][0]
    print("\t".join(map(str,[n,t,th,b.split('/')[2] if '/' in b else b,r["open"],r["plane_open"],r["new_errors"],r["vias"],x])))
except Exception as e:
    print("\t".join(map(str,[n,t,th,b,"FAIL rc="+rc,"","","",x])))
PY
exit 0
