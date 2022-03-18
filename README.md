# 256M ROM Builder (by Lesserkuma)

A tool for compiling a multi-game ROM compilation that can be written to X-in-1 reproduction cartridges.

The binary for Windows is available in the [Releases](https://github.com/lesserkuma/256M_ROM_Builder/releases) section.

## Usage

Place your ROM files into the `roms` directory. The game title that is displayed in the menu will be read from the ROM headers. If you want to manually name the games for the menu, use this filename format: `#00 Name.gb`. If you want to manually disable SRAM access for a ROM, add another `#` character after the name, e.g. `#14 Mario Land 2#.gb`.

To change the menu title, call the software like so `compile.exe "Menu Title Here"`.

## Compatibility
Tested repro cartridges:
- SD008-6810-512S with MSP55LV512
- SD008-6810-V4 with MX29GL256EL
- SD008-6810-V5 with MX29CL256FH
