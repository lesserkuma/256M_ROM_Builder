# 256M ROM Builder (by Lesserkuma)

A tool for compiling a multi-game ROM compilation that can be written to X-in-1 Game Boy reproduction cartridges.

The binary for Windows is available in the [Releases](https://github.com/lesserkuma/256M_ROM_Builder/releases) section.

## Usage

Place your ROM files into the `roms` directory. The game title that is displayed in the menu will be read from the ROM headers. If you want to manually name the games for the menu, use this filename format: `#00 Name.gb`. If you want to manually disable SRAM access for a ROM, add another `#` character after the name, e.g. `#08 Mario Land 2#.gb`.

The default output filename contains a unique ROM code. This is to make it easier to assign save data backups to the correct compilation ROM.

### Parameters

No command line arguments are required, however there are some optional ones that can tweak some things:

```
--output "OUTPUT"          sets the output filename
                           (<CODE> will be replaced by a unique value)
						   (default: "256M COMPO_<CODE>.gbc")
--title "TITLE"            sets a custom menu title
                           (default: "256M COLLECTION")
--split                    splits output files into 8 MB parts
--toc-sort {index,offset}  sets what the table of contents is ordered by
                           (default: index)
--no-wait                  don’t wait for user input when finished
--write-log                write the program’s output into a text file
```

## Compatibility
Tested repro cartridges:
- SD008-6810-512S with MSP55LV512
- SD008-6810-V4 with MX29GL256EL
- SD008-6810-V5 with MX29CL256FH

## Screenshots

<img src="https://raw.githubusercontent.com/lesserkuma/256M_ROM_Builder/master/.github/screen.png" alt="" />
