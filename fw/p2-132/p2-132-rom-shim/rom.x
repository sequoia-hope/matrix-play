MEMORY
{
    ROM (rx) : ORIGIN = 0x00000000, LENGTH = 32K
}

SECTIONS
{
    .vector_table ORIGIN(ROM) :
    {
        KEEP(*(.vector_table))
    } > ROM

    .text : ALIGN(4)
    {
        *(.text .text.*)
        *(.rodata .rodata.*)
    } > ROM

    /DISCARD/ :
    {
        *(.ARM.exidx .ARM.exidx.* .ARM.extab .ARM.extab.* .data .data.* .bss .bss.*)
    }
}
