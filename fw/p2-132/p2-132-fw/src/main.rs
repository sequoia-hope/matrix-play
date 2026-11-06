#![no_std]
#![no_main]

//! Bare-metal dual-core RP2350A firmware for `parallelogram/p2-132` (132 RGB LEDs, 2x AW20198QNR, LIS2DW12TR).
//!
//! Hardware & EM-Derived Configuration:
//! - Boots directly from RP2350 silicon bootrom via valid PICOBIN IMAGE_DEF at 0x1000_0040.
//! - Enables Cortex-M33 VFPv5 FPU, 12 MHz XOSC, and 150 MHz PLL_SYS + 1 us TIMER0 tick.
//! - Configures PADS_QSPI SLEWFAST=0 (Phase P1 EM finding: cuts In2.Cu QSPI crosstalk 5.1x).
//! - Drives U1 (0x20, North 6x11 D1..D66) and U2 (0x25, South 6x11 D67..D132) over 1.04 MHz Fm+
//!   open-drain I2C on GPIO4/GPIO5 using RP2350 PIO0 SM0 + DMA Channel 0 (DREQ_PIO0_TX0 = 0).
//! - Programs AW20198QNR EM-derived registers:
//!     * SRCR (0x2B) = 0x07 (6 ns rise / 10 ns fall -> 3.4x lower I2C glitch & -30.4 dB @ 300 MHz EMI)
//!     * PCCR (0x29) = 0x02 (Three-Phase PWM stagger -> 5.4x lower VSYS AC ripple at North U1)
//!     * SSCR (0x28) = 0x15 (Spread-spectrum clock modulation enabled)
//!     * DGCR (0x02) = 0x44 (Off-time 4 kOhm CS pull-up / 2 kOhm SW bleed de-ghosting)
//!     * SL0..197    = D65 white-balanced per-die current scaling (R=255, G=96, B=220)
//! - Polls LIS2DW12TR (0x19) on GPIO2/GPIO3 (400 kHz open-drain SIO I2C), SW1 button (GPIO11),
//!   BQ24073 status (GPIO12 CHG, GPIO13 PGOOD), and 8x-oversampled ADC0/ADC1 (VBAT_SENSE / LIGHT,
//!   averaging out the 148 mV VREG_LX buck crossover spikes discovered in Phase P2!).
//! - Applies our Phase P4 PDN-derived GCC(VBAT) foldback curve below 3.65 V to prevent North Blue/Green dropout.
//! - Dual-core pipelined architecture:
//!     * Core 0 computes 4 skewed-parallelogram floating-point animations (Aurora Shear Wave,
//!       Gravity Liquid Pool, Crystalline Rhombus Pulse, Battery/Lux Gauge) into ping-pong PWM pages
//!       and encodes 32-bit PIO open-drain DMA waveforms.
//!     * Core 1 receives frame buffer pointers over the RP2350 inter-core SIO FIFO and streams
//!       both 198-byte PWM pages + live GCCR updates over DMA Ch0 -> PIO0 SM0 concurrently!

use core::arch::asm;
use core::panic::PanicInfo;
use core::ptr::{read_volatile, write_volatile};

// ============================================================================
// Boot Headers: Cortex-M33 Vector Table + RP2350 PICOBIN + Core 1 Vector Table
// ============================================================================

#[repr(C)]
pub union VectorEntry {
    pub sp: u32,
    pub handler: unsafe extern "C" fn() -> !,
}

unsafe extern "C" {
    static mut _sidata: u32;
    static mut _sdata: u32;
    static mut _edata: u32;
    static mut _sbss: u32;
    static mut _ebss: u32;
}

#[unsafe(link_section = ".vector_table")]
#[used]
pub static VECTOR_TABLE: [VectorEntry; 16] = [
    VectorEntry { sp: 0x2008_2000 }, // Top of 520 KB SRAM
    VectorEntry { handler: _reset },
    VectorEntry { handler: _fault_handler }, // NMI
    VectorEntry { handler: _fault_handler }, // HardFault
    VectorEntry { handler: _fault_handler }, // MemManage
    VectorEntry { handler: _fault_handler }, // BusFault
    VectorEntry { handler: _fault_handler }, // UsageFault
    VectorEntry { handler: _fault_handler }, // SecureFault
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { handler: _fault_handler }, // SVCall
    VectorEntry { handler: _fault_handler }, // DebugMon
    VectorEntry { sp: 0 },
    VectorEntry { handler: _fault_handler }, // PendSV
    VectorEntry { handler: _fault_handler }, // SysTick
];

/// RP2350 Minimum Viable PICOBIN IMAGE_DEF block (Datasheet §5.9.5):
/// EXE | EXE_SECURITY_S (2<<4) | EXE_CPU_ARM (0<<8) | EXE_CHIP_RP2350 (1<<12) = 0x1021.
#[unsafe(link_section = ".picobin")]
#[used]
pub static PICOBIN_BLOCK: [u32; 5] = [
    0xFFFF_DED3, // PICOBIN_BLOCK_MARKER_START
    0x1021_0142, // ITEM_1BS_IMAGE_TYPE (0x42), size=1 word, image_type=0x1021
    0x0000_01FF, // ITEM_2BS_LAST (0xFF), total inner size = 1 word
    0x0000_0000, // Relative link = 0 (single-block self-loop)
    0xAB12_3579, // PICOBIN_BLOCK_MARKER_END
];

#[unsafe(link_section = ".core1_vectors")]
#[used]
pub static CORE1_VECTORS: [VectorEntry; 16] = [
    VectorEntry { sp: 0x2008_0000 },
    VectorEntry { handler: core1_entry },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
    VectorEntry { sp: 0 },
    VectorEntry { handler: _fault_handler },
    VectorEntry { handler: _fault_handler },
];

// ============================================================================
// RP2350 Memory-Mapped Register Constants
// ============================================================================

const CLOCKS_BASE: u32     = 0x4001_0000;
const RESETS_BASE: u32     = 0x4002_0000;
const IO_BANK0_BASE: u32   = 0x4002_8000;
const PADS_BANK0_BASE: u32 = 0x4003_8000;
const PADS_QSPI_BASE: u32  = 0x4004_0000;
const XOSC_BASE: u32       = 0x4004_8000;
const PLL_SYS_BASE: u32    = 0x4005_0000;
const ADC_BASE: u32        = 0x400A_0000;
const TIMER0_BASE: u32     = 0x400B_0000;
const TICKS_BASE: u32      = 0x4010_8000;
const DMA_BASE: u32        = 0x5000_0000;
const PIO0_BASE: u32       = 0x5020_0000;
const SIO_BASE: u32        = 0xD000_0000;
const SCB_CPACR: u32       = 0xE000_ED88;

const ALIAS_CLR: u32 = 0x3000;

// RESETS bits (RP2350 Datasheet §7.5 Table 486)
const RESET_ADC: u32        = 1 << 0;
const RESET_DMA: u32        = 1 << 2;
const RESET_IO_BANK0: u32   = 1 << 6;
const RESET_PADS_BANK0: u32 = 1 << 9;
const RESET_PIO0: u32       = 1 << 11;
const RESET_PLL_SYS: u32    = 1 << 14;
const RESET_TIMER0: u32     = 1 << 23;

// p2-132 GPIO Pinout
const PIN_LIGHT_PWR: u32 = 1;
const PIN_ACC_SDA: u32   = 2;
const PIN_ACC_SCL: u32   = 3;
const PIN_I2C_SDA: u32   = 4;
const PIN_I2C_SCL: u32   = 5;
const PIN_LED_SDB: u32   = 6;
const PIN_ACC_INT: u32   = 10;
const PIN_BTN: u32       = 11;
const PIN_CHG: u32       = 12;
const PIN_PGOOD: u32     = 13;
const PIN_VBAT_EN: u32   = 14;
const PIN_VBAT_ADC: u32  = 26;
const PIN_LIGHT_ADC: u32 = 27;

// I2C 7-bit Addresses on p2-132
const ADDR_AW1_NORTH: u8 = 0x20;
const ADDR_AW2_SOUTH: u8 = 0x25;
const ADDR_LIS2DW12: u8  = 0x19;

// Structured Non-Intrusive Telemetry & Optional Sim Analog Stimulus Mailbox at 0x2007_F000
const MAILBOX_ADDR: u32 = 0x2007_F000;
const SIM_STIM_MAGIC: u32 = 0x5349_4D31; // "SIM1" written optionally by p2-132-sim
const FW_TELEM_MAGIC: u32 = 0x5032_3133; // "P213" written by firmware

#[repr(C)]
pub struct TelemetryMailbox {
    pub fw_magic: u32,            // +0x00: 0x5032_3133 ("P213")
    pub boot_stage: u32,          // +0x04: 1=clocks, 2=gpio, 3=sensors, 4=aw20198, 5=core1, 6=running, 0xDEAD=fault
    pub aw1_chip_id: u32,         // +0x08: Read back from 0x20 reg 0x2F (expect 0x71)
    pub aw2_chip_id: u32,         // +0x0C: Read back from 0x25 reg 0x2F (expect 0x71)
    pub lis_whoami: u32,          // +0x10: Read back from 0x19 reg 0x0F (expect 0x44)
    pub i2c_ack_errors: u32,      // +0x14: Cumulative NACK count across both buses (expect 0)
    pub core0_frames: u32,        // +0x18: Frames rendered by Core 0 VFPv5 shader pipeline
    pub core1_frames_dma: u32,    // +0x1C: Dual-driver frame pairs streamed by Core 1 via DMA->PIO0
    pub active_mode: u32,         // +0x20: 0=Aurora Shear, 1=Gravity Pool, 2=Rhombus Pulse, 3=Battery/Lux Gauge
    pub active_gcc: u32,          // +0x24: Live AW20198 GCCR value after VBAT foldback & lux scaling
    pub vbat_mv: u32,             // +0x28: Measured battery voltage in mV
    pub light_raw: u32,           // +0x2C: Measured 12-bit ambient light ADC count
    pub accel_mg_x: i32,          // +0x30: LIS2DW12 X acceleration (mg)
    pub accel_mg_y: i32,          // +0x34: LIS2DW12 Y acceleration (mg)
    pub accel_mg_z: i32,          // +0x38: LIS2DW12 Z acceleration (mg)
    pub max_frames_limit: u32,    // +0x3C: Optional frame stop target set by sim (0 = run forever on silicon!)
    pub sim_stim_magic: u32,      // +0x40: Optional 0x5349_4D31 ("SIM1")
    pub sim_vbat_adc_12b: u32,    // +0x44: Injected 12-bit ADC0 reading when sim_stim_magic == SIM1
    pub sim_light_adc_12b: u32,   // +0x48: Injected 12-bit ADC1 reading when sim_stim_magic == SIM1
    pub status_flags: u32,        // +0x4C: bit0=charging(!CHG), bit1=usb_pgood(!PGOOD), bit2=btn_pressed(!BTN)
}

#[inline(always)]
fn mmio_write(addr: u32, val: u32) {
    unsafe { write_volatile(addr as *mut u32, val) };
}

#[inline(always)]
fn mmio_read(addr: u32) -> u32 {
    unsafe { read_volatile(addr as *const u32) }
}

#[inline(always)]
fn mbox() -> *mut TelemetryMailbox {
    MAILBOX_ADDR as *mut TelemetryMailbox
}

// ============================================================================
// Timing & Hardware Initialization
// ============================================================================

#[inline(always)]
fn timer_us() -> u32 {
    mmio_read(TIMER0_BASE + 0x0C) // TIMERAWL (free-running 1 us counter)
}

fn delay_us(us: u32) {
    let start = timer_us();
    while timer_us().wrapping_sub(start) < us {
        core::hint::spin_loop();
    }
}

fn init_clocks_150mhz() {
    // 1. Enable 12 MHz crystal oscillator (XOSC)
    mmio_write(XOSC_BASE + 0x0C, 47);          // STARTUP delay
    mmio_write(XOSC_BASE + 0x00, 0x00FA_BAA0); // ENABLE + 1_15MHZ
    while (mmio_read(XOSC_BASE + 0x04) & (1 << 31)) == 0 {}

    // 2. Switch CLK_REF to XOSC (SRC = 2) and ensure CLK_SYS is on CLK_REF (SRC = 0) before touching PLL_SYS
    mmio_write(CLOCKS_BASE + 0x3C, 0);
    mmio_write(CLOCKS_BASE + 0x30, 2);

    // 3. Configure PLL_SYS: 12 MHz / 1 * 125 = 1500 MHz VCO, POSTDIV 5 * 2 = 10 -> 150 MHz
    mmio_write(RESETS_BASE + ALIAS_CLR, RESET_PLL_SYS);
    while (mmio_read(RESETS_BASE + 0x08) & RESET_PLL_SYS) == 0 {}

    mmio_write(PLL_SYS_BASE + 0x00, 1);   // REFDIV = 1
    mmio_write(PLL_SYS_BASE + 0x08, 125); // FBDIV_INT = 125
    mmio_write(PLL_SYS_BASE + 0x04 + ALIAS_CLR, (1 << 0) | (1 << 5)); // Clear PD & VCOPD
    while (mmio_read(PLL_SYS_BASE + 0x00) & (1 << 31)) == 0 {}        // Wait PLL LOCK

    mmio_write(PLL_SYS_BASE + 0x0C, (5 << 16) | (2 << 12)); // PRIM: POSTDIV1=5, POSTDIV2=2
    mmio_write(PLL_SYS_BASE + 0x04 + ALIAS_CLR, 1 << 3);    // Clear POSTDIVPD

    // 4. Switch CLK_SYS to PLL_SYS (SRC = 1, AUXSRC = 0), enable CLK_PERI & CLK_ADC
    mmio_write(CLOCKS_BASE + 0x44, 1 << 16);  // CLK_SYS_DIV = 1.0
    mmio_write(CLOCKS_BASE + 0x3C, 1);        // CLK_SYS_CTRL = AUX (PLL_SYS)
    mmio_write(CLOCKS_BASE + 0x48, 1 << 11);  // CLK_PERI_CTRL ENABLE
    mmio_write(CLOCKS_BASE + 0x60, 1 << 11);  // CLK_ADC_CTRL ENABLE

    // 5. Start 1 MHz tick generator for TIMER0 (12 cycles of 12 MHz XOSC = 1 us)
    mmio_write(TICKS_BASE + 0x1C, 12);
    mmio_write(TICKS_BASE + 0x18, 1);
}

fn init_peripherals_and_pins() {
    let mask = RESET_ADC | RESET_DMA | RESET_IO_BANK0 | RESET_PADS_BANK0 | RESET_PIO0 | RESET_TIMER0;
    mmio_write(RESETS_BASE + ALIAS_CLR, mask);
    while (mmio_read(RESETS_BASE + 0x08) & mask) != mask {}

    // Enforce Phase P1 EM constraint: keep PADS_QSPI SLEWFAST=0 (bit 0 = 0), 4 mA drive (DRIVE=1)
    for off in [0x04u32, 0x08, 0x0C, 0x10, 0x14, 0x18] {
        let cur = mmio_read(PADS_QSPI_BASE + off);
        mmio_write(PADS_QSPI_BASE + off, (cur & !0x31) | (1 << 4));
    }

    // Configure digital pads (clear RP2350 ISO bit 8, enable IE bit 6, 4 mA drive, slow slew)
    for &pin in &[
        PIN_LIGHT_PWR, PIN_ACC_SDA, PIN_ACC_SCL, PIN_I2C_SDA, PIN_I2C_SCL,
        PIN_LED_SDB, PIN_ACC_INT, PIN_BTN, PIN_CHG, PIN_PGOOD, PIN_VBAT_EN,
    ] {
        let mut pad = (1 << 6) | (1 << 4); // IE=1, DRIVE=4mA, ISO=0, SLEWFAST=0
        if pin == PIN_BTN || pin == PIN_CHG || pin == PIN_PGOOD || pin == PIN_ACC_INT {
            pad |= 1 << 3; // PUE=1 internal pull-up on active-low status/button inputs
        }
        mmio_write(PADS_BANK0_BASE + 0x04 + 4 * pin, pad);
    }
    // Analog ADC inputs GPIO26 (VBAT_SENSE) & GPIO27 (LIGHT): OD=1 (bit 7), IE=0, ISO=0
    for &apin in &[PIN_VBAT_ADC, PIN_LIGHT_ADC] {
        mmio_write(PADS_BANK0_BASE + 0x04 + 4 * apin, 1 << 7);
    }

    // Clear SIO outputs first; drive LIGHT_PWR=0, LED_SDB=0, VBAT_EN=0; open-drain ACC_SDA/SCL out=0, oe=0
    mmio_write(
        SIO_BASE + 0x18 + 0x08, // GPIO_OUT_CLR (0xD000_0020)
        (1 << PIN_LIGHT_PWR) | (1 << PIN_ACC_SDA) | (1 << PIN_ACC_SCL)
            | (1 << PIN_LED_SDB) | (1 << PIN_VBAT_EN),
    );
    mmio_write(
        SIO_BASE + 0x38, // GPIO_OE_SET: push-pull outputs for power gates & LED_SDB
        (1 << PIN_LIGHT_PWR) | (1 << PIN_LED_SDB) | (1 << PIN_VBAT_EN),
    );
    mmio_write(
        SIO_BASE + 0x40, // GPIO_OE_CLR: release open-drain ACC_SDA/ACC_SCL & inputs
        (1 << PIN_ACC_SDA) | (1 << PIN_ACC_SCL) | (1 << PIN_BTN) | (1 << PIN_CHG) | (1 << PIN_PGOOD),
    );

    // IO_BANK0 FUNCSEL = 5 (SIO) for control/sensor pins; FUNCSEL = 6 (PIO0) for GPIO4/5 (1 MHz I2C_SDA/SCL)
    for &pin in &[
        PIN_LIGHT_PWR, PIN_ACC_SDA, PIN_ACC_SCL, PIN_LED_SDB,
        PIN_ACC_INT, PIN_BTN, PIN_CHG, PIN_PGOOD, PIN_VBAT_EN,
    ] {
        mmio_write(IO_BANK0_BASE + 0x04 + 8 * pin, 5);
    }
    mmio_write(IO_BANK0_BASE + 0x04 + 8 * PIN_I2C_SDA, 6); // PIO0
    mmio_write(IO_BANK0_BASE + 0x04 + 8 * PIN_I2C_SCL, 6); // PIO0

    // Enable ADC block
    mmio_write(ADC_BASE + 0x00, 1); // CS.EN = 1
}

// ============================================================================
// Bus 1: 400 kHz Open-Drain SIO I2C Master on GPIO2/GPIO3 (LIS2DW12TR @ 0x19)
// ============================================================================

#[inline(always)]
fn acc_sda_drive_low(low: bool) {
    if low {
        mmio_write(SIO_BASE + 0x38, 1 << PIN_ACC_SDA); // OE_SET -> drives 0
    } else {
        mmio_write(SIO_BASE + 0x40, 1 << PIN_ACC_SDA); // OE_CLR -> 4.7k pull-up to 3.3V
    }
}

#[inline(always)]
fn acc_scl_drive_low(low: bool) {
    if low {
        mmio_write(SIO_BASE + 0x38, 1 << PIN_ACC_SCL);
    } else {
        mmio_write(SIO_BASE + 0x40, 1 << PIN_ACC_SCL);
    }
}

#[inline(always)]
fn acc_sda_read() -> bool {
    ((mmio_read(SIO_BASE + 0x04) >> PIN_ACC_SDA) & 1) != 0
}

#[inline(always)]
fn acc_quarter_delay() {
    // ~0.6 us at 150 MHz (~400 kHz I2C)
    for _ in 0..22 {
        unsafe { asm!("nop") };
    }
}

fn acc_i2c_start() {
    acc_sda_drive_low(false);
    acc_quarter_delay();
    acc_scl_drive_low(false);
    acc_quarter_delay();
    acc_sda_drive_low(true);
    acc_quarter_delay();
    acc_scl_drive_low(true);
    acc_quarter_delay();
}

fn acc_i2c_stop() {
    acc_sda_drive_low(true);
    acc_quarter_delay();
    acc_scl_drive_low(false);
    acc_quarter_delay();
    acc_sda_drive_low(false);
    acc_quarter_delay();
}

fn acc_i2c_write_byte(b: u8) -> bool {
    for i in (0..8).rev() {
        let bit_one = ((b >> i) & 1) != 0;
        acc_sda_drive_low(!bit_one);
        acc_quarter_delay();
        acc_scl_drive_low(false);
        acc_quarter_delay();
        acc_quarter_delay();
        acc_scl_drive_low(true);
        acc_quarter_delay();
    }
    acc_sda_drive_low(false); // Release SDA for slave ACK
    acc_quarter_delay();
    acc_scl_drive_low(false);
    acc_quarter_delay();
    let ack = !acc_sda_read();
    acc_quarter_delay();
    acc_scl_drive_low(true);
    acc_quarter_delay(); // Ensure full t_LOW so slave sees 9th falling edge & releases ACK!
    if !ack {
        unsafe { (*mbox()).i2c_ack_errors = (*mbox()).i2c_ack_errors.wrapping_add(1) };
    }
    ack
}

fn acc_i2c_read_byte(send_ack: bool) -> u8 {
    let mut val = 0u8;
    acc_sda_drive_low(false);
    for _ in 0..8 {
        acc_quarter_delay();
        acc_scl_drive_low(false);
        acc_quarter_delay();
        val = (val << 1) | (acc_sda_read() as u8);
        acc_quarter_delay();
        acc_scl_drive_low(true);
        acc_quarter_delay();
    }
    acc_sda_drive_low(send_ack); // Master drives LOW to ACK, releases HIGH to NACK
    acc_quarter_delay();
    acc_scl_drive_low(false);
    acc_quarter_delay();
    acc_quarter_delay();
    acc_scl_drive_low(true);
    acc_quarter_delay();
    acc_sda_drive_low(false);
    acc_quarter_delay();
    val
}

fn lis2dw12_write_reg(reg: u8, val: u8) -> bool {
    acc_i2c_start();
    let ok = acc_i2c_write_byte(ADDR_LIS2DW12 << 1)
        && acc_i2c_write_byte(reg)
        && acc_i2c_write_byte(val);
    acc_i2c_stop();
    ok
}

fn lis2dw12_read_regs(start_reg: u8, out: &mut [u8]) -> bool {
    acc_i2c_start();
    if !acc_i2c_write_byte(ADDR_LIS2DW12 << 1) || !acc_i2c_write_byte(start_reg) {
        acc_i2c_stop();
        return false;
    }
    acc_i2c_start();
    if !acc_i2c_write_byte((ADDR_LIS2DW12 << 1) | 1) {
        acc_i2c_stop();
        return false;
    }
    let last = out.len().saturating_sub(1);
    for (i, slot) in out.iter_mut().enumerate() {
        *slot = acc_i2c_read_byte(i != last);
    }
    acc_i2c_stop();
    true
}

// ============================================================================
// Bus 0: 1.04 MHz Fm+ PIO0 SM0 + DMA Channel 0 Open-Drain I2C Engine (GPIO4/5)
// ============================================================================
//
// PIO0 SM0 runs a 2-instruction open-drain phase engine:
//   0: OUT PINDIRS, 2 [1]   (0x6182: 2 PIO cycles; bit0=SDA_oe, bit1=SCL_oe; pad_out fixed at 0!)
//   1: IN  PINS,    2 [1]   (0x4102: 2 PIO cycles; samples live GPIO4/5 into ISR!)
// At CLKDIV = 9.0 (150 MHz / 9 = 16.67 MHz PIO clk), each 2-bit phase takes 4 PIO cycles = 36 CPU
// cycles (240 ns), so 4 phases = 1 full I2C bit = 960 ns = 1.0417 MHz I2C Fast-mode Plus!

fn init_pio0_i2c_master() {
    mmio_write(PIO0_BASE + 0x000, 0); // Disable all SMs while configuring
    // Clear FIFOs & restart SM0 (CTRL bits [7:4] SM_RESTART, [11:8] CLKDIV_RESTART)
    mmio_write(PIO0_BASE + 0x000, (1 << 4) | (1 << 8));

    // Program 2-instruction open-drain phase/capture loop into INSTR_MEM[0..1]
    mmio_write(PIO0_BASE + 0x048 + 0, 0x6182); // OUT PINDIRS, 2 [1]
    mmio_write(PIO0_BASE + 0x048 + 4, 0x4102); // IN  PINS,    2 [1]

    // SM0_CLKDIV (0x0C8): INT = 9, FRAC = 0
    mmio_write(PIO0_BASE + 0x0C8, 9 << 16);
    // SM0_EXECCTRL (0x0CC): WRAP_BOTTOM = 0 << 7, WRAP_TOP = 1 << 12
    mmio_write(PIO0_BASE + 0x0CC, (0 << 7) | (1 << 12));
    // SM0_SHIFTCTRL (0x0D0): OUT_SHIFTDIR=1 (right, bit 19), IN_SHIFTDIR=0 (left), AUTOPULL=1 (bit 17), PULL_THRESH=0 (32)
    mmio_write(PIO0_BASE + 0x0D0, (1 << 19) | (1 << 17));
    // SM0_PINCTRL (0x0DC): OUT_BASE=4, SET_BASE=4<<5, IN_BASE=4<<15, OUT_COUNT=2<<20, SET_COUNT=2<<26
    mmio_write(
        PIO0_BASE + 0x0DC,
        4 | (4 << 5) | (4 << 15) | (2 << 20) | (2 << 26),
    );

    // Force-execute SET PINS, 0 (0xE000) and SET PINDIRS, 0 (0xE080) so shared output latch is 0 (open-drain!) and bus is idle HIGH
    mmio_write(PIO0_BASE + 0x0D8, 0xE000);
    mmio_write(PIO0_BASE + 0x0D8, 0xE080);

    // Enable SM0
    mmio_write(PIO0_BASE + 0x000, 1);
}

struct PioWaveBuilder<'a> {
    words: &'a mut [u32],
    w_idx: usize,
    phase_in_word: u32,
    cur_word: u32,
}

impl<'a> PioWaveBuilder<'a> {
    fn new(words: &'a mut [u32]) -> Self {
        Self {
            words,
            w_idx: 0,
            phase_in_word: 0,
            cur_word: 0,
        }
    }

    #[inline(always)]
    fn push_phase(&mut self, sda_low: bool, scl_low: bool) {
        let pair = (sda_low as u32) | ((scl_low as u32) << 1);
        self.cur_word |= pair << (self.phase_in_word * 2);
        self.phase_in_word += 1;
        if self.phase_in_word == 16 {
            if self.w_idx < self.words.len() {
                self.words[self.w_idx] = self.cur_word;
                self.w_idx += 1;
            }
            self.cur_word = 0;
            self.phase_in_word = 0;
        }
    }

    fn i2c_start(&mut self) {
        self.push_phase(false, false);
        self.push_phase(true, false);
        self.push_phase(true, false);
        self.push_phase(true, true);
    }

    fn i2c_stop(&mut self) {
        self.push_phase(true, true);
        self.push_phase(true, false);
        self.push_phase(false, false);
        self.push_phase(false, false);
    }

    #[inline(always)]
    fn i2c_bit(&mut self, bit_high: bool) {
        let d_low = !bit_high;
        self.push_phase(d_low, true);
        self.push_phase(d_low, false);
        self.push_phase(d_low, false);
        self.push_phase(d_low, true);
    }

    fn i2c_write_byte(&mut self, byte: u8) {
        for i in (0..8).rev() {
            self.i2c_bit(((byte >> i) & 1) != 0);
        }
        // 9th bit: release SDA (bit_high=true -> d_low=false) so slave drives ACK low
        self.i2c_bit(true);
    }

    fn finish(mut self) -> usize {
        // Ensure at least 2 idle phases (SDA=H, SCL=H) at end, then pad partial word with idle (0b00)
        self.push_phase(false, false);
        self.push_phase(false, false);
        if self.phase_in_word > 0 && self.w_idx < self.words.len() {
            self.words[self.w_idx] = self.cur_word;
            self.w_idx += 1;
        }
        self.w_idx
    }
}

#[inline(always)]
fn pio0_drain_osr_fence() {
    // 16 PIO phases = 576 CPU cycles at CLKDIV=9; spin ~680 CPU cycles so OSR finishes shifting
    // cleanly regardless of whether TICKS counts clk_ref (silicon) or clk_sys (picoem)!
    for _ in 0..230 {
        unsafe { asm!("nop") };
    }
}

/// Stream a packed PIO waveform buffer via RP2350 DMA Channel 0 -> PIO0 TXF0 (DREQ_PIO0_TX0 = 0).
fn pio0_dma_transfer_blocking(words: &[u32]) {
    if words.is_empty() {
        return;
    }
    // Poll previous DMA Ch0 completion just in case (CTRL_TRIG bit 26 = BUSY on RP2350)
    while (mmio_read(DMA_BASE + 0x0C) & (1 << 26)) != 0 {}

    mmio_write(DMA_BASE + 0x00, words.as_ptr() as u32); // CH0_READ_ADDR
    mmio_write(DMA_BASE + 0x04, PIO0_BASE + 0x010);     // CH0_WRITE_ADDR = PIO0_TXF0
    mmio_write(DMA_BASE + 0x08, words.len() as u32);    // CH0_TRANS_COUNT
    // RP2350 DMA CTRL_TRIG: EN=1 (bit 0), DATA_SIZE=2 word (2<<2), INCR_READ=1 (1<<4),
    // INCR_WRITE=0, CHAIN_TO=0 (0<<13), TREQ_SEL=0 (DREQ_PIO0_TX0 = 0 << 17)
    let ctrl = (1 << 0) | (2 << 2) | (1 << 4) | (0 << 13) | (0 << 17);
    mmio_write(DMA_BASE + 0x0C, ctrl);

    // Wait for DMA to finish pushing all words into PIO0 TX FIFO
    while (mmio_read(DMA_BASE + 0x0C) & (1 << 26)) != 0 {
        core::hint::spin_loop();
    }
    // Wait for PIO0 SM0 TX FIFO to drain (FSTAT offset 0x004, bit 24 = TXEMPTY[0]) + final OSR word fence
    while (mmio_read(PIO0_BASE + 0x004) & (1 << 24)) == 0 {
        core::hint::spin_loop();
    }
    pio0_drain_osr_fence();
}

fn pio0_i2c_write_reg(addr: u8, reg: u8, val: u8) -> bool {
    let mut buf = [0u32; 12];
    let mut b = PioWaveBuilder::new(&mut buf);
    b.i2c_start();
    b.i2c_write_byte(addr << 1);
    b.i2c_write_byte(reg);
    b.i2c_write_byte(val);
    b.i2c_stop();
    let n = b.finish();
    pio0_dma_transfer_blocking(&buf[..n]);
    true
}

/// Read a single 8-bit register over PIO0 SM0 using its built-in ISR logic analyzer (`PUSH NOBLOCK`)!
fn pio0_i2c_read_reg(addr: u8, reg: u8) -> (u8, bool) {
    // 1. Write register pointer + Repeated START + (addr<<1 | 1)
    let mut hdr = [0u32; 12];
    let mut b = PioWaveBuilder::new(&mut hdr);
    b.i2c_start();
    b.i2c_write_byte(addr << 1);
    b.i2c_write_byte(reg);
    b.i2c_start();
    b.i2c_write_byte((addr << 1) | 1);
    // Keep SCL LOW at end of address ACK so bus pauses cleanly between nibbles!
    while b.phase_in_word != 0 {
        b.push_phase(false, true); // SDA released, SCL held LOW (clock stretch by master!)
    }
    let n_hdr = b.w_idx;
    pio0_dma_transfer_blocking(&hdr[..n_hdr]);

    // Helper: clock 4 read bits (16 phases = 1 TX word = 32 ISR bits) using hardware AUTOPUSH!
    // Force-execute `PUSH NOBLOCK` (0x8000) first so both ISR and `isr_shift_count` reset to 0
    // (RP2350 §11.4.7; also avoids picoem `MOV ISR, NULL` leaving `isr_count == 32`), wait 1 PIO
    // clock (9 sys_clk cycles) for SM0_INSTR to retire, drain RXF0, then enable AUTOPUSH!
    mmio_write(PIO0_BASE + 0x0D8, 0x8000); // PUSH NOBLOCK -> clears ISR & isr_count = 0
    for _ in 0..24 {
        unsafe { asm!("nop") };
    }
    while (mmio_read(PIO0_BASE + 0x004) & (1 << 8)) == 0 {
        let _ = mmio_read(PIO0_BASE + 0x020);
    }
    mmio_write(PIO0_BASE + 0x0D0, (1 << 19) | (1 << 17) | (1 << 16)); // Enable AUTOPUSH (thresh = 32)

    let read_nibble = || -> u8 {
        let mut wbuf = [0u32; 1];
        let mut nb = PioWaveBuilder::new(&mut wbuf);
        for _ in 0..4 {
            nb.i2c_bit(true); // Release SDA, pulse SCL 4 times (16 phases = 32 ISR bits!)
        }
        mmio_write(PIO0_BASE + 0x010, wbuf[0]); // Push 1 word to TXF0
        // Wait for hardware AUTOPUSH into RXF0 on the exact final IN PINS cycle of phase 15!
        while (mmio_read(PIO0_BASE + 0x004) & (1 << 8)) != 0 {
            core::hint::spin_loop();
        }
        let isr = mmio_read(PIO0_BASE + 0x020);
        // Phases p=2, 6, 10, 14 (middle of SCL=HIGH) sit at bit offsets 26, 18, 10, 2 (SDA = bit0 of pair)
        ((((isr >> 26) & 1) << 3)
            | (((isr >> 18) & 1) << 2)
            | (((isr >> 10) & 1) << 1)
            | ((isr >> 2) & 1)) as u8
    };

    let hi = read_nibble();
    let lo = read_nibble();
    mmio_write(PIO0_BASE + 0x0D0, (1 << 19) | (1 << 17)); // Restore AUTOPUSH=0 for write bursts

    // Send NACK (SDA=H) + STOP
    let mut tail = [0u32; 4];
    let mut tb = PioWaveBuilder::new(&mut tail);
    tb.i2c_bit(true); // Master NACK
    tb.i2c_stop();
    let n_tail = tb.finish();
    pio0_dma_transfer_blocking(&tail[..n_tail]);

    ((hi << 4) | lo, true)
}

// ============================================================================
// AW20198QNR Bring-Up (EM-Optimized Registers + D65 White-Balance SL Page)
// ============================================================================

fn init_aw20198(addr: u8) -> u8 {
    // Select Page 0 (0xF0 = 0xC0), read Chip ID at RSTN (0x2F -> 0x71)
    pio0_i2c_write_reg(addr, 0xF0, 0xC0);
    let (chip_id, _) = pio0_i2c_read_reg(addr, 0x2F);

    // Soft-reset AW20198 (0x2F = 0xAE), wait 1.5 ms t_reset
    pio0_i2c_write_reg(addr, 0x2F, 0xAE);
    delay_us(1500);

    // Page 0 EM-optimized configuration derived from Phases P2, P3, P4:
    pio0_i2c_write_reg(addr, 0xF0, 0xC0);
    pio0_i2c_write_reg(addr, 0x2B, 0x07); // SRCR: SRR=1 (6 ns rise), SRF=11 (10 ns fall) -> -30.4 dB EMI!
    pio0_i2c_write_reg(addr, 0x29, 0x02); // PCCR: PSEL=10 (Three-Phase PWM stagger -> 5.4x lower PVCC ripple!)
    pio0_i2c_write_reg(addr, 0x28, 0x15); // SSCR: Spread spectrum enabled (+/-10% modulation)
    pio0_i2c_write_reg(addr, 0x02, 0x44); // DGCR: Off-time 4 kOhm CS pull-up & 2 kOhm SW bleed de-ghosting
    pio0_i2c_write_reg(addr, 0x01, 220);  // GCCR: Initial global current

    // Page 2 (0xF0 = 0xC2): Burst-write all 198 SL current-scaling registers (D65 white balance: R=255, G=96, B=220)
    pio0_i2c_write_reg(addr, 0xF0, 0xC2);
    static mut SL_WAVE: [u32; 464] = [0; 464];
    unsafe {
        let words = &mut *core::ptr::addr_of_mut!(SL_WAVE);
        let mut wb = PioWaveBuilder::new(words);
        wb.i2c_start();
        wb.i2c_write_byte(addr << 1);
        wb.i2c_write_byte(0x00); // Auto-increment from SL0..SL197
        for row in 0..11 {
            let _ = row;
            for _col in 0..6 {
                wb.i2c_write_byte(255); // Red (100-180 mcd)
                wb.i2c_write_byte(96);  // Green (350-800 mcd -> attenuated 2.65x for D65 white!)
                wb.i2c_write_byte(220); // Blue (120-180 mcd)
            }
        }
        wb.i2c_stop();
        let n = wb.finish();
        pio0_dma_transfer_blocking(&words[..n]);
    }

    // Enable active scanning in Page 0 GCR (0x00 = 0xB9: SW1..SW11 active, LGC=1 2.4/0.6V, CHIPEN=1)
    pio0_i2c_write_reg(addr, 0xF0, 0xC0);
    pio0_i2c_write_reg(addr, 0x00, 0xB9);
    // Leave Page 1 (PWM page 0xC1) selected for fast streaming!
    pio0_i2c_write_reg(addr, 0xF0, 0xC1);

    chip_id
}

// ============================================================================
// Dual-Core Ping-Pong DMA Frame Buffers & Core 1 Streaming Worker
// ============================================================================

#[repr(C, align(4))]
struct DualDriverWavePacket {
    u1_len: usize,
    u2_len: usize,
    u1_words: [u32; 480],
    u2_words: [u32; 480],
}

static mut WAVE_PING_PONG: [DualDriverWavePacket; 2] = [
    DualDriverWavePacket { u1_len: 0, u2_len: 0, u1_words: [0; 480], u2_words: [0; 480] },
    DualDriverWavePacket { u1_len: 0, u2_len: 0, u1_words: [0; 480], u2_words: [0; 480] },
];

// Use volatile + explicit DMB SY barrier rather than Ordering::Acquire/Release (`lda`/`stl`),
// since Armv8-M `lda`/`stl` (0xE8D0/0xE8C0 0x_FAF) falls through to LDRD/STRD with Rt2=PC in picoem v0.2.6!
static mut CORE1_READY: u32 = 0;

fn encode_driver_frame_wave(addr: u8, gcc: u8, pwm_198: &[u8; 198], out_words: &mut [u32; 480]) -> usize {
    let mut wb = PioWaveBuilder::new(out_words);
    // Transaction 1: Page 0 -> update GCCR (0x01) -> switch to Page 1 (0xC1)
    wb.i2c_start();
    wb.i2c_write_byte(addr << 1);
    wb.i2c_write_byte(0xF0);
    wb.i2c_write_byte(0xC0);
    wb.i2c_stop();

    wb.i2c_start();
    wb.i2c_write_byte(addr << 1);
    wb.i2c_write_byte(0x01);
    wb.i2c_write_byte(gcc);
    wb.i2c_stop();

    wb.i2c_start();
    wb.i2c_write_byte(addr << 1);
    wb.i2c_write_byte(0xF0);
    wb.i2c_write_byte(0xC1);
    wb.i2c_stop();

    // Transaction 2: 198-byte contiguous PWM0..PWM197 burst!
    wb.i2c_start();
    wb.i2c_write_byte(addr << 1);
    wb.i2c_write_byte(0x00);
    for &b in pwm_198.iter() {
        wb.i2c_write_byte(b);
    }
    wb.i2c_stop();
    wb.finish()
}

/// Standard RP2350 Bootrom Multicore Launch Protocol over SIO FIFO.
fn launch_core1() {
    let vtor = (&CORE1_VECTORS as *const _ as u32) & !0x7F;
    let sp = 0x2008_0000u32;
    let entry = (core1_entry as *const () as u32) | 1;
    let cmds = [0u32, 0, 1, vtor, sp, entry];

    let mut i = 0;
    while i < cmds.len() {
        let cmd = cmds[i];
        if cmd == 0 {
            // Drain RX FIFO (SIO_FIFO_ST 0x050 bit 0 = VLD)
            while (mmio_read(SIO_BASE + 0x050) & 1) != 0 {
                let _ = mmio_read(SIO_BASE + 0x058);
            }
            unsafe { asm!("sev") };
        }
        // Wait TX FIFO ready (bit 1 = RDY)
        while (mmio_read(SIO_BASE + 0x050) & 2) == 0 {}
        mmio_write(SIO_BASE + 0x054, cmd);
        unsafe { asm!("sev") };

        // Wait RX response
        while (mmio_read(SIO_BASE + 0x050) & 1) == 0 {
            unsafe { asm!("wfe") };
        }
        let resp = mmio_read(SIO_BASE + 0x058);
        if resp == cmd {
            i += 1;
        } else {
            i = 0;
        }
    }
}

/// Core 1 Entry: enables its own VFPv5 FPU, signals readiness, and streams ping-pong DMA frames to PIO0!
pub unsafe extern "C" fn core1_entry() -> ! {
    mmio_write(SCB_CPACR, mmio_read(SCB_CPACR) | (0xF << 20));
    unsafe {
        asm!("dsb sy", "isb sy");
        write_volatile(core::ptr::addr_of_mut!(CORE1_READY), 1);
        asm!("dmb sy");
    }

    loop {
        // Wait for ping-pong slot index (0 or 1) from Core 0 via SIO FIFO.
        // Note: use YIELD (`spin_loop`) rather than WFE in steady-state streaming because
        // `picoem` v0.2.6 freezes `cs[c].cycles` during WFE and bursts the accumulated cycle
        // delta inside a single `emu.step()` on wake, starving sub-microsecond GPIO co-sim!
        while (mmio_read(SIO_BASE + 0x050) & 1) == 0 {
            core::hint::spin_loop();
        }
        let slot = (mmio_read(SIO_BASE + 0x058) & 1) as usize;
        let pkt = unsafe { &*core::ptr::addr_of!(WAVE_PING_PONG[slot]) };

        pio0_dma_transfer_blocking(&pkt.u1_words[..pkt.u1_len]);
        pio0_dma_transfer_blocking(&pkt.u2_words[..pkt.u2_len]);

        unsafe {
            let n = (*mbox()).core1_frames_dma.wrapping_add(1);
            write_volatile(&mut (*mbox()).core1_frames_dma, n);
        }
        // Return completion token to Core 0
        while (mmio_read(SIO_BASE + 0x050) & 2) == 0 {}
        mmio_write(SIO_BASE + 0x054, slot as u32);
        unsafe { asm!("sev") };
    }
}

// ============================================================================
// VFPv5 Fast Math, Sensors, PDN Foldback, & Skewed-Parallelogram Shaders
// ============================================================================

/// Truncate `f32 -> i32` directly via LLVM `fptosi` (`VCVT.S32.F32` `0xEEBD`),
/// avoiding Rust's saturating `as i32/u32` lowering (`0xFE__` `VSEL`/`VMAXNM`/`VMINNM`,
/// where `rp2350-emu v0.2.6` `execute_fpu.rs:630` decodes `D` from `hw0[4]` instead of `hw0[6]`).
#[inline(always)]
fn f32_to_i32_hw(x: f32) -> i32 {
    let clamped = f32_clamp(x, -1.0e8, 1.0e8);
    unsafe { clamped.to_int_unchecked::<i32>() }
}

#[inline(always)]
fn i32_to_f32_hw(v: i32) -> f32 {
    v as f32
}

#[inline(always)]
fn f32_abs(x: f32) -> f32 {
    f32::from_bits(x.to_bits() & 0x7FFF_FFFF)
}

#[inline(always)]
fn f32_clamp(x: f32, lo: f32, hi: f32) -> f32 {
    // IEEE-754 integer-order comparison avoids emitting Armv8-M `VSEL` / `VMAXNM` (`0xFE__`)
    let xb = x.to_bits() as i32;
    let x_ord = xb ^ (((xb >> 31) as u32 >> 1) as i32);
    let lob = lo.to_bits() as i32;
    let lo_ord = lob ^ (((lob >> 31) as u32 >> 1) as i32);
    let hib = hi.to_bits() as i32;
    let hi_ord = hib ^ (((hib >> 31) as u32 >> 1) as i32);
    let c_ord = x_ord.max(lo_ord).min(hi_ord);
    let cb = c_ord ^ (((c_ord >> 31) as u32 >> 1) as i32);
    f32::from_bits(cb as u32)
}

#[inline(always)]
fn hw_sqrtf(x: f32) -> f32 {
    if (x.to_bits() as i32) <= 0 {
        return 0.0;
    }
    let mut y = f32::from_bits(0x5f37_5a86 - (x.to_bits() >> 1));
    let half_x = 0.5 * x;
    y = y * (1.5 - half_x * y * y);
    y = y * (1.5 - half_x * y * y);
    x * y
}

/// Accurate minimax-style fast sine on any radian input using VFPv5 FMA.
#[inline(always)]
fn fast_sinf(x_in: f32) -> f32 {
    const INV_TAU_Q16: f32 = 10430.378; // 65536 / (2*pi)
    // Wrap phase cleanly in 16-bit signed integer angle [-32768, 32767] -> [-pi, pi)!
    let ang_i16 = (f32_to_i32_hw(x_in * INV_TAU_Q16) as i16) as i32;
    let x = i32_to_f32_hw(ang_i16) * 0.000_095_873_8; // pi / 32768
    let y = 1.273_239_5 * x - 0.405_284_73 * x * f32_abs(x);
    0.225 * (y * f32_abs(y) - y) + y
}

#[inline(always)]
fn fast_cosf(x: f32) -> f32 {
    fast_sinf(x + 1.570_796_4)
}

/// Read 8x-oversampled RP2350 ADC channel (0 = GPIO26 VBAT_SENSE, 1 = GPIO27 LIGHT).
/// Oversampling 8x averages out the 148 mV / 2 ns VREG_LX buck spikes found in Phase P2!
fn read_adc_oversampled_8x(ch: u32) -> u16 {
    unsafe {
        if read_volatile(&(*mbox()).sim_stim_magic) == SIM_STIM_MAGIC {
            return if ch == 0 {
                read_volatile(&(*mbox()).sim_vbat_adc_12b) as u16
            } else {
                read_volatile(&(*mbox()).sim_light_adc_12b) as u16
            };
        }
    }
    let mut acc = 0u32;
    for _ in 0..8 {
        // CS: AINSEL = ch << 12, START_ONCE = 1 << 2, EN = 1
        mmio_write(ADC_BASE + 0x00, 1 | (1 << 2) | ((ch & 0x7) << 12));
        while (mmio_read(ADC_BASE + 0x00) & (1 << 8)) == 0 {} // Poll READY bit 8
        acc += mmio_read(ADC_BASE + 0x04) & 0x0FFF;
    }
    (acc >> 3) as u16
}

/// Phase P4 PDN-Derived GCC(VBAT) Foldback Curve:
/// Above 3650 mV -> 255; between 3000..3650 mV -> linear foldback 51..255 preventing North D1 Blue/Green dropout!
fn compute_pdn_safe_gcc(vbat_mv: u32, light_12b: u16) -> u8 {
    let vbat_cap: u32 = if vbat_mv >= 3650 {
        255
    } else if vbat_mv <= 3000 {
        51
    } else {
        51 + ((vbat_mv - 3000) * 204) / 650
    };
    // Ambient auto-brightness scaling (floor = 35% indoors, 100% = 256/256 in bright ambient)
    let lux_scale = 90 + ((light_12b.min(4095) as u32) * 166) / 4095;
    let gcc = (vbat_cap * lux_scale) >> 8;
    gcc.clamp(28, 255) as u8
}

/// Gamma 2.2 LUT approximation `(x^2 * (192 + 63*x))` on Q12 input `[0..4096]` -> `0..255`.
#[inline(always)]
fn gamma_q12_u8(v_q12: i32) -> u8 {
    let c = v_q12.clamp(0, 4096) as u32;
    let c2 = (c * c) >> 12; // 0..4096
    let mix = 3072 + ((c * 1024) >> 12); // 0.75 + 0.25*c in Q12 (3072..4096)
    let g_q12 = (c2 * mix) >> 12; // 0..4096
    (((g_q12 * 255) + 2048) >> 12).min(255) as u8
}

fn hsv_to_rgb(h: f32, s: f32, v: f32) -> (u8, u8, u8) {
    // Convert float shader outputs to Q12 via explicit VCVT.S32.F32 (no 0xFE__ VSEL/VMAXNM)
    let h_wrapped = (f32_to_i32_hw(h * 4096.0)).rem_euclid(4096) as u32;
    let s_q12 = f32_to_i32_hw(s * 4096.0).clamp(0, 4096) as u32;
    let v_q12 = f32_to_i32_hw(v * 4096.0).clamp(0, 4096) as u32;

    let hh = h_wrapped * 6; // 0..24575
    let sector = (hh >> 12).min(5);
    let frac = hh & 0xFFF; // 0..4095

    let p = (v_q12 * (4096 - s_q12)) >> 12;
    let q = (v_q12 * (4096 - ((s_q12 * frac) >> 12))) >> 12;
    let t = (v_q12 * (4096 - ((s_q12 * (4096 - frac)) >> 12))) >> 12;

    let (r, g, b) = match sector {
        0 => (v_q12, t, p),
        1 => (q, v_q12, p),
        2 => (p, v_q12, t),
        3 => (p, q, v_q12),
        4 => (t, p, v_q12),
        _ => (v_q12, p, q),
    };
    (gamma_q12_u8(r as i32), gamma_q12_u8(g as i32), gamma_q12_u8(b as i32))
}

/// Render all 132 LEDs using their EXACT physical skewed-parallelogram coordinates on `p2-132`:
///   x_mm(col)      = -9.25 + 3.70 * col                      (col = 0..5)
///   y_mm(col, row) = -30.25 + 1.15 * col + 2.60 * row        (row = 0..21; 0..10 = U1, 11..21 = U2)
fn render_p2_132_frame(
    mode: u32,
    t_sec: f32,
    ax_g: f32,
    ay_g: f32,
    vbat_mv: u32,
    light_12b: u16,
    u1_pwm: &mut [u8; 198],
    u2_pwm: &mut [u8; 198],
) {
    for row in 0..22usize {
        for col in 0..6usize {
            let x = -9.25 + 3.70 * i32_to_f32_hw(col as i32);
            let y = -30.25 + 1.15 * i32_to_f32_hw(col as i32) + 2.60 * i32_to_f32_hw(row as i32);

            let (r, g, b) = match mode & 3 {
                // Mode 0: Aurora Shear Wave -- wavefronts aligned & counter-propagating along the 17.75 deg lattice!
                0 => {
                    let u_shear = 0.085 * x + 0.095 * (y - 0.3108 * x);
                    let w1 = fast_sinf(6.283 * (u_shear - 0.65 * t_sec + 0.18 * ax_g));
                    let w2 = fast_cosf(0.22 * y + 2.4 * t_sec + 1.5 * ay_g);
                    let hue = 0.48 + 0.22 * w1 + 0.10 * w2;
                    let val = 0.52 + 0.48 * (0.5 + 0.5 * fast_sinf(0.18 * x - 0.14 * y + 3.1 * t_sec));
                    hsv_to_rgb(hue, 0.88, val)
                }
                // Mode 1: Accelerometer Gravity Liquid Pool + Surface Ripples
                1 => {
                    let gx = f32_clamp(ax_g, -1.2, 1.2);
                    let gy = f32_clamp(ay_g, -1.2, 1.2);
                    let level = x * gx * 0.85 + y * gy * 0.55;
                    let ripple = 2.2 * fast_sinf(0.35 * x + 4.8 * t_sec);
                    let depth = (level + ripple + 6.0) * 0.075;
                    let v = f32_clamp(depth, 0.06, 1.0);
                    let menisc = 1.0 - f32_clamp(f32_abs(level + ripple) * 0.28, 0.0, 1.0);
                    let hue = 0.55 - 0.18 * v + 0.08 * menisc;
                    hsv_to_rgb(hue, 0.92 - 0.45 * menisc, f32_clamp(v + 0.35 * menisc, 0.05, 1.0))
                }
                // Mode 2: Crystalline Rhombus Radial Interference
                2 => {
                    let cx = 5.5 * ax_g;
                    let cy = 12.0 * ay_g;
                    let dx = x - cx;
                    let dy = y - cy;
                    let r_mm = hw_sqrtf(dx * dx + dy * dy);
                    let ring = 0.5 + 0.5 * fast_cosf(0.34 * r_mm - 4.2 * t_sec);
                    let diag = 0.5 + 0.5 * fast_sinf(0.26 * (y - 0.3108 * x) + 2.0 * t_sec);
                    let hue = 0.82 + 0.32 * (r_mm * 0.025) - 0.15 * t_sec;
                    hsv_to_rgb(hue, 0.85, f32_clamp(0.18 + 0.82 * ring * diag, 0.05, 1.0))
                }
                // Mode 3: Live Battery SoC Bar (left 3 cols, South->North) + Ambient Lux Bar (right 3 cols)
                _ => {
                    let soc = f32_clamp(i32_to_f32_hw(vbat_mv.saturating_sub(3100) as i32) * (1.0 / 1050.0), 0.05, 1.0);
                    let lux = f32_clamp(i32_to_f32_hw(light_12b as i32) * (1.0 / 4095.0), 0.05, 1.0);
                    // Row 21 is South bottom, Row 0 is North top
                    let frac = (i32_to_f32_hw((21 - row) as i32) + 0.5) * (1.0 / 22.0);
                    let frac_ord = f32_to_i32_hw(frac * 4096.0);
                    if col < 3 {
                        if frac_ord <= f32_to_i32_hw(soc * 4096.0) {
                            let hue = 0.02 + 0.32 * soc; // Red -> Emerald Green
                            hsv_to_rgb(hue, 0.95, 0.85)
                        } else {
                            (6, 8, 14)
                        }
                    } else if frac_ord <= f32_to_i32_hw(lux * 4096.0) {
                        hsv_to_rgb(0.13 + 0.42 * frac, 0.80, 0.85)
                    } else {
                        (8, 6, 12)
                    }
                }
            };

            if row < 11 {
                let base = row * 18 + col * 3;
                u1_pwm[base] = r;
                u1_pwm[base + 1] = g;
                u1_pwm[base + 2] = b;
            } else {
                let base = (row - 11) * 18 + col * 3;
                u2_pwm[base] = r;
                u2_pwm[base + 1] = g;
                u2_pwm[base + 2] = b;
            }
        }
    }
}

// ============================================================================
// Core 0 Reset Handler & Main Application Loop
// ============================================================================

#[unsafe(no_mangle)]
pub unsafe extern "C" fn _reset() -> ! {
    // 1. Enable Cortex-M33 VFPv5 FPU (CP10 & CP11 full access) BEFORE any f32 instructions run!
    mmio_write(SCB_CPACR, mmio_read(SCB_CPACR) | (0xF << 20));
    unsafe { asm!("dsb sy", "isb sy") };

    // 2. Copy .data from XIP Flash to SRAM and zero .bss
    unsafe {
        let mut src = core::ptr::addr_of!(_sidata);
        let mut dst = core::ptr::addr_of_mut!(_sdata);
        let end = core::ptr::addr_of_mut!(_edata);
        while dst < end {
            write_volatile(dst, read_volatile(src));
            src = src.add(1);
            dst = dst.add(1);
        }
        let mut bss = core::ptr::addr_of_mut!(_sbss);
        let bss_end = core::ptr::addr_of_mut!(_ebss);
        while bss < bss_end {
            write_volatile(bss, 0);
            bss = bss.add(1);
        }
    }

    // 3. Initialize telemetry mailbox (preserving any pre-seeded sim_stim_magic / max_frames_limit!)
    unsafe {
        write_volatile(&mut (*mbox()).fw_magic, FW_TELEM_MAGIC);
        write_volatile(&mut (*mbox()).boot_stage, 1);
        write_volatile(&mut (*mbox()).i2c_ack_errors, 0);
        write_volatile(&mut (*mbox()).core0_frames, 0);
        write_volatile(&mut (*mbox()).core1_frames_dma, 0);
        write_volatile(&mut (*mbox()).active_mode, 0);
    }

    // 4. Bring up 150 MHz PLL_SYS + 1 us TIMER0 + GPIOs + PIO0 1.04 MHz I2C Master
    init_clocks_150mhz();
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 2) };
    init_peripherals_and_pins();
    init_pio0_i2c_master();

    // Gate ON VBAT_EN (GPIO14), LIGHT_PWR (GPIO1), and AW20198 hardware enable LED_SDB (GPIO6)!
    mmio_write(
        SIO_BASE + 0x18, // GPIO_OUT_SET
        (1 << PIN_VBAT_EN) | (1 << PIN_LIGHT_PWR) | (1 << PIN_LED_SDB),
    );
    delay_us(1200); // t_init after SDB rises (AW20198 datasheet >= 1 ms)

    // 5. Bring up LIS2DW12TR accelerometer on GPIO2/3 (0x19)
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 3) };
    let mut who = [0u8; 1];
    let _ = lis2dw12_read_regs(0x0F, &mut who);
    unsafe { write_volatile(&mut (*mbox()).lis_whoami, who[0] as u32) };
    let _ = lis2dw12_write_reg(0x21, 0x0C); // CTRL2: BDU=1, IF_ADD_INC=1
    let _ = lis2dw12_write_reg(0x25, 0x04); // CTRL6: +/-2g, low-noise
    let _ = lis2dw12_write_reg(0x20, 0x54); // CTRL1: 100 Hz High-Performance

    // 6. Bring up North (0x20) & South (0x25) AW20198QNR 18x11 LED matrix drivers over PIO0 + DMA!
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 4) };
    let id1 = init_aw20198(ADDR_AW1_NORTH);
    let id2 = init_aw20198(ADDR_AW2_SOUTH);
    unsafe {
        write_volatile(&mut (*mbox()).aw1_chip_id, id1 as u32);
        write_volatile(&mut (*mbox()).aw2_chip_id, id2 as u32);
    }

    // 7. Launch Core 1 DMA streaming worker via RP2350 Bootrom SIO FIFO handshake
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 5) };
    launch_core1();
    while unsafe { read_volatile(core::ptr::addr_of!(CORE1_READY)) } == 0 {
        core::hint::spin_loop();
    }
    unsafe { asm!("dmb sy") };
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 6) };

    // 8. Pipelined Dual-Core Render + DMA Loop!
    let mut u1_pwm = [0u8; 198];
    let mut u2_pwm = [0u8; 198];
    let mut slot: usize = 0;
    let mut core1_in_flight = false;
    let mut mode: u32 = 0;
    let mut prev_btn_pressed = false;
    let mut frame_idx: u32 = 0;

    loop {
        // Sample GPIO status inputs (BTN active-low on GPIO11, CHG GPIO12, PGOOD GPIO13)
        let gpio_in = mmio_read(SIO_BASE + 0x04);
        let btn_pressed = ((gpio_in >> PIN_BTN) & 1) == 0;
        let chg_active = ((gpio_in >> PIN_CHG) & 1) == 0;
        let pgood_active = ((gpio_in >> PIN_PGOOD) & 1) == 0;
        if btn_pressed && !prev_btn_pressed {
            mode = (mode + 1) & 3;
        }
        prev_btn_pressed = btn_pressed;

        // Read 8x-oversampled VBAT_SENSE (ADC0, /2 divider: mV = adc * 6600 / 4095) and LIGHT (ADC1)
        let vbat_adc = read_adc_oversampled_8x(0);
        let light_adc = read_adc_oversampled_8x(1);
        let vbat_mv = ((vbat_adc as u32) * 6600) / 4095;
        let gcc = compute_pdn_safe_gcc(vbat_mv, light_adc);

        // Read 6-byte acceleration burst from LIS2DW12TR (0x28..0x2D, 14-bit left-justified +/-2g -> 16384 LSB/g)
        let mut raw_xyz = [0u8; 6];
        let _ = lis2dw12_read_regs(0x28, &mut raw_xyz);
        let rx = i16::from_le_bytes([raw_xyz[0], raw_xyz[1]]);
        let ry = i16::from_le_bytes([raw_xyz[2], raw_xyz[3]]);
        let rz = i16::from_le_bytes([raw_xyz[4], raw_xyz[5]]);
        let ax_g = (rx as f32) * (1.0 / 16384.0);
        let ay_g = (ry as f32) * (1.0 / 16384.0);
        let az_g = (rz as f32) * (1.0 / 16384.0);

        // Render next 132-LED frame on Core 0 while Core 1 finishes streaming the previous frame!
        let t_sec = (frame_idx as f32) * 0.040;
        render_p2_132_frame(mode, t_sec, ax_g, ay_g, vbat_mv, light_adc, &mut u1_pwm, &mut u2_pwm);

        unsafe {
            let pkt = &mut *core::ptr::addr_of_mut!(WAVE_PING_PONG[slot]);
            pkt.u1_len = encode_driver_frame_wave(ADDR_AW1_NORTH, gcc, &u1_pwm, &mut pkt.u1_words);
            pkt.u2_len = encode_driver_frame_wave(ADDR_AW2_SOUTH, gcc, &u2_pwm, &mut pkt.u2_words);
        }

        // Wait for previous Core 1 DMA batch to complete before dispatching new slot
        if core1_in_flight {
            while (mmio_read(SIO_BASE + 0x050) & 1) == 0 {
                core::hint::spin_loop();
            }
            let _done_slot = mmio_read(SIO_BASE + 0x058);
        }

        // Publish live telemetry
        frame_idx = frame_idx.wrapping_add(1);
        unsafe {
            write_volatile(&mut (*mbox()).core0_frames, frame_idx);
            write_volatile(&mut (*mbox()).active_mode, mode);
            write_volatile(&mut (*mbox()).active_gcc, gcc as u32);
            write_volatile(&mut (*mbox()).vbat_mv, vbat_mv);
            write_volatile(&mut (*mbox()).light_raw, light_adc as u32);
            write_volatile(&mut (*mbox()).accel_mg_x, (ax_g * 1000.0) as i32);
            write_volatile(&mut (*mbox()).accel_mg_y, (ay_g * 1000.0) as i32);
            write_volatile(&mut (*mbox()).accel_mg_z, (az_g * 1000.0) as i32);
            write_volatile(
                &mut (*mbox()).status_flags,
                (chg_active as u32) | ((pgood_active as u32) << 1) | ((btn_pressed as u32) << 2),
            );
        }

        // Dispatch current slot to Core 1 over SIO FIFO!
        while (mmio_read(SIO_BASE + 0x050) & 2) == 0 {}
        mmio_write(SIO_BASE + 0x054, slot as u32);
        unsafe { asm!("sev") };
        core1_in_flight = true;
        slot ^= 1;

        // Optional simulation frame limit check (0 on real silicon -> runs forever!)
        let max_lim = unsafe { read_volatile(&(*mbox()).max_frames_limit) };
        if max_lim != 0 && frame_idx >= max_lim {
            // Wait for final in-flight Core 1 DMA frame to finish before halting cleanly with BKPT #0!
            while (mmio_read(SIO_BASE + 0x050) & 1) == 0 {
                core::hint::spin_loop();
            }
            let _ = mmio_read(SIO_BASE + 0x058);
            unsafe { asm!("bkpt #0") };
            loop {
                unsafe { asm!("wfi") };
            }
        }
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn _fault_handler() -> ! {
    unsafe { write_volatile(&mut (*mbox()).boot_stage, 0xDEAD) };
    unsafe { asm!("bkpt #1") };
    loop {
        unsafe { asm!("wfi") };
    }
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    unsafe { _fault_handler() }
}
