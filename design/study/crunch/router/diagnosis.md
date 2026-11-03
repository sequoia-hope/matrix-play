# Router attack: what blocks the open connections

Tool: `scripts/crunch/router/diagnose.py`. It takes KiCad's DRC opens on a refilled copy, then models free space on the finished copper at 0.025 mm: a 0.1 mm track centre needs 0.14 mm to foreign copper and 0.25 mm to foreign holes; a 0.25/0.15 via centre needs 0.275 mm to foreign copper on every routing layer. Class limits are simplified (0.09 mm clearance for every class). It is a model of the final copper, not a proof of routability, and no prediction was tested by routing that connection by hand. `failview.py` was exported to `scripts/crunch/router/tools/` but not run, so there is no picture.

## Counts (signal opens, KiCad's list)

| Class | 8 layers, c-layers-v3-8a | 8 layers, c-placement-y5 |
|---|---:|---:|
| chip-fanout: chip pad end sealed, under 0.25 mm2 of reach | 12 | 8 |
| pad-wall: region bounded mostly by pads | 23 | 7 |
| via-wall: region bounded mostly by via keep-off | 9 | 3 |
| led-pad: LED pad end sealed | 2 | 2 |
| track-wall: bounded mostly by tracks | 6 | 1 |
| free-path: both ends in one free region | 4 | 1 |
| Total | 56 | 22 |

Older 6-layer result, trial 5 (variant b, SW at 0.2 mm, zones 0.5 mm): 122 signal: free-path 47, via-wall 25, pad-wall 25, track-wall 16, chip-fanout 9.

## Layers or local?

Evidence points to local blockage, not layer shortage, at 8 layers:

- Free track-centre fraction on inner signal layers after routing: 53-56% on 8a, 57-62% on y5. Against that, F.Cu is 28% and B.Cu 35-38%.
- Legal via sites after routing: 3.75% of the disc on 8a, 6.2% on y5; 2.9% on trial 5 (6 layers).
- On y5, the cheapest path allowed through other copper (0.1 mm grid; `blocked_mm`, `illegal_via_hops`, `nets_crossed` in `diag/y5.json`): 13 of 22 cross no foreign net at all, and 19 of 22 need one or more via where none is legal. Median for those classes is 1 illegal via. On the unfixed metric, 8a's `blocked_mm` undercounts because it ignored illegal via hops, so only y5's path figures should be used.

By class: chip-fanout, led-pad, pad-wall and via-wall are local: an end can't reach a legal via site, and more layers would not add sites because a through via blocks all of them. Each added layer also adds keep-offs for vias. track-wall is the only class that could be a layer shortage; it is 1 of 22 on y5 and 6 of 56 on 8a. What moved `open` most was grid cell (below), which also says the limit wasn't capacity.

No cut was counted, so this does not prove capacity is sufficient. c-placement-y17, fully connected, is the proof that it is.

## Zone clearance

The 0.5 mm zone clearance explains the plane class: 6 layers at 420 s, 75 plane open on v1 (0.5 mm), 5 on v2, 3 on v3.

## Narrow pad joint lines

`pad_joints.py` and the router disagree, and the router is nearer right. Trial 5: 442 log lines, pad_joints PASS. On the finished board 440 of the 442 ends are inside the pad's polygon, which is pad_joints' test of soundness, but they straddle a rectangular pad's corner, so copper passes through a chord narrower than the track. `necks.py` measures the chord. 

- Trial 5: 162 joints under 0.09 mm, 104 sole path to the pad, min 0.0.
- c-placement-y17: 597 log lines, pad_joints FAIL with 2, necks.py 462 under 0.09 of 1123 joints, 393 sole, 459 on LED pads. 202 of the 462 are 0.085-0.09 mm, 210 are 0.075-0.085, 50 are under 0.075.

Whether a corner neck is a fab defect is a judgement for the owner: DRC doesn't see it, and JLC's 0.09 mm limit is for tracks. 'Sole' uses touching copper as a second path, so it may undercount. necks.py was not checked against a second tool.

## Gemini's two claims

- 'About 262 CS vias land in channels and each corks F.Cu': the count is about right, 327 routed CS vias off-pad in the channel region on the v1 baseline. 'Each corks' isn't: 51 of 327 leave no track room on opposite sides by my test, 276 leave room. Pre-placing vias on cathode pads (327 in pad, 269 on stubs, 106 no site) gave 120 open, 1188 vias against 112 open, 933 vias at 420 s, 6 layers, one run: no gain.
- '50 track_width errors come from forced necks at narrow pads': partly. They are all on VBAT, VSYS, VBUS and BAT_N. But necks are not all of it: on c-layers-v3-8a KiCad finds 51 errors over 60.7 mm, while the router's `neck:` lines total 18 over 18.9 mm. The B.Cu zone fix was not tested by me.
