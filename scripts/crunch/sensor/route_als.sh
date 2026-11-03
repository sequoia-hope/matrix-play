#!/usr/bin/env bash
# route_als.sh IN_DIR OUT_DIR TIMEOUT "OPTIONS": one booked router pass with no strip; the board's other copper is kept unless OPTIONS adopt it.
set -uo pipefail
cd "$(dirname "$0")/../../.."
I=$1; O=$2; T=$3; X=$4; mkdir -p $O; cp $I/round-pendant.kicad_pro $I/round-pendant.kicad_dru $O/
BIN=$(scripts/route.sh --build)
~/.claude/bin/reserve -c 2 --here -l "round-pendant crunch: sensor $(basename $O)" -- systemd-run --user --scope --quiet -p MemoryMax=12G -p MemorySwapMax=0 -p CPUQuota=200% nice -n 15 timeout $((T+120)) "$BIN" route $I/round-pendant.kicad_pcb -o $O/round-pendant.kicad_pcb --planes In2.Cu,In5.Cu --seed 0 --threads 2 --timeout $T --report $O/report.json --blame $X > $O/route.log 2>&1
echo exit $? >> $O/route.log
