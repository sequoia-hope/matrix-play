#!/usr/bin/env python3
"""coherent.py IN.csv OUT.csv: turn each LED so its footprint +x lies along its triplet's chain, so lands 1, 2, 4 run port, middle, starboard all the way down the ribbon.

The chain is the shortest path through a triplet's 9 sites. Turn k's +x axis points at world angle a-90k, so k is the one within 45 degrees of the heading (mean of in and out).
All LEDs have one chirality, so one sense of travel gives every LED the same left-to-right land order. Each chain's sense (two options) is the one with the better anode via fit.
Prints mean misalignment and via-fit counts. (The ribbon idea is in gemini/implementation_plan.md section 4.2; its land order there is mirrored, which this LED can't do.)
"""
import itertools, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import mapkit


def best_path(pts):
    n = len(pts); d = [[math.dist(a, b) for b in pts] for a in pts]
    dp = {(1 << i, i): (0.0, None) for i in range(n)}
    for mask in range(1, 1 << n):
        for last in range(n):
            if (mask, last) not in dp:
                continue
            c = dp[(mask, last)][0]
            for nx in range(n):
                if mask >> nx & 1:
                    continue
                k = (mask | 1 << nx, nx)
                if k not in dp or dp[k][0] > c+d[last][nx]:
                    dp[k] = (c+d[last][nx], last)
    full = (1 << n)-1
    last = min(range(n), key=lambda l: dp[(full, l)][0])
    path = []; mask = full; L = dp[(full, last)][0]
    while last is not None:
        path.append(last); prev = dp[(mask, last)][1]; mask ^= 1 << last; last = prev
    return path[::-1], L


def wrap(x):
    return (x+180) % 360-180


def main():
    rows = mapkit.load(sys.argv[1]); probe = json.loads(mapkit.PROBE.read_text())
    tot = 0; mis = []; legs = []; costs = 0
    for drv in (1, 2):
        for t in range(1, 14):
            ch = [r for r in rows if r["driver"] == drv and r["triplet"] == t]
            pts = [(r["x"], r["y"]) for r in ch]
            path, L = best_path(pts); tot += L
            legs += [math.dist(pts[path[i]], pts[path[i+1]]) for i in range(8)]
            best = None
            for rev in (False, True):
                p = path[::-1] if rev else path; c = 0; pick = []
                for i, idx in enumerate(p):
                    a0 = pts[p[max(i-1, 0)]]; a1 = pts[p[min(i+1, 8)]]
                    th = math.degrees(math.atan2(a1[1]-a0[1], a1[0]-a0[0]))
                    r = ch[idx]
                    k = min(range(4), key=lambda q: abs(wrap(r["a"]-90*q-th)))
                    c += mapkit.via_cost(r, k, probe); pick.append((r, k, abs(wrap(r["a"]-90*k-th))))
                if best is None or c < best[0]:
                    best = (c, pick)
            costs += best[0]
            for r, k, m in best[1]:
                r["turn"] = k; mis.append(m)
    ns, pin = mapkit.nets(rows)
    print(json.dumps({"path_mm": round(tot), "leg_mean": round(sum(legs)/len(legs), 2), "legs_over_2.6": sum(l > 2.6 for l in legs), "mean_misalign_deg": round(sum(mis)/len(mis), 1), "via_cost": round(costs),
                      "cs_tree": round(sum(mapkit.net_len(m, pin[k]) for k, m in ns.items() if k[0] == "cs"))}))
    mapkit.save(rows, sys.argv[2])


if __name__ == "__main__":
    main()
