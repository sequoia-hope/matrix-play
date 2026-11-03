#!/usr/bin/env python3
"""cost_compare.py BOARD [--qty N] -- parts cost per board at LCSC prices for this board, and the counterfactual with addressable LEDs (same count, no IS31FL3741A). Reads each part's LCSC number from the board,
price breaks from LCSC's product API. Parts only: fab, assembly fees and the cell are quoted separately. Driver-only parts are found by net: anything on the matrix sheets."""
import collections, json, sys, urllib.request
import pcbnew
QTY = int(sys.argv[sys.argv.index("--qty")+1]) if "--qty" in sys.argv else 5
UA = {"User-Agent": "Mozilla/5.0"}
def info(c):
    r = urllib.request.urlopen(urllib.request.Request(f"https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={c}", headers=UA), timeout=30)
    d = json.load(r)["result"]
    return d["productModel"], [(p["ladder"], p["usdPrice"] if "usdPrice" in p else p.get("productPrice")) for p in d["productPriceList"]]
def price(lad, n):
    best = lad[0][1]
    for l, p in lad:
        if n >= l: best = p
    return float(best)
b = pcbnew.LoadBoard(sys.argv[1]); cnt = collections.Counter(); refs = collections.defaultdict(list); sheet = {}
for f in b.GetFootprints():
    fl = {x.GetName(): x.GetText() for x in f.GetFields()}
    c = fl.get("LCSC", ""); r = f.GetReference(); sheet[r] = f.GetSheetfile()
    if c:
        cnt[c] += 1; refs[c].append(r)
tot = drv = led = 0; cache = {}; rows = []
for c, n in cnt.most_common():
    try:
        m, lad = info(c); cache[c] = lad
    except Exception as e:
        print("NO PRICE", c, refs[c][:3], e); continue
    p = price(lad, n*QTY); cost = p*n; tot += cost
    rs = refs[c]; drvn = sum(1 for r in rs if "matrix" in sheet[r] and not r.startswith("D"))
    drv += p*drvn
    if rs[0].startswith("D"): led += cost
    rows.append((round(cost, 3), n, p, c, m[:26], ",".join(rs[:4])))
for r in sorted(rows, reverse=True)[:14]: print(r)
print(f"parts per board at qty {QTY}: ${tot:.2f}; LED ${led:.2f}; driver sheet parts (no LEDs) ${drv:.2f}")
print("unique parts", len(cnt))
alts = {"WS2816C-1313/4P (earring now)": "C42417612", "SK6805-EC10 (earring before)": "C22394946"}
N = sum(1 for f in b.GetFootprints() if f.GetReference().startswith("D"))
for name, c in alts.items():
    m, lad = info(c); p = price(lad, N*QTY)
    print(f"{name}: {N} x ${p:.4f} = ${N*p:.2f}; counterfactual parts ${tot-led-drv+N*p:.2f}", lad[:6])
