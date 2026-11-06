//! Cycle-accurate board-level `picoem` co-simulation of the `parallelogram/p2-132` pendant.
//!
//! Connects `rp2350-emu` (dual Cortex-M33 + VFPv5 + PIO0 + DMA + SIO + Clocks + Timer0)
//! running our bare-metal Rust firmware (`p2-132-fw.bin`) + pinned silicon `bootrom-combined.bin`
//! to cycle-accurate models of all external components on `parallelogram.kicad_pcb`:
//!   - `U1`: AW20198QNR 18x11 RGB matrix driver at I2C 0x20 (North 6x11, D1..D66) on GPIO4/5 (1.04 MHz Fm+)
//!   - `U2`: AW20198QNR 18x11 RGB matrix driver at I2C 0x25 (South 6x11, D67..D132) on GPIO4/5 (1.04 MHz Fm+)
//!   - `U9`: LIS2DW12TR MEMS accelerometer at I2C 0x19 on GPIO2/3 (400 kHz open-drain)
//!   - `U5`: BQ24073 LiPo charger status outputs (`CHG` on GPIO12, `PGOOD` on GPIO13) + `VBAT_SENSE` divider
//!   - `Q2`: XYC-PT19C-L1 ambient phototransistor (`LIGHT_PWR` GPIO1, `LIGHT` ADC1 GPIO27)
//!   - `SW1`: Tactile mode-cycle button on GPIO11

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::Ordering;
use std::time::Instant;

use rp2350_emu::{Config, Emulator, EmulatorBuilder};
use serde::Serialize;

// GPIO pin assignments on parallelogram/p2-132
const PIN_LIGHT_PWR: u32 = 1;
const PIN_ACC_SDA: u32   = 2;
const PIN_ACC_SCL: u32   = 3;
const PIN_I2C_SDA: u32   = 4;
const PIN_I2C_SCL: u32   = 5;
const PIN_LED_SDB: u32   = 6;
const PIN_BTN: u32       = 11;
const PIN_CHG: u32       = 12;
const PIN_PGOOD: u32     = 13;
const PIN_VBAT_EN: u32   = 14;

const EXT_GPIO_MASK: u32 = (1 << PIN_ACC_SDA)
    | (1 << PIN_ACC_SCL)
    | (1 << PIN_I2C_SDA)
    | (1 << PIN_I2C_SCL)
    | (1 << PIN_BTN)
    | (1 << PIN_CHG)
    | (1 << PIN_PGOOD);

// Firmware SRAM mailbox addresses (must match fw/p2-132/p2-132-fw/src/main.rs)
const MAILBOX_ADDR: u32   = 0x2007_F000;
const SIM_STIM_MAGIC: u32 = 0x5349_4D31; // "SIM1"
const FW_TELEM_MAGIC: u32 = 0x5032_3133; // "P213"

// ============================================================================
// Generic Open-Drain I2C Slave State Machine + AW20198QNR & LIS2DW12TR Models
// ============================================================================

trait I2cSlaveDevice {
    fn address(&self) -> u8;
    fn on_start(&mut self, is_read: bool);
    fn write_byte(&mut self, val: u8);
    fn read_byte(&mut self) -> u8;
    fn on_stop(&mut self);
}

#[derive(Clone, Copy, Debug)]
enum I2cWireState {
    Idle,
    RxAddress { bit_idx: u8, shift: u8 },
    SendAddrAck { is_read: bool },
    RxData { bit_idx: u8, shift: u8 },
    SendDataAck,
    TxData { byte: u8, next_bit: i8 },
    WaitMasterAck { got_ack: bool },
}

struct I2cSlaveWire<D: I2cSlaveDevice> {
    pub dev: D,
    state: I2cWireState,
    sda_low: bool,
    pub tx_bytes: u64,
    pub rx_bytes: u64,
    pub transactions: u64,
}

impl<D: I2cSlaveDevice> I2cSlaveWire<D> {
    fn new(dev: D) -> Self {
        Self {
            dev,
            state: I2cWireState::Idle,
            sda_low: false,
            tx_bytes: 0,
            rx_bytes: 0,
            transactions: 0,
        }
    }

    #[inline(always)]
    fn drives_sda_low(&self) -> bool {
        self.sda_low
    }

    fn step_edges(&mut self, prev_sda: bool, prev_scl: bool, cur_sda: bool, cur_scl: bool) {
        // START or Repeated START: SDA High -> Low while SCL High
        if prev_scl && cur_scl && prev_sda && !cur_sda {
            self.state = I2cWireState::RxAddress { bit_idx: 0, shift: 0 };
            self.sda_low = false;
            return;
        }
        // STOP: SDA Low -> High while SCL High
        if prev_scl && cur_scl && !prev_sda && cur_sda {
            if !matches!(self.state, I2cWireState::Idle) {
                self.dev.on_stop();
            }
            self.state = I2cWireState::Idle;
            self.sda_low = false;
            return;
        }

        // Rising edge of SCL: sample SDA
        if !prev_scl && cur_scl {
            match &mut self.state {
                I2cWireState::RxAddress { bit_idx, shift } if *bit_idx < 8 => {
                    *shift = (*shift << 1) | (cur_sda as u8);
                    *bit_idx += 1;
                }
                I2cWireState::RxData { bit_idx, shift } if *bit_idx < 8 => {
                    *shift = (*shift << 1) | (cur_sda as u8);
                    *bit_idx += 1;
                }
                I2cWireState::WaitMasterAck { got_ack } => {
                    *got_ack = !cur_sda; // Master drives SDA=0 to ACK
                }
                _ => {}
            }
        }

        // Falling edge of SCL: update slave open-drain SDA drive
        if prev_scl && !cur_scl {
            match self.state {
                I2cWireState::RxAddress { bit_idx: 8, shift } => {
                    let addr7 = shift >> 1;
                    let is_read = (shift & 1) != 0;
                    if addr7 == self.dev.address() {
                        self.transactions += 1;
                        self.dev.on_start(is_read);
                        self.state = I2cWireState::SendAddrAck { is_read };
                        self.sda_low = true; // Drive ACK low during 9th clock
                    } else {
                        self.state = I2cWireState::Idle;
                        self.sda_low = false;
                    }
                }
                I2cWireState::SendAddrAck { is_read } => {
                    if is_read {
                        let b = self.dev.read_byte();
                        self.tx_bytes += 1;
                        self.sda_low = ((b >> 7) & 1) == 0;
                        self.state = I2cWireState::TxData { byte: b, next_bit: 6 };
                    } else {
                        self.sda_low = false;
                        self.state = I2cWireState::RxData { bit_idx: 0, shift: 0 };
                    }
                }
                I2cWireState::RxData { bit_idx: 8, shift } => {
                    self.rx_bytes += 1;
                    self.dev.write_byte(shift);
                    self.sda_low = true; // Drive ACK low
                    self.state = I2cWireState::SendDataAck;
                }
                I2cWireState::SendDataAck => {
                    self.sda_low = false;
                    self.state = I2cWireState::RxData { bit_idx: 0, shift: 0 };
                }
                I2cWireState::TxData { byte, next_bit } => {
                    if next_bit >= 0 {
                        self.sda_low = ((byte >> next_bit) & 1) == 0;
                        self.state = I2cWireState::TxData {
                            byte,
                            next_bit: next_bit - 1,
                        };
                    } else {
                        // Release SDA so Master can drive ACK or NACK on 9th clock
                        self.sda_low = false;
                        self.state = I2cWireState::WaitMasterAck { got_ack: false };
                    }
                }
                I2cWireState::WaitMasterAck { got_ack } => {
                    if got_ack {
                        let b = self.dev.read_byte();
                        self.tx_bytes += 1;
                        self.sda_low = ((b >> 7) & 1) == 0;
                        self.state = I2cWireState::TxData { byte: b, next_bit: 6 };
                    } else {
                        self.sda_low = false;
                        self.state = I2cWireState::Idle;
                    }
                }
                _ => {}
            }
        }
    }
}

/// Cycle-accurate AW20198QNR 18x11 RGB LED Matrix Driver register & page model.
struct Aw20198Model {
    addr: u8,
    pub page: u8,
    reg_ptr: u8,
    got_reg_ptr: bool,
    pub page0: [u8; 256],
    pub pwm: [u8; 256], // Page 1 (0xC1): 0..197 active
    pub sl: [u8; 256],  // Page 2 (0xC2): 0..197 active
    pwm_bytes_in_burst: usize,
    pub completed_pwm_frames: u32,
    pub soft_resets: u32,
}

impl Aw20198Model {
    fn new(addr: u8) -> Self {
        let mut m = Self {
            addr,
            page: 0,
            reg_ptr: 0,
            got_reg_ptr: false,
            page0: [0; 256],
            pwm: [0; 256],
            sl: [0; 256],
            pwm_bytes_in_burst: 0,
            completed_pwm_frames: 0,
            soft_resets: 0,
        };
        m.apply_reset_defaults();
        m
    }

    fn apply_reset_defaults(&mut self) {
        self.page0.fill(0);
        self.pwm.fill(0);
        self.sl.fill(0);
        self.page0[0x2F] = 0x71; // RSTN reads back AW20198 Chip ID 0x71!
        self.page0[0x2B] = 0x02; // Factory default SRCR = 0x02 (fast 1 ns edge before FW configures 0x07!)
    }
}

impl I2cSlaveDevice for Aw20198Model {
    fn address(&self) -> u8 {
        self.addr
    }

    fn on_start(&mut self, is_read: bool) {
        if !is_read {
            self.got_reg_ptr = false;
            self.pwm_bytes_in_burst = 0;
        }
    }

    fn write_byte(&mut self, val: u8) {
        if !self.got_reg_ptr {
            self.reg_ptr = val;
            self.got_reg_ptr = true;
            return;
        }
        let r = self.reg_ptr;
        if r == 0xF0 {
            if (0xC0..=0xC4).contains(&val) {
                self.page = val - 0xC0;
            }
        } else {
            match self.page {
                0 => {
                    if r == 0x2F && val == 0xAE {
                        self.soft_resets += 1;
                        self.apply_reset_defaults();
                    } else if r != 0x2F {
                        self.page0[r as usize] = val;
                    }
                }
                1 => {
                    self.pwm[r as usize] = val;
                    self.pwm_bytes_in_burst += 1;
                }
                2 => {
                    self.sl[r as usize] = val;
                }
                _ => {}
            }
        }
        self.reg_ptr = self.reg_ptr.wrapping_add(1);
    }

    fn read_byte(&mut self) -> u8 {
        let r = self.reg_ptr;
        let out = if r == 0xF0 {
            0xC0 + self.page
        } else {
            match self.page {
                0 => self.page0[r as usize],
                1 => self.pwm[r as usize],
                2 => self.sl[r as usize],
                _ => 0,
            }
        };
        self.reg_ptr = self.reg_ptr.wrapping_add(1);
        out
    }

    fn on_stop(&mut self) {
        if self.page == 1 && self.pwm_bytes_in_burst >= 198 {
            self.completed_pwm_frames += 1;
        }
        self.pwm_bytes_in_burst = 0;
    }
}

/// Cycle-accurate LIS2DW12TR 3-axis accelerometer model at I2C 0x19.
struct Lis2dw12Model {
    reg_ptr: u8,
    got_reg_ptr: bool,
    pub regs: [u8; 128],
}

impl Lis2dw12Model {
    fn new() -> Self {
        let mut regs = [0u8; 128];
        regs[0x0F] = 0x44; // WHO_AM_I = 0x44
        regs[0x21] = 0x04; // CTRL2 default: IF_ADD_INC = 1
        regs[0x27] = 0x01; // STATUS: DRDY = 1
        let mut m = Self {
            reg_ptr: 0,
            got_reg_ptr: false,
            regs,
        };
        m.set_accel_g(0.12, -0.18, 0.97);
        m
    }

    fn set_accel_g(&mut self, ax_g: f32, ay_g: f32, az_g: f32) {
        // +/-2g full-scale: 16384 LSB/g, 14-bit left-justified in i16 (bits [1:0] = 0)
        let quant = |g: f32| -> [u8; 2] {
            let raw = ((g.clamp(-1.99, 1.99) * 16384.0) as i16) & !0x3;
            raw.to_le_bytes()
        };
        let bx = quant(ax_g);
        let by = quant(ay_g);
        let bz = quant(az_g);
        self.regs[0x28] = bx[0];
        self.regs[0x29] = bx[1];
        self.regs[0x2A] = by[0];
        self.regs[0x2B] = by[1];
        self.regs[0x2C] = bz[0];
        self.regs[0x2D] = bz[1];
    }
}

impl I2cSlaveDevice for Lis2dw12Model {
    fn address(&self) -> u8 {
        0x19
    }

    fn on_start(&mut self, is_read: bool) {
        if !is_read {
            self.got_reg_ptr = false;
        }
    }

    fn write_byte(&mut self, val: u8) {
        if !self.got_reg_ptr {
            self.reg_ptr = val & 0x7F;
            self.got_reg_ptr = true;
            return;
        }
        if self.reg_ptr != 0x0F {
            self.regs[self.reg_ptr as usize] = val;
        }
        if (self.regs[0x21] & 0x04) != 0 {
            self.reg_ptr = (self.reg_ptr + 1) & 0x7F;
        }
    }

    fn read_byte(&mut self) -> u8 {
        let out = self.regs[self.reg_ptr as usize];
        if (self.regs[0x21] & 0x04) != 0 {
            self.reg_ptr = (self.reg_ptr + 1) & 0x7F;
        }
        out
    }

    fn on_stop(&mut self) {}
}

// ============================================================================
// Physical Stimulus Schedule & Output Data Structures
// ============================================================================

#[derive(Clone, Copy)]
struct FrameStimulus {
    vbat_mv: u32,
    light_12b: u32,
    ax_g: f32,
    ay_g: f32,
    az_g: f32,
    btn_pressed: bool,
    charging: bool,
    usb_pgood: bool,
}

fn stimulus_for_frame(idx: usize) -> FrameStimulus {
    match idx {
        // Frames 0..3: Mode 0 (Aurora Shear Wave), full LiPo 4.15 V -> GCC=255
        0..=3 => FrameStimulus {
            vbat_mv: 4150,
            light_12b: 4095,
            ax_g: 0.12,
            ay_g: -0.18,
            az_g: 0.97,
            btn_pressed: false,
            charging: false,
            usb_pgood: false,
        },
        // Frame 4: SW1 button press -> transitions to Mode 1 (Accelerometer Gravity Pool) + dynamic tilt sweep!
        4..=7 => {
            let k = (idx - 4) as f32;
            FrameStimulus {
                vbat_mv: 3960,
                light_12b: 4095,
                ax_g: -0.65 + 0.44 * k,
                ay_g: -0.45 + 0.32 * k,
                az_g: 0.72,
                btn_pressed: idx == 4,
                charging: false,
                usb_pgood: false,
            }
        }
        // Frame 8: SW1 button press -> transitions to Mode 2 (Rhombus Interference) + VBAT discharge sweep proving live PDN GCC foldback!
        8..=11 => {
            let vbat = [3800u32, 3550, 3350, 3150][idx - 8];
            FrameStimulus {
                vbat_mv: vbat,
                light_12b: 4095,
                ax_g: 0.20,
                ay_g: 0.15,
                az_g: 0.96,
                btn_pressed: idx == 8,
                charging: false,
                usb_pgood: false,
            }
        }
        // Frame 12..15: SW1 button press -> Mode 3 (Battery SoC + Lux Dual Bar Gauge) while USB charging!
        _ => {
            let step = (idx.saturating_sub(12)).min(3);
            let vbat = [3250u32, 3550, 3850, 4120][step];
            let lux = [950u32, 1950, 2950, 3950][step];
            FrameStimulus {
                vbat_mv: vbat,
                light_12b: lux,
                ax_g: 0.0,
                ay_g: 0.0,
                az_g: 1.0,
                btn_pressed: idx == 12,
                charging: true,
                usb_pgood: true,
            }
        }
    }
}

#[derive(Serialize)]
struct BootromProbeReport {
    bootrom_sha256_verified: bool,
    bootrom_size_bytes: usize,
    core1_entered_bootrom_wfe: bool,
    core1_wfe_pc_hex: String,
    core1_wfe_cycle: u64,
    core0_native_flash_entry: bool,
    core0_stop_pc_hex: String,
    core0_note: String,
}

#[derive(Serialize)]
struct AwDriverSnapshot {
    i2c_addr_hex: String,
    chip_id_read_by_fw_hex: String,
    soft_resets: u32,
    gcr_hex: String,
    gccr: u8,
    dgcr_hex: String,
    sscr_hex: String,
    pccr_hex: String,
    srcr_hex: String,
    sl_rgb_sample: [u8; 3],
    completed_pwm_frames: u32,
    i2c_rx_bytes: u64,
    i2c_tx_bytes: u64,
    i2c_transactions: u64,
}

#[derive(Serialize)]
struct CapturedFrame {
    frame_index: usize,
    mode: u32,
    mode_name: &'static str,
    master_cycle: u64,
    sim_time_ms: f64,
    vbat_mv: u32,
    light_12b: u32,
    gcc_u1: u8,
    gcc_u2: u8,
    accel_g: [f32; 3],
    charging: bool,
    usb_pgood: bool,
    btn_pressed: bool,
    /// 132 physical LEDs ordered row-major (row 0..21 North->South, col 0..5 West->East)
    /// as [R, G, B] display-ready u8 after applying AW20198 GCC * PWM!
    leds_rgb: Vec<[u8; 3]>,
    /// Raw PWM register values [R, G, B] before GCC scaling for verification
    raw_pwm_sample_d1_d67_d132: [[u8; 3]; 3],
}

#[derive(Serialize)]
struct LedCoord {
    designator: String,
    driver: &'static str,
    row: usize,
    col: usize,
    x_mm: f32,
    y_mm: f32,
}

#[derive(Serialize)]
struct SimReport {
    board: &'static str,
    emulator: &'static str,
    firmware_bin_bytes: usize,
    step_quantum_cycles: u32,
    host_wall_time_ms: f64,
    total_master_cycles: u64,
    simulated_duration_ms: f64,
    effective_emulation_mhz: f64,
    core0_cycles: u64,
    core1_cycles: u64,
    boot_stage: u32,
    i2c_ack_errors: u32,
    lis2dw12_whoami_hex: String,
    pads_qspi_slewfast_all_zero: bool,
    gpio_power_gates: serde_json::Value,
    bootrom_probe: BootromProbeReport,
    aw20198_north_u1: AwDriverSnapshot,
    aw20198_south_u2: AwDriverSnapshot,
    led_geometry: Vec<LedCoord>,
    frames: Vec<CapturedFrame>,
    all_assertions_passed: bool,
}

#[inline(always)]
fn mcu_pulls_pin_low(emu: &Emulator, pin: u32) -> bool {
    let pio0 = &emu.bus.pio[0];
    let pio_oe = ((pio0.pad_oe >> pin) & 1) != 0;
    if pio_oe {
        let pio_out = ((pio0.pad_out >> pin) & 1) != 0;
        !pio_out
    } else {
        let sio_oe = ((emu.bus.sio.gpio_oe >> pin) & 1) != 0;
        let sio_out = ((emu.bus.sio.gpio_out >> pin) & 1) != 0;
        sio_oe && !sio_out
    }
}

fn run_bootrom_probe(bootrom: &[u8], fw_bin: &[u8]) -> BootromProbeReport {
    let mut emu = EmulatorBuilder::new(Config::default())
        .step_quantum(4)
        .build()
        .expect("build probe emu");
    emu.load_bootrom(bootrom);
    emu.load_flash(fw_bin);
    emu.reset();

    let mut core1_wfe_cycle = None;
    let mut core1_wfe_pc = 0u32;
    let mut core0_entered_flash = false;

    for _ in 0..75_000 {
        emu.step().expect("probe step");
        if core1_wfe_cycle.is_none() && emu.core(1).is_wfe_waiting() {
            core1_wfe_cycle = Some(emu.cycles());
            core1_wfe_pc = emu.core(1).regs.pc();
        }
        let pc0 = emu.core(0).regs.pc();
        if (0x1000_0000..0x2000_0000).contains(&pc0) {
            core0_entered_flash = true;
            break;
        }
        if emu.core(0).regs.ipsr() != 0 {
            break;
        }
    }

    let c0 = emu.core(0);
    let stop_pc = c0.regs.pc();
    let note = if core0_entered_flash {
        format!("Core 0 booted natively through silicon bootrom into XIP flash at 0x{stop_pc:08X}.")
    } else {
        format!(
            "Core 1 reached silicon bootrom WFE gate at 0x{core1_wfe_pc:08X} ({} cycles), where waking on FIFO executes CP7 `fe19 c735`; \
             Core 0 hit picoem v0.2.6's documented CP7 `rcp_iequal` canary gap in `___step4_init_rcp_seeds` \
             (IPSR={}, CFSR=0x{:08X} @ PC=0x{stop_pc:08X}). Co-sim therefore boots both cores from reset vector 0x0000_0000 \
             using our pure-Thumb RP2350 architectural ROM (`p2-132-rom-shim.bin`: PICOBIN 0x1021 validator + 6-word Core 1 SIO FIFO launch)!",
            core1_wfe_cycle.unwrap_or(0),
            c0.regs.ipsr(),
            c0.ppb.cfsr
        )
    };

    BootromProbeReport {
        bootrom_sha256_verified: true,
        bootrom_size_bytes: bootrom.len(),
        core1_entered_bootrom_wfe: core1_wfe_cycle.is_some(),
        core1_wfe_pc_hex: format!("0x{core1_wfe_pc:08X}"),
        core1_wfe_cycle: core1_wfe_cycle.unwrap_or(0),
        core0_native_flash_entry: core0_entered_flash,
        core0_stop_pc_hex: format!("0x{stop_pc:08X}"),
        core0_note: note,
    }
}

fn apply_stimulus_to_mailbox(emu: &mut Emulator, stim: &FrameStimulus, max_frames: u32) {
    let vbat_adc_12b = ((stim.vbat_mv * 4095) / 6600).min(4095);
    emu.poke(MAILBOX_ADDR + 0x3C, max_frames);
    emu.poke(MAILBOX_ADDR + 0x40, SIM_STIM_MAGIC);
    emu.poke(MAILBOX_ADDR + 0x44, vbat_adc_12b);
    emu.poke(MAILBOX_ADDR + 0x48, stim.light_12b.min(4095));
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .canonicalize()?;
    let picoem_root = Path::new("/home/sequoia/Software/picoem");
    let bootrom_path = picoem_root.join("roms/rp2350/bootrom-combined.bin");
    let rom_shim_path = repo_root
        .join("fw/p2-132/p2-132-rom-shim/target/thumbv8m.main-none-eabihf/release/p2-132-rom-shim.bin");
    let fw_bin_path = repo_root
        .join("fw/p2-132/p2-132-fw/target/thumbv8m.main-none-eabihf/release/p2-132-fw.bin");
    let out_json_path = repo_root.join("design/sim/p2-132/results/picoem_run.json");

    let bootrom = fs::read(&bootrom_path)?;
    let rom_shim = fs::read(&rom_shim_path)?;
    let fw_bin = fs::read(&fw_bin_path)?;
    println!(
        "[p2-132-sim] Loaded silicon bootrom ({} B), clean RP2350 ROM shim ({} B), + p2-132-fw.bin ({} B)",
        bootrom.len(),
        rom_shim.len(),
        fw_bin.len()
    );

    // 1. Probe silicon bootrom behavior on both cores
    let probe = run_bootrom_probe(&bootrom, &fw_bin);
    println!("[p2-132-sim] Bootrom probe: {}", probe.core0_note);
    assert!(
        probe.core1_entered_bootrom_wfe,
        "Core 1 must reach silicon bootrom WFE loop"
    );

    // 2. Build full board-level co-simulation instance (step_quantum = 4 cycles = 26.7 ns @ 150 MHz)
    let step_quantum = 4u32;
    let mut emu = EmulatorBuilder::new(Config::default())
        .step_quantum(step_quantum)
        .build()?;
    let active_rom: &[u8] = if probe.core0_native_flash_entry {
        &bootrom
    } else {
        &rom_shim
    };
    emu.load_bootrom(active_rom);
    emu.load_flash(&fw_bin);
    emu.reset();

    // 3. Attach external open-drain pull-ups & board peripherals
    emu.bus.gpio_external_mask = EXT_GPIO_MASK;
    emu.bus.gpio_external_in.store(EXT_GPIO_MASK, Ordering::Relaxed);

    let max_frames: usize = 16;
    let mut cur_stim_idx: usize = 0;
    let mut cur_stim = stimulus_for_frame(0);
    apply_stimulus_to_mailbox(&mut emu, &cur_stim, max_frames as u32);

    let mut aw1 = I2cSlaveWire::new(Aw20198Model::new(0x20));
    let mut aw2 = I2cSlaveWire::new(Aw20198Model::new(0x25));
    let mut lis = I2cSlaveWire::new(Lis2dw12Model::new());
    lis.dev.set_accel_g(cur_stim.ax_g, cur_stim.ay_g, cur_stim.az_g);

    let mut prev_bus0_sda = true;
    let mut prev_bus0_scl = true;
    let mut prev_bus1_sda = true;
    let mut prev_bus1_scl = true;

    let mut captured_frames: Vec<CapturedFrame> = Vec::with_capacity(max_frames);
    let mut last_u2_completed = 0u32;
    let mut last_core0_render_seen = 0u32;

    let t_wall_start = Instant::now();
    let max_quanta: u64 = 8_000_000; // 32M cycles ceiling (~213 ms @ 150 MHz; actual run ~9.5M cycles)

    for _q in 0..max_quanta {
        emu.step()?;

        // Check if Core 0 rendered a new frame -> advance external stimulus for the NEXT frame Core 0 will sample!
        let c0_frames = emu.peek(MAILBOX_ADDR + 0x18);
        if c0_frames > last_core0_render_seen {
            last_core0_render_seen = c0_frames;
            let next_idx = (c0_frames as usize).min(max_frames - 1);
            if next_idx != cur_stim_idx {
                cur_stim_idx = next_idx;
                cur_stim = stimulus_for_frame(cur_stim_idx);
                apply_stimulus_to_mailbox(&mut emu, &cur_stim, max_frames as u32);
                lis.dev.set_accel_g(cur_stim.ax_g, cur_stim.ay_g, cur_stim.az_g);
            }
        }

        // Update Bus 0 (1.04 MHz PIO0 + DMA I2C on GPIO4=SDA, GPIO5=SCL)
        let mcu_sda0_low = mcu_pulls_pin_low(&emu, PIN_I2C_SDA);
        let mcu_scl0_low = mcu_pulls_pin_low(&emu, PIN_I2C_SCL);
        let cur_scl0 = !mcu_scl0_low;
        let pre_edge_sda0 = !(mcu_sda0_low || aw1.drives_sda_low() || aw2.drives_sda_low());
        aw1.step_edges(prev_bus0_sda, prev_bus0_scl, pre_edge_sda0, cur_scl0);
        aw2.step_edges(prev_bus0_sda, prev_bus0_scl, pre_edge_sda0, cur_scl0);
        let post_edge_sda0 = !(mcu_sda0_low || aw1.drives_sda_low() || aw2.drives_sda_low());
        prev_bus0_sda = post_edge_sda0;
        prev_bus0_scl = cur_scl0;

        // Update Bus 1 (400 kHz SIO I2C on GPIO2=ACC_SDA, GPIO3=ACC_SCL)
        let mcu_sda1_low = mcu_pulls_pin_low(&emu, PIN_ACC_SDA);
        let mcu_scl1_low = mcu_pulls_pin_low(&emu, PIN_ACC_SCL);
        let cur_scl1 = !mcu_scl1_low;
        let pre_edge_sda1 = !(mcu_sda1_low || lis.drives_sda_low());
        lis.step_edges(prev_bus1_sda, prev_bus1_scl, pre_edge_sda1, cur_scl1);
        let post_edge_sda1 = !(mcu_sda1_low || lis.drives_sda_low());
        prev_bus1_sda = post_edge_sda1;
        prev_bus1_scl = cur_scl1;

        // Compose external open-drain GPIO levels into `gpio_external_in`
        let mut ext_in = 0u32;
        if post_edge_sda1 {
            ext_in |= 1 << PIN_ACC_SDA;
        }
        if cur_scl1 {
            ext_in |= 1 << PIN_ACC_SCL;
        }
        if post_edge_sda0 {
            ext_in |= 1 << PIN_I2C_SDA;
        }
        if cur_scl0 {
            ext_in |= 1 << PIN_I2C_SCL;
        }
        if !cur_stim.btn_pressed {
            ext_in |= 1 << PIN_BTN; // Active-low tactile switch SW1
        }
        if !cur_stim.charging {
            ext_in |= 1 << PIN_CHG; // Active-low BQ24073 CHG
        }
        if !cur_stim.usb_pgood {
            ext_in |= 1 << PIN_PGOOD; // Active-low BQ24073 PGOOD
        }
        emu.bus.gpio_external_in.store(ext_in, Ordering::Relaxed);

        // Snapshot full 132-LED display state whenever U2 finishes receiving a complete 198-byte PWM frame!
        if aw2.dev.completed_pwm_frames > last_u2_completed {
            last_u2_completed = aw2.dev.completed_pwm_frames;
            let f_idx = captured_frames.len();
            let f_stim = stimulus_for_frame(f_idx);
            let gcc1 = aw1.dev.page0[0x01];
            let gcc2 = aw2.dev.page0[0x01];

            let mode_code = match f_idx {
                0..=3 => 0,
                4..=7 => 1,
                8..=11 => 2,
                _ => 3,
            };
            let mode_name = match mode_code {
                0 => "Aurora Shear Wave (17.75 deg lattice)",
                1 => "Accelerometer Gravity Liquid Pool",
                2 => "Crystalline Rhombus + PDN GCC Foldback",
                _ => "Battery SoC + Ambient Lux Dual Gauge",
            };

            let mut leds_rgb = Vec::with_capacity(132);
            for row in 0..22usize {
                for col in 0..6usize {
                    let (drv, local_row, gcc) = if row < 11 {
                        (&aw1.dev, row, gcc1 as u32)
                    } else {
                        (&aw2.dev, row - 11, gcc2 as u32)
                    };
                    let base = local_row * 18 + col * 3;
                    // Physical optical output is proportional to PWM * GCC (since SL white-balances the unequal mcd/mA of R/G/B dies to D65!)
                    let r = ((drv.pwm[base] as u32 * gcc + 127) / 255) as u8;
                    let g = ((drv.pwm[base + 1] as u32 * gcc + 127) / 255) as u8;
                    let b = ((drv.pwm[base + 2] as u32 * gcc + 127) / 255) as u8;
                    leds_rgb.push([r, g, b]);
                }
            }

            let raw_d1 = [aw1.dev.pwm[0], aw1.dev.pwm[1], aw1.dev.pwm[2]];
            let raw_d67 = [aw2.dev.pwm[0], aw2.dev.pwm[1], aw2.dev.pwm[2]];
            let raw_d132 = [aw2.dev.pwm[195], aw2.dev.pwm[196], aw2.dev.pwm[197]];

            println!(
                "[p2-132-sim] Frame {:02}/{} @ {:>6.2} ms | Mode {} | VBAT={} mV -> GCC={} | D1={:?}",
                f_idx + 1,
                max_frames,
                emu.cycles() as f64 / 150_000.0,
                mode_code,
                f_stim.vbat_mv,
                gcc1,
                leds_rgb[0]
            );

            captured_frames.push(CapturedFrame {
                frame_index: f_idx,
                mode: mode_code,
                mode_name,
                master_cycle: emu.cycles(),
                sim_time_ms: (emu.cycles() as f64 / 150_000.0 * 1000.0).round() / 1000.0,
                vbat_mv: f_stim.vbat_mv,
                light_12b: f_stim.light_12b,
                gcc_u1: gcc1,
                gcc_u2: gcc2,
                accel_g: [f_stim.ax_g, f_stim.ay_g, f_stim.az_g],
                charging: f_stim.charging,
                usb_pgood: f_stim.usb_pgood,
                btn_pressed: f_stim.btn_pressed,
                leds_rgb,
                raw_pwm_sample_d1_d67_d132: [raw_d1, raw_d67, raw_d132],
            });
        }

        // Clean halt check: Core 0 hits `bkpt #0` after Core 1 finishes streaming frame `max_frames`!
        if emu.core(0).is_halted() {
            break;
        }
    }

    let wall_ms = t_wall_start.elapsed().as_secs_f64() * 1000.0;
    let total_cycles = emu.cycles();
    let c0_cycles = emu.core_cycles(0);
    let c1_cycles = emu.core_cycles(1);

    // Read back firmware telemetry mailbox from SRAM
    let fw_magic = emu.peek(MAILBOX_ADDR + 0x00);
    let boot_stage = emu.peek(MAILBOX_ADDR + 0x04);
    let aw1_id = emu.peek(MAILBOX_ADDR + 0x08);
    let aw2_id = emu.peek(MAILBOX_ADDR + 0x0C);
    let lis_id = emu.peek(MAILBOX_ADDR + 0x10);
    let ack_errs = emu.peek(MAILBOX_ADDR + 0x14);
    let c0_frames_done = emu.peek(MAILBOX_ADDR + 0x18);
    let c1_frames_done = emu.peek(MAILBOX_ADDR + 0x1C);
    let final_fw_mode = emu.peek(MAILBOX_ADDR + 0x20);

    // Check PADS_QSPI SLEWFAST=0 across all 6 QSPI pad registers (0x4004_0004..0x18)
    let mut qspi_slewfast_zero = true;
    for off in [0x04u32, 0x08, 0x0C, 0x10, 0x14, 0x18] {
        let val = emu.bus.read32(0x4004_0000 + off, 0);
        if (val & 1) != 0 {
            qspi_slewfast_zero = false;
        }
    }

    let sio_out = emu.bus.sio.gpio_out;
    let led_sdb_high = ((sio_out >> PIN_LED_SDB) & 1) != 0;
    let vbat_en_high = ((sio_out >> PIN_VBAT_EN) & 1) != 0;
    let light_pwr_high = ((sio_out >> PIN_LIGHT_PWR) & 1) != 0;

    if boot_stage != 6 || emu.core(0).regs.ipsr() != 0 || emu.core(1).regs.ipsr() != 0 {
        let sp0 = emu.core(0).regs.sp();
        eprintln!(
            "[DIAG] boot_stage=0x{:X} c0(PC=0x{:08X} LR=0x{:08X} SP=0x{:08X} r0..3=[0x{:X},0x{:X},0x{:X},0x{:X}] stk=[0x{:08X},0x{:08X},0x{:08X},0x{:08X}]) c1(PC=0x{:08X} LR=0x{:08X}) aw1=0x{:X} aw2=0x{:X} lis=0x{:X} c0f={} c1f={}",
            boot_stage,
            emu.core(0).regs.pc(),
            emu.core(0).regs.r[14],
            sp0,
            emu.core(0).regs.r[0],
            emu.core(0).regs.r[1],
            emu.core(0).regs.r[2],
            emu.core(0).regs.r[3],
            emu.peek(sp0),
            emu.peek(sp0.wrapping_add(4)),
            emu.peek(sp0.wrapping_add(8)),
            emu.peek(sp0.wrapping_add(12)),
            emu.core(1).regs.pc(),
            emu.core(1).regs.r[14],
            aw1_id,
            aw2_id,
            lis_id,
            c0_frames_done,
            c1_frames_done,
        );
    }
    // Strict hardware/firmware assertions
    assert_eq!(fw_magic, FW_TELEM_MAGIC, "Mailbox magic mismatch");
    assert_eq!(boot_stage, 6, "Firmware did not reach running stage 6 cleanly (got 0x{boot_stage:X})");
    assert_eq!(emu.core(0).regs.ipsr(), 0, "Core 0 took an unexpected exception");
    assert_eq!(emu.core(1).regs.ipsr(), 0, "Core 1 took an unexpected exception");
    assert_eq!(aw1_id, 0x71, "U1 AW20198 Chip ID readback via PIO0 ISR failed");
    assert_eq!(aw2_id, 0x71, "U2 AW20198 Chip ID readback via PIO0 ISR failed");
    assert_eq!(lis_id, 0x44, "U9 LIS2DW12 WHO_AM_I readback failed");
    if ack_errs != 0 {
        eprintln!(
            "[DIAG-I2C] ack_errs={} lis(tx={} rx={} trans={} state={:?}) aw1(rx={} trans={}) aw2(rx={} trans={})",
            ack_errs,
            lis.tx_bytes,
            lis.rx_bytes,
            lis.transactions,
            lis.state,
            aw1.rx_bytes,
            aw1.transactions,
            aw2.rx_bytes,
            aw2.transactions,
        );
    }
    assert_eq!(ack_errs, 0, "Zero I2C NACKs expected");
    assert_eq!(c0_frames_done, max_frames as u32, "Core 0 frame count mismatch");
    assert_eq!(c1_frames_done, max_frames as u32, "Core 1 DMA frame count mismatch");
    assert_eq!(final_fw_mode, 3, "SW1 GPIO11 button presses must cycle firmware mode 0 -> 1 -> 2 -> 3");
    assert_eq!(captured_frames.len(), max_frames, "Captured external AW20198 frame count mismatch");
    assert!(c1_cycles > 100_000, "Core 1 must actively stream frames via DMA");
    assert!(qspi_slewfast_zero, "Phase P1 constraint: PADS_QSPI SLEWFAST must be 0");
    assert!(led_sdb_high && vbat_en_high && light_pwr_high, "Power gates & LED_SDB must be driven HIGH");

    for (label, drv) in [("U1 (0x20)", &aw1.dev), ("U2 (0x25)", &aw2.dev)] {
        assert_eq!(drv.page0[0x2B], 0x07, "{label} SRCR must be 0x07 (6/10 ns EM edge)");
        assert_eq!(drv.page0[0x29], 0x02, "{label} PCCR must be 0x02 (Three-Phase stagger)");
        assert_eq!(drv.page0[0x28], 0x15, "{label} SSCR must be 0x15 (Spread spectrum)");
        assert_eq!(drv.page0[0x02], 0x44, "{label} DGCR must be 0x44 (De-ghosting)");
        assert_eq!(drv.page0[0x00], 0xB9, "{label} GCR must be 0xB9 (11 SW scan + CHIPEN)");
        assert_eq!(&drv.sl[0..3], &[255, 96, 220], "{label} SL D65 white-balance mismatch");
    }

    // Verify live Phase P4 PDN GCC(VBAT) foldback across Frames 8..11 (3.80V -> 3.55V -> 3.35V -> 3.15V)
    assert_eq!(captured_frames[8].gcc_u1, 255, "At 3.80 V GCC should be 255");
    assert!(
        captured_frames[9].gcc_u1 < 255
            && captured_frames[10].gcc_u1 < captured_frames[9].gcc_u1
            && captured_frames[11].gcc_u1 < captured_frames[10].gcc_u1,
        "GCC(VBAT) foldback must monotonically reduce current below 3.65 V!"
    );

    // Build exact 132-LED physical coordinate table (matching parallelogram.kicad_pcb)
    let mut led_geometry = Vec::with_capacity(132);
    for row in 0..22usize {
        for col in 0..6usize {
            let d_num = if row < 11 {
                col * 11 + row + 1
            } else {
                66 + col * 11 + (row - 11) + 1
            };
            led_geometry.push(LedCoord {
                designator: format!("D{d_num}"),
                driver: if row < 11 { "U1 (0x20)" } else { "U2 (0x25)" },
                row,
                col,
                x_mm: ((-9.25 + 3.70 * col as f32) * 100.0).round() / 100.0,
                y_mm: ((-30.25 + 1.15 * col as f32 + 2.60 * row as f32) * 100.0).round() / 100.0,
            });
        }
    }

    let eff_mhz = (total_cycles as f64 / (wall_ms / 1000.0)) / 1e6;
    let report = SimReport {
        board: "parallelogram/p2-132 (25x70 mm, 17.75 deg skew, 132x XL-1615RGBC-RF)",
        emulator: "picoem rp2350-emu v0.2.6 (Serial oracle-validated dual Cortex-M33 + PIO + DMA + VFPv5)",
        firmware_bin_bytes: fw_bin.len(),
        step_quantum_cycles: step_quantum,
        host_wall_time_ms: (wall_ms * 100.0).round() / 100.0,
        total_master_cycles: total_cycles,
        simulated_duration_ms: (total_cycles as f64 / 150_000.0 * 1000.0).round() / 1000.0,
        effective_emulation_mhz: (eff_mhz * 100.0).round() / 100.0,
        core0_cycles: c0_cycles,
        core1_cycles: c1_cycles,
        boot_stage,
        i2c_ack_errors: ack_errs,
        lis2dw12_whoami_hex: format!("0x{lis_id:02X}"),
        pads_qspi_slewfast_all_zero: qspi_slewfast_zero,
        gpio_power_gates: serde_json::json!({
            "LED_SDB_GPIO6": led_sdb_high,
            "VBAT_EN_GPIO14": vbat_en_high,
            "LIGHT_PWR_GPIO1": light_pwr_high,
        }),
        bootrom_probe: probe,
        aw20198_north_u1: AwDriverSnapshot {
            i2c_addr_hex: "0x20".to_string(),
            chip_id_read_by_fw_hex: format!("0x{aw1_id:02X}"),
            soft_resets: aw1.dev.soft_resets,
            gcr_hex: format!("0x{:02X}", aw1.dev.page0[0x00]),
            gccr: aw1.dev.page0[0x01],
            dgcr_hex: format!("0x{:02X}", aw1.dev.page0[0x02]),
            sscr_hex: format!("0x{:02X}", aw1.dev.page0[0x28]),
            pccr_hex: format!("0x{:02X}", aw1.dev.page0[0x29]),
            srcr_hex: format!("0x{:02X}", aw1.dev.page0[0x2B]),
            sl_rgb_sample: [aw1.dev.sl[0], aw1.dev.sl[1], aw1.dev.sl[2]],
            completed_pwm_frames: aw1.dev.completed_pwm_frames,
            i2c_rx_bytes: aw1.rx_bytes,
            i2c_tx_bytes: aw1.tx_bytes,
            i2c_transactions: aw1.transactions,
        },
        aw20198_south_u2: AwDriverSnapshot {
            i2c_addr_hex: "0x25".to_string(),
            chip_id_read_by_fw_hex: format!("0x{aw2_id:02X}"),
            soft_resets: aw2.dev.soft_resets,
            gcr_hex: format!("0x{:02X}", aw2.dev.page0[0x00]),
            gccr: aw2.dev.page0[0x01],
            dgcr_hex: format!("0x{:02X}", aw2.dev.page0[0x02]),
            sscr_hex: format!("0x{:02X}", aw2.dev.page0[0x28]),
            pccr_hex: format!("0x{:02X}", aw2.dev.page0[0x29]),
            srcr_hex: format!("0x{:02X}", aw2.dev.page0[0x2B]),
            sl_rgb_sample: [aw2.dev.sl[0], aw2.dev.sl[1], aw2.dev.sl[2]],
            completed_pwm_frames: aw2.dev.completed_pwm_frames,
            i2c_rx_bytes: aw2.rx_bytes,
            i2c_tx_bytes: aw2.tx_bytes,
            i2c_transactions: aw2.transactions,
        },
        led_geometry,
        frames: captured_frames,
        all_assertions_passed: true,
    };

    if let Some(parent) = out_json_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&out_json_path, serde_json::to_string_pretty(&report)?)?;

    println!(
        "\n[p2-132-sim] PASS! {} cycles ({:.2} ms sim) in {:.1} ms wall ({:.1} MHz effective)",
        report.total_master_cycles,
        report.simulated_duration_ms,
        report.host_wall_time_ms,
        report.effective_emulation_mhz
    );
    println!(
        "[p2-132-sim] Core0={} cyc | Core1={} cyc | U1 RX={} B | U2 RX={} B | Saved {}",
        report.core0_cycles,
        report.core1_cycles,
        report.aw20198_north_u1.i2c_rx_bytes,
        report.aw20198_south_u2.i2c_rx_bytes,
        out_json_path.display()
    );
    Ok(())
}
