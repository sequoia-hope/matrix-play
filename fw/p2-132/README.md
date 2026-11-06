# `parallelogram/p2-132` Firmware & `picoem` Co-Simulation

Bare-metal dual-core Rust firmware and cycle-accurate board-level `picoem` (`rp2350-emu`) co-simulation for `hw/parallelogram/p2-132/parallelogram.kicad_pcb` (`25 × 70 mm`, `17.75°`-skewed parallelogram pendant, `132× XL-1615RGBC-RF`, `2× AW20198QNR`, `RP2350A`, `LIS2DW12TR`, `XYC-PT19C-L1`, `BQ24073`).

## Crates

- **`p2-132-fw/`** (`thumbv8m.main-none-eabihf`, zero external crates):
  - Valid RP2350 `PICOBIN` `IMAGE_DEF` (`0x1021`) at `0x1000_0040`.
  - Configures `12 MHz` `XOSC` + `150 MHz` `PLL_SYS` + Cortex-M33 VFPv5 FPU on both cores.
  - Enforces all EM-derived hardware settings from `design/sim/p2-132/`:
    - `PADS_QSPI` `SLEWFAST = 0` (`5.1×` lower crosstalk on the `109.2 Ω` `In2.Cu` QSPI bus).
    - `AW20198QNR` (`0x20` North, `0x25` South): `SRCR = 0x07` (`6/10 ns` slew -> `-30.4 dB` 300 MHz EMI & `3.39×` lower I²C glitch), `PCCR = 0x02` (Three-Phase PWM -> `5.4×` lower `VSYS` ripple), `SSCR = 0x15` (spread spectrum), `DGCR = 0x44` (hardware de-ghosting), and D65 white-balanced `SL = [255, 96, 220]`.
    - `8×` `ADC0` oversampling on `VBAT_SENSE` (eliminating the `147.7 mV` `VREG_LX` buck crossover spike) + linear `GCC(VBAT)` foldback below `3.65 V`.
  - Streams dual 198-byte PWM frames at `1.04 MHz` over `DMA Ch0 -> PIO0 SM0` (`GPIO4/5`) on Core 1 while Core 0 renders 4 interactive animations (`Aurora Shear Wave`, `Gravity Liquid Pool`, `Crystalline Rhombus`, `Battery SoC + Lux Bar Gauge`) and polls `LIS2DW12TR` (`0x19`) on `GPIO2/3`.
- **`p2-132-rom-shim/`** (`thumbv8m.main-none-eabihf`):
  - Pure-Thumb architectural RP2350 bootrom (`0x0000_0000`) implementing `PICOBIN` `0x1021` XIP validation on Core 0 and the 6-word `SIO_FIFO` + `WFE/SEV` multicore launch state machine on Core 1 (sidestepping silicon `bootrom-combined.bin`'s CP7 `rcp_*` canary traps in `rp2350-emu v0.2.6`).
- **`p2-132-sim/`** (`x86_64-unknown-linux-gnu`):
  - Links `/home/sequoia/Software/picoem/crates/rp2350-emu` and connects cycle-accurate open-drain models of `2× AW20198QNR` (`0x20`, `0x25`), `LIS2DW12TR` (`0x19`), `BQ24073` (`CHG`/`PGOOD`), `SW1`, and `VBAT`/`LIGHT` stimulus, exporting `design/sim/p2-132/results/picoem_run.json`.

## Verified `picoem` (`rp2350-emu v0.2.6`) Findings

1. **Silicon Bootrom CP7 `rcp_*` Canary Traps (Core 0 & Core 1):** Unmodified `bootrom-combined.bin` executes Redundancy Coprocessor (`CP7`) instructions both on Core 0 (`0x0000_39b6` -> UsageFault `NOCP`) and on Core 1 (`0x0000_01c6` immediately upon `WFE` wake during the 6-word FIFO handshake). Solved cleanly by `p2-132-rom-shim` (`356 B` pure-Thumb architectural RP2350 ROM).
2. **`TICKS` Peripheral Clock Domain (`peripherals/ticks.rs:27`):** Divides `clk_sys` (`150 MHz`) instead of `clk_ref` (`12 MHz`), advancing `TIMER0` `12.5×` faster than silicon when `TICKS.TIMER0.CYCLES = 12`. Hardware `PIO0 AUTOPUSH` + cycle-calibrated delays make `p2-132-fw` rate-independent.
3. **PIO `MOV ISR, NULL` Bit Counter (`picoem-common/src/pio/sm.rs:929`):** Clears `isr = 0` without resetting `isr_count = 0`; using `PUSH NOBLOCK` (`0x8000`) + `RXF0` drain resets both `isr` and `isr_count` identically on silicon and `picoem`.
4. **Armv8-M `LDA`/`STL` Decode Fallthrough (`core/execute_thumb32.rs:875`):** `thumb32_load_store_dual` lacks `LDA`/`STL` (`0xE8D0/0xE8C0 0x_FAF`) and falls through to `LDRD`/`STRD` with `Rt2 = 0xF` (`PC`), clobbering `PC` on `AtomicU32` `Acquire`/`Release`. Solved by `write_volatile`/`read_volatile` + `dmb sy` barriers.
5. **`WFE` Wake Cycle-Debt Catch-Up (`rp2350-emu/src/lib.rs` `step_pair_arm`):** While a core is parked in `WFE`, `cs[c].cycles` freezes while `clock.cycles` (`target`) advances; upon wake, `step_pair_arm` loops `while cs[c].cycles < target`, bursting ~`546,000` cycles inside a single `emu.step()` without yielding to host GPIO co-simulation. Using `core::hint::spin_loop()` (`YIELD`) for steady-state inter-core polling preserves cycle-granular host I²C wire stepping (`0` NACKs across all `7,008` AW20198 + LIS2DW12 bytes).
6. **Armv8-M `VSEL`/`VMAXNM`/`VMINNM` `D` & `cc` Bitfields (`core/execute_fpu.rs:630,639`):** In `fpu_v8m_dp` (`0xFE__` prefix), `d` is decoded from `hw0[4]` instead of `hw0[6]` and `VSEL` `cc` from `hw0[6:5]` instead of `hw0[5:4]` (DDI0553 §C2.4.407 / §C2.4.379), causing `VSELGT`/`VSELVS` on even `Sd` registers (`S2`, `S4`, ...) to write `S(2k+1)` instead. Using IEEE-754 integer-order `f32_clamp` + `to_int_unchecked::<i32>()` (`VCVT.S32.F32` `0xEEBD`) eliminates all `0xFE__` opcodes cleanly.
