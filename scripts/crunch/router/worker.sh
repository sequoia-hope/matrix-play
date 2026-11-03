#!/usr/bin/env bash
# worker.sh QUEUEFILE: pop trials (lines: NAME|TIMEOUT|EXTRA|THREADS|BIN|BOARD) until the file is empty. Two workers at most.
cd "$(dirname "$0")/../../.."
Q=$1
while :; do
  L=$(flock "$Q.lock" bash -c "head -1 '$Q'; sed -i 1d '$Q'")
  [ -z "$L" ] && break
  IFS='|' read -r N T X TH B BD <<<"$L"
  scripts/crunch/router/trial.sh "$N" "$T" "$X" "${TH:-2}" "$B" "$BD"
done
