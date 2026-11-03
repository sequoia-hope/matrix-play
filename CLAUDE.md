# round-pendant

A PCB project in the Boardroom suite (Boardroom = `~/Software/easy_pcb`, Circuit Composer,
UltraRoute Studio), run with the `pcb-design` skill vendored in `.claude/skills/pcb-design/`
(never hand-edit that copy; `VENDORED_FROM` names the upstream commit). Load it for any board
work and follow its phases and gates. Start every session by reading the skill's `LESSONS.md`
and `design/status.json`, and resume from the last passed gate in `design/gates/`.

- KiCad projects live in `hw/<board>/<variant>/`.
- The project page is `index.html` (status from `design/status.json`, plus the embedded viewer),
  served on the registered port by `proj up round-pendant` or `./serve.sh`.
- The viewer is pcbview, pinned at `vendor/pcbview`; the router is ultraroute, pinned at
  `vendor/ultraroute`. Build with `scripts/view.sh build pcbview.toml`; route through the skill's
  `autoroute.py`. Never edit files under `vendor/` or `viewer/`.
- Update `design/status.json` (schema 1, Boardroom's `docs/shell-spec.md`) and rebuild the viewer
  at every gate.
- Heavy jobs (routing, full renders, ultraroute builds) go through `~/.claude/bin/reserve`.
- When the user corrects you: read `~/.config/boardroom/config.toml`; if its `skill_upstream`
  exists on this machine, add the rule to that copy's `LESSONS.md`; otherwise add it to this
  project's copy.
