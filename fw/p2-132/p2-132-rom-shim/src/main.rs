#![no_std]
#![no_main]

//! Architectural RP2350 Bootrom Shim for `picoem` (`rp2350-emu v0.2.6`).
//!
//! Implements the exact RP2350 Datasheet §5.3 & §5.9.5 boot flow in pure Armv8-M Thumb
//! (avoiding the silicon bootrom's CP7 `rcp_*` canary instructions while `picoem`'s CP7
//! canary/count state follow-up is pending):
//!   - Core 0 (`SIO_CPUID == 0`): validates `PICOBIN` `IMAGE_DEF` markers (`0xFFFF_DED3`..`0xAB12_3579`
//!     and `IMAGE_TYPE_EXE` `0x1021`) in XIP flash (`0x1000_0040`), programs `SCB.VTOR = 0x1000_0000`,
//!     loads `MSP` and `Reset` from the XIP vector table, and branches into firmware!
//!   - Core 1 (`SIO_CPUID == 1`): switches to an independent boot stack and enters the standard
//!     6-word `[0, 0, 1, vtor, sp, entry]` `WFE` + `SIO_FIFO` + `SEV` multicore launch state machine!

use core::arch::{asm, naked_asm};
use core::panic::PanicInfo;
use core::ptr::{read_volatile, write_volatile};

#[repr(C)]
pub union VectorEntry {
    pub sp: u32,
    pub handler: unsafe extern "C" fn() -> !,
}

#[unsafe(link_section = ".vector_table")]
#[used]
pub static ROM_VECTORS: [VectorEntry; 16] = [
    VectorEntry { sp: 0x2008_2000 },
    VectorEntry { handler: _rom_reset },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { sp: 0 },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
    VectorEntry { sp: 0 },
    VectorEntry { handler: _rom_fault },
    VectorEntry { handler: _rom_fault },
];

#[unsafe(naked)]
#[unsafe(no_mangle)]
pub unsafe extern "C" fn _rom_reset() -> ! {
    naked_asm!(
        "movw r0, #0x0000",
        "movt r0, #0xD000",
        "ldr  r0, [r0, #0]",
        "cbz  r0, 1f",
        "movw r1, #0x0800",
        "movt r1, #0x2008",
        "msr  msp, r1",
        "b    {core1}",
        "1:",
        "b    {core0}",
        core0 = sym rom_core0_boot,
        core1 = sym rom_core1_wait_for_vector,
    );
}

unsafe extern "C" fn rom_core0_boot() -> ! {
    // Scan first 4 KB of XIP flash (0x1000_0000..0x1000_1000) for valid PICOBIN IMAGE_DEF block
    let mut found_picobin = false;
    let mut off = 0u32;
    while off < 0x1000 {
        let addr = 0x1000_0000 + off;
        let w0 = unsafe { read_volatile(addr as *const u32) };
        if w0 == 0xFFFF_DED3 {
            let w1 = unsafe { read_volatile((addr + 4) as *const u32) };
            let w4 = unsafe { read_volatile((addr + 16) as *const u32) };
            if (w1 & 0xFF) == 0x42 && ((w1 >> 16) & 0xFFFF) == 0x1021 && w4 == 0xAB12_3579 {
                found_picobin = true;
                break;
            }
        }
        off += 4;
    }
    if !found_picobin {
        unsafe { _rom_fault() };
    }

    // Boot XIP image at 0x1000_0000
    let app_sp = unsafe { read_volatile(0x1000_0000 as *const u32) };
    let app_entry = unsafe { read_volatile(0x1000_0004 as *const u32) };
    unsafe {
        write_volatile(0xE000_ED08 as *mut u32, 0x1000_0000); // SCB.VTOR
        asm!(
            "dsb sy",
            "isb sy",
            "msr msp, {0}",
            "bx  {1}",
            in(reg) app_sp,
            in(reg) app_entry,
            options(noreturn)
        );
    }
}

unsafe extern "C" fn rom_core1_wait_for_vector() -> ! {
    const SIO_FIFO_ST: *const u32 = 0xD000_0050 as *const u32;
    const SIO_FIFO_WR: *mut u32   = 0xD000_0054 as *mut u32;
    const SIO_FIFO_RD: *const u32 = 0xD000_0058 as *const u32;
    const SCB_VTOR: *mut u32      = 0xE000_ED08 as *mut u32;

    let mut state: u32 = 0;
    let mut vtor: u32 = 0;
    let mut sp: u32 = 0;

    loop {
        // Wait for word in RX FIFO (VLD = bit 0)
        while (unsafe { read_volatile(SIO_FIFO_ST) } & 1) == 0 {
            unsafe { asm!("wfe") };
        }
        let cmd = unsafe { read_volatile(SIO_FIFO_RD) };

        // Echo every received word back over TX FIFO + SEV per RP2350 bootrom protocol
        while (unsafe { read_volatile(SIO_FIFO_ST) } & 2) == 0 {}
        unsafe {
            write_volatile(SIO_FIFO_WR, cmd);
            asm!("sev");
        }

        match state {
            0 => {
                if cmd == 0 {
                    state = 1;
                }
            }
            1 => {
                if cmd == 0 {
                    // Stay in state 1 across any extra leading zeros!
                } else if cmd == 1 {
                    state = 2;
                } else {
                    state = 0;
                }
            }
            2 => {
                vtor = cmd;
                state = 3;
            }
            3 => {
                sp = cmd;
                state = 4;
            }
            _ => {
                let entry = cmd;
                unsafe {
                    write_volatile(SCB_VTOR, vtor);
                    asm!(
                        "dsb sy",
                        "isb sy",
                        "msr msp, {0}",
                        "bx  {1}",
                        in(reg) sp,
                        in(reg) entry,
                        options(noreturn)
                    );
                }
            }
        }
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn _rom_fault() -> ! {
    unsafe { asm!("bkpt #2") };
    loop {
        unsafe { asm!("wfi") };
    }
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    unsafe { _rom_fault() }
}
