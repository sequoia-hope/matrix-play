# BT1: Grepow 5435035 round LiPo

Not assembled by JLC. No maker's datasheet obtained; figures are from listings:
- Reseller listings: 610 mAh min, 3.85 V nominal, 1C, 35 × 35.1 × 5.45 mm, 10 g.
- Grepow's guide: GRP5435035, 4.4 V, 1C, 620 mAh, 5.4 × 35 × 35 mm.

Reading: 3.85 V nominal with a 4.4 V full charge is a high-voltage LiPo; not confirmed. 4.2 V charge is within limits either way, at reduced capacity. Standard resellers showed it out of stock on 2026-11-02.

- Discharge 1C = 610 mA. R19 300 mA is safe; hardware max 878 mA only under firmware fault. XB9901A is the short-circuit protection.
- Charge 300 mA = 0.5 C.
- Connection: leads to pads BT1+/BT1− on the bottom, near the edge **(decision: no connector)**, saves area, and XB9901A covers a reversed cell per its datasheet.
- Fit: 35 mm round behind a 38 mm board. Rests on 3.5 mm tallest part.

**Needs from the user:** Grepow's spec sheet, if a higher charge voltage is wanted.
