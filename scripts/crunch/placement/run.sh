#!/usr/bin/env bash
# run.sh VARIANT [TIMEOUT]: one booked route with the README's flags, then the opens summary.
cd "$(dirname "$0")/../../.."; V=$1; T=${2:-600}
~/.claude/bin/reserve -c 4 --here -l "round-pendant crunch: placement $V ${T}s" -- python3 .claude/skills/pcb-design/scripts/autoroute.py hw/round-pendant/$V --planes ${PLANES:-In2.Cu,In5.Cu} --seeds 1 --timeout $T --threads 4 --memory 12G --extra "--prefanout-mode inner" > /tmp/claude-1000/-home-sequoia-pcb-round-pendant/b747bb30-353b-4635-8cb8-3b492fc301c0/scratchpad/$V.out 2>&1
rc=$?; echo "exit $rc"
[ $rc = 75 ] && { echo "NOT RUN (75)"; exit 75; }
python3 scripts/crunch/placement/opens_map.py hw/round-pendant/$V 2>&1 | grep -v Debug | cut -c1-400
grep -E "prefanout:|^negotiated|^rip-up|^routed|deadline|planes:" hw/round-pendant/$V/route/s0.log | cut -c1-160
