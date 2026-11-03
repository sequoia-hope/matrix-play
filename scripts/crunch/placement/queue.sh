#!/usr/bin/env bash
# queue.sh V1 V2 ...: run these one after another, one booking at a time, with the same flags.
cd "$(dirname "$0")"
for v in "$@"; do echo "=== $v"; ./run.sh "$v" 600; done
