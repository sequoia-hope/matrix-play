#!/usr/bin/env bash
# probe.sh: write design/study/crunch/map/via_probe.json, the anode via fit of every LED site at each of its four turns. Sites are the same in every map.
set -euo pipefail
R="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"; cd $R
export PENDANT_VARIANT=c-map-probe PENDANT_PLACE=place_c PENDANT_MAP=design/study/b/spiral/build/chip_lsa.csv
D=hw/round-pendant/$PENDANT_VARIANT; S=hw/round-pendant/c; B=scripts/crunch/map/board_map.py
python3 scripts/board_outline.py
python3 $B stack; python3 $B rules; python3 $B sync | tail -1
python3 $B place_c | tail -1
PROBE_OUT=$R/design/study/crunch/map/via_probe.json python3 $B anodes_b | tail -1
