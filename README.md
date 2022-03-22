# 256M ROM Builder (by Lesserkuma)

A tool for compiling a multi-game ROM compilation that can be written to X-in-1 Game Boy reproduction cartridges.

The binary for Windows is available in the [Releases](https://github.com/lesserkuma/256M_ROM_Builder/releases) section.

## Usage

Place your ROM files into the `roms` directory. The game title that is displayed in the menu will be read from the ROM headers. If you want to manually name the games for the menu, use this filename format: `#000 Name.gb`. If you want to manually disable SRAM access for a ROM, add another `#` character after the name, e.g. `#008 Mario Land 2#.gb`. If you also put save data files (.sav) into the `roms` directory, a full 512 KB .sav file will also be generated for the cartridge.

The default output filename contains a unique ROM code. This is to make it easier to keep save data backups and their compilation ROMs together without confusion.

### Command Line Arguments

No command line arguments are required for creating a compilation, however there are some optional ones that can tweak some things:

```
--title "TITLE"            sets a custom menu title
--split                    splits output files into 8 MB parts
--toc {index,offset,hide}  changes the order of the table of contents (default: index)
--no-wait                  don’t wait for user input when finished
--no-log                   don’t write a log file
--export                   export individual SRAM files and ROM files from an existing compilation
--import-sram              import individual SRAM files into a 512 KB SRAM compilation file
```

#### How to
- Export ROMs and save data files from an existing compilation
  - With both `256MROMSET_xxxx.gbc` and the 512 KB `256MROMSET_xxxx.sav` file in one directory, run `256m_rom_builder --export 256MROMSET_xxxx.gbc`. This will create a new directory called `256MROMSET_xxxx` with all the individual ROMs and save data files.

- Import individual save data files into an existing compilation
  - With both `256MROMSET_xxxx.gbc` and the 512 KB `256MROMSET_xxxx.sav` file in one directory, run `256m_rom_builder --import-sram 256MROMSET_xxxx.gbc`. This will read all save data files from the directory called `256MROMSET_xxxx` and combine them back into the full compilation 512 KB save data file.


### Limitations
- up to 108 ROMs total
- up to 16 ROMs that use SRAM
- up to 32 MB combined file size (since ROMs need to be aligned in a very specific way, there may be less usable space)

## Compatibility
Tested repro cartridges:
- SD008-6810-512S with MSP55LV512
- SD008-6810-V4 with MX29GL256EL
- SD008-6810-V5 with MX29CL256FH

ROM and save data can be written and read using a [GBxCart RW v1.4+](https://www.gbxcart.com/) device by insideGadgets and the [FlashGBX](https://github.com/lesserkuma/FlashGBX) software.

## Screenshots

<img src="https://raw.githubusercontent.com/lesserkuma/256M_ROM_Builder/master/.github/screen.png" alt="" />
