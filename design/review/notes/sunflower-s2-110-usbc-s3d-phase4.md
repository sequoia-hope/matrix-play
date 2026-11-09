**Gate 4 — mechanical and layout brief.** The agent's fresh-context reviewer passed it (0 blocker, 0 major). Three decisions are yours; all three were also open on S3C and are kept as-is until you answer.

![Floorplan (back side)](../../renders/sunflower-s2-110-usbc-s3d/floorplan.png)

**What changed from S3C** — check it is what you asked for:

- USB-C `J1` is now the full-SMT `TYPE-C-31-M-22`: no through-hole slots. Mouth corners stick out 0.8 mm past the 38 mm rim. It is held only by its solder pads, so support it when plugging in on the bench and capture the shell in the bezel.
- Cell protection `U8` (+ `C6`, `R8`) moved into the north-west pocket next to battery socket `BT1`.
- Flash decoupling cap `C22` is now 1.40 mm from its power pin (was 8.56 mm).
- USB ESD chip `U7` sits inline just north of `J1`, no crossing traces.
- The second inner layer (`In2.Cu`) is now a solid ground plane right under the back-side chips.
- LED positions are identical to S3C, so firmware LED tables don't change.

### Decision 1 — battery stack and buttons

- `BT1` faces inward, so the battery plug goes in before the cell is fitted. There is **no reverse-polarity protection**: check the plug wiring first.
- A 35 mm cell sits over `J1` and `BT1` (about 3.3 mm tall). Choose:
  **(a)** 35 mm cell on a ≥ 3.5 mm pocketed spacer (about 10 mm total stack), or
  **(b)** a ≤ 30 mm cell on 2.4 mm foam inside the central pocket.
- Side buttons `SW1`/`SW2` stick out 0.40 mm nominal; worst-case tolerance leaves them flush to 0.2 mm recessed. Is fingernail press OK?

### Decision 2 — charge current

- Keep `R4` = 3.0 kΩ: about 297 mA, the charger dissipates 0.56 W, charge only at ≤ 25 °C ambient.
- Or `R4` = 4.7 kΩ: about 189 mA, 0.36 W, runs cooler.

### Decision 3 — back silkscreen

- Keep the back free of board name / revision / URL (board identifies itself by the `BOARD_ID = 4` strap only)?
- If you want the URL, it is now `github.com/sequoia-hope/matrix-play`.

**Heads-up:** the agent has already routed past Gate 4. Changing the spacer (if it moves `J1`/`BT1`) or adding back-silk text means rework; swapping `R4` is only a value change.
