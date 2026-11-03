#!/usr/bin/env python3
"""autoroute_t.py: the skill's autoroute.py, with the router's output streamed to s0.log with a
timestamp per line (so `open` against time can be read off a run) instead of captured at the end.
Nothing else differs: same governing, same judge, same RECIPE. Run with $ULTRAROUTE for another binary."""
import os, re, subprocess, sys, threading, time
from pathlib import Path
SKILL = Path(__file__).resolve().parents[3] / ".claude/skills/pcb-design/scripts"
sys.path.insert(0, str(SKILL))
sys.argv[0] = str(SKILL / "autoroute.py")
import autoroute as ar

real_run = subprocess.run
class R:  # what autoroute reads back
    def __init__(s, rc, out): s.returncode, s.stdout, s.stderr = rc, out, ""
def run(cmd, **kw):
    if "route" not in cmd or "-o" not in cmd:
        return real_run(cmd, **kw)
    # --drop:FLAG removes FLAG (and nothing else) from the recipe, for continuation passes
    for d in [c for c in cmd if c.startswith("--drop:")]:
        cmd = [c for c in cmd if c != d and c != d[7:]]
    o = Path(cmd[cmd.index("-o") + 1]); tl = o.with_suffix(".tlog")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    t0 = time.time(); lines = []
    with tl.open("w") as f:
        for ln in p.stdout:
            lines.append(ln); f.write(f"{time.time()-t0:8.1f} {ln}"); f.flush()
    return R(p.wait(), "".join(lines))
ar.subprocess.run = run
# Continuation passes: errors count against the unrouted starting point, not the routed input.
base = Path(os.environ["AR_BASE"])
if os.environ.get("AR_CONT"):
    real_judge = ar.judge; first = [True]
    def judge(pcb, pro, plane_nets):
        if first[0]:
            first[0] = False
            return real_judge(base, pro, plane_nets)
        return real_judge(pcb, pro, plane_nets)
    ar.judge = judge
sys.exit(ar.main())
