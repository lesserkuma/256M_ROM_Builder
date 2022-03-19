# 256M ROM Builder (by Lesserkuma)

A tool for compiling a multi-game ROM compilation that can be written to X-in-1 Game Boy reproduction cartridges.

The binary for Windows is available in the [Releases](https://github.com/lesserkuma/256M_ROM_Builder/releases) section.

## Usage

Place your ROM files into the `roms` directory. The game title that is displayed in the menu will be read from the ROM headers. If you want to manually name the games for the menu, use this filename format: `#000 Name.gb`. If you want to manually disable SRAM access for a ROM, add another `#` character after the name, e.g. `#008 Mario Land 2#.gb`. If you also put save data files into the roms `directory`, a full 512 KB file will also be generated for the cartridge.

The default output filename contains a unique ROM code. This is to make it easier to assign save data backups to the correct compilation ROM.

### Parameters

No command line arguments are required for creating a compilation, however there are some optional ones that can tweak some things:

```
--title TITLE              sets a custom menu title
--split                    splits output files into 8 MB parts
--toc {index,offset,hide}  changes the order of the table of contents (default: index)
--no-wait                  don�t wait for user input when finished
--no-log                   don�t write a log file
--export                   export individual SRAM files and ROM files from a previous compilation
--import-sram              import individual SRAM files into full 512 KB SRAM file of the given compilation
```

## Compatibility
Tested repro cartridges:
- SD008-6810-512S with MSP55LV512
- SD008-6810-V4 with MX29GL256EL
- SD008-6810-V5 with MX29CL256FH

## Screenshots

<img src="https://raw.githubusercontent.com/lesserkuma/256M_ROM_Builder/master/.github/screen.png" alt="" />
