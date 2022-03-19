# -*- coding: utf-8 -*-
# 256M ROM Builder
# Author: Lesserkuma (github.com/lesserkuma)

import math, glob, re, os, datetime, time, hashlib, time, sys, argparse, struct

# Configuration
app_version = "0.6"
default_menu_title = "256M COLLECTION"
default_file = "256MROMSET_<CODE>.gbc"

################################

# Menu ROM Parameters
addr_num_items = 0x4046
addr_num_pages = 0x404B
addr_menu_title = 0x4272
addr_menu_param = 0x46FA
addr_menu_text = 0x4EA0
max_roms = 108
roms_per_page = 11

# Initialization
rom_map = {}
roms = []
roms_added = 0
uses_sram = False
output = bytearray([0xFF] * 0x2000000)
output_sram = bytearray([0x00] * 0x80000)
sram_slots_used = []
sram_addr = []
for i in range(0, 0x2000000, 0x200000): sram_addr.append(i)
now = datetime.datetime.now()
log = ""
v7001_values = {0x800000:0x00, 0x400000:0x80, 0x200000:0xC0, 0x100000:0xE0, 0x80000:0xF0, 0x40000:0xF8, 0x20000:0xFC, 0x10000:0xFE, 0x8000:0xFF}
sram_sizes = [0, 0x800, 0x2000, 0x8000]
logodata = bytearray(0x30)

class ArgParseCustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter): pass
def FixChecksums(buffer):
	checksum = 0
	for i in range(0x134, 0x14D):
		checksum = checksum - buffer[i] - 1
	checksum = checksum & 0xFF
	buffer[0x14D] = checksum
	
	buffer[0x14E] = 0
	buffer[0x14F] = 0
	checksum = sum(buffer) & 0xFFFF
	buffer[0x14E] = checksum >> 8
	buffer[0x14F] = checksum & 0xFF
	return buffer

def lprint(*args, **kwargs):
	global log
	s = format(" ".join(map(str, args)))
	print("{:s}".format(s))
	log += "{:s}\n".format(s)

################################

print("")
lprint("256M ROM Builder v{:s}\nby Lesserkuma\n".format(app_version))
parser = argparse.ArgumentParser()
parser.add_argument("--title", help="sets a custom menu title", type=str.upper, default=default_menu_title)
parser.add_argument("--split", help="splits output files into 8 MB parts", action="store_true", default=False)
parser.add_argument("--toc", help="changes the order of the table of contents", choices=["index", "offset", "hide"], type=str.lower, default="index")
parser.add_argument("--no-wait", help="don’t wait for user input when finished", action="store_true", default=False)
parser.add_argument("--no-log", help="don’t write a log file", action="store_true", default=False)
parser.add_argument("--export", help="export individual SRAM files and ROM files from an existing compilation", action="store_true", default=False)
parser.add_argument("--import-sram", help="import individual SRAM files into a 512 KB SRAM compilation file", action="store_true", default=False)
parser.add_argument("file", help="sets the file name of the compilation ROM", nargs='?', default=default_file)
args = parser.parse_args()
menu_title = args.title
output_file = args.file
if output_file == "menu.bin":
	lprint("Error: The file must not be named menu.bin")
	if not args.no_wait: input("\nPress ENTER to exit.\n")
	sys.exit(1)

if args.export is False and args.import_sram is False:
	# Load Menu ROM
	if not os.path.exists("menu.bin"):
		lprint("Error: Menu ROM file not found!")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)
	with open("menu.bin", "rb") as f: menu = bytearray(f.read())
	menu_title = re.sub(r"[^A-Z0-9 ]+", "", menu_title.upper()).strip()[:16]
	if menu_title != default_menu_title:
		lprint("Setting menu title to: {:s}\n".format(menu_title))
	output[0:0x8000] = menu

	# Load Game ROMs
	files = glob.glob("./roms/*.*")
	files.sort()
	for file in files:
		info = {}
		with open(file, "rb") as f: buffer = bytearray(f.read())
		if len(buffer) > 0x800000: continue
		if (hashlib.sha1(buffer[0x104:0x134]).digest() != bytearray([ 0x07, 0x45, 0xFD, 0xEF, 0x34, 0x13, 0x2D, 0x1B, 0x3D, 0x48, 0x8C, 0xFB, 0xDF, 0x03, 0x79, 0xA3, 0x9F, 0xD5, 0x4B, 0x4C ])): continue
		
		if buffer[0x149] > 0:
			if buffer[0x149] < len(sram_sizes):
				sram_size = sram_sizes[buffer[0x149]]
			else:
				sram_size = 0x8000
		elif buffer[0x147] == 0x06: # MBC2
			sram_size = 512
		else:
			sram_size = 0
		
		buffer_sram = None
		if sram_size > 0:
			file_sram = "{:s}.sav".format(os.path.splitext(file)[0])
			if os.path.exists(file_sram):
				with open(file_sram, "rb") as f:
					buffer_sram = bytearray(f.read())
					buffer_sram = buffer_sram[:0x8000]
		
		fn = os.path.split(file)[1]
		fn = os.path.splitext(fn)[0]
		m = re.search(r'^\#[0-9]+ (.+)', fn)
		if m is not None:
			game_title = m.group(1)[:16]
			if game_title.endswith("#"):
				game_title = game_title[:-1]
				sram_size = 0
			game_title = game_title[:16]
		else:
			if buffer[0x143] in (0x00, 0x80, 0xC0):
				game_title = bytearray(buffer[0x134:0x143]).decode("ascii", "replace")
			else:
				game_title = bytearray(buffer[0x134:0x144]).decode("ascii", "replace")
		game_title = re.sub(r"[^A-Z0-9 ]+", "", game_title.upper()).strip()
		logodata = buffer[0x104:0x134]
		
		# Pad ROM to next power of 2 if trimmed
		rom_size = len(buffer)
		if ((rom_size & (rom_size - 1)) != 0):
			x = 128
			while (x < rom_size): x *= 2
			rom_size = x
			buffer = buffer + bytearray([0xFF] * (rom_size - len(buffer)))
		
		info["index"] = len(roms)
		info["filename"] = file
		info["title"] = game_title
		info["sram_size"] = sram_size
		info["size"] = len(buffer)
		info["hash"] = hashlib.sha1(buffer[0:0x200]).digest()
		buffer = FixChecksums(buffer)
		info["rom"] = buffer
		if buffer_sram is not None:
			info["sram"] = buffer_sram
		roms.append(info)

	lprint("Found {:d} ROM(s)".format(len(roms)))
	# Re-order loaded ROMs by size
	roms.sort(key=lambda item: item["size"])

	# Carefully align ROMs
	# - They must always be in a location that is divisible by their ROM size
	# - There also can only be one SRAM-enabled ROM every 0x200000 bytes
	# SRAM-enabled ROMs go first
	for rom in roms:
		if rom["sram_size"] > 0:
			sram_addr[0] = rom["size"]
			for j in range(0, len(sram_addr)):
				pos = sram_addr[j]
				sram_slot = math.floor(pos / 0x200000)
				if sram_slot in sram_slots_used: continue
				if sram_addr[j] % rom["size"] > 0: continue
				if pos not in rom_map and output[pos:pos+rom["size"]] == bytearray([0xFF] * rom["size"]):
					rom["offset"] = sram_addr[j]
					rom_map[sram_addr[j]] = rom
					output[rom["offset"]:rom["offset"]+rom["size"]] = rom["rom"]
					sram_slots_used.append(sram_slot)
					if "sram" in rom:
						output_sram[sram_slot*0x8000:sram_slot*0x8000+len(rom["sram"])] = rom["sram"]
					break
			if "offset" not in rom:
				lprint("Error: Can’t add {:s} because no SRAM slots are available or it would exceed the maximum size of the compilation".format(rom["title"]))
	lprint("\nAdded {:d} ROM(s) that use SRAM to the compilation".format(len(sram_slots_used)))
	
	# Now fill up the rest
	for rom in roms:
		if rom["sram_size"] == 0:
			pos = rom["size"]
			while True:
				if pos not in rom_map and output[pos:pos+rom["size"]] == bytearray([0xFF] * rom["size"]):
					rom["offset"] = pos
					rom_map[pos] = rom
					output[rom["offset"]:rom["offset"]+rom["size"]] = rom["rom"]
					break
				else:
					pos += rom["size"]
					if pos > 0x2000000:
						break
			if "offset" not in rom:
				lprint("Error: Can’t add {:s} (size: 0x{:X}) because it exceeds the maximum size of the compilation".format(rom["filename"], rom["size"]))
	lprint("Added {:d} ROM(s) that do not use SRAM to the compilation".format(len(rom_map) - len(sram_slots_used)))

	if len(rom_map) == 0:
		lprint("\nPlease place ROM files into the “roms” directory.")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)

	# Patch Menu ROM
	roms_added = 0
	table_lines = {}
	rom_map = dict(sorted(rom_map.items(), key=lambda item: item[1]["index"]))
	for k, v in rom_map.items():
		pos = addr_menu_text + (roms_added * 16)
		menu[pos:pos+16] = v["title"].ljust(16).encode("ascii")
		v7000 = math.floor(v["offset"] / 0x8000) & 0xFF
		v7001 = v7001_values[v["size"]]
		v7002 = math.floor(v["offset"] / 0x8000) >> 8
		x = 0x00
		if v7002 == 1: x = 0x01
		if v7002 == 2: x = 0x10
		if v7002 == 3: x = 0x11

		if v["sram_size"] > 0:
			v7002 += 0x90
			sram_id = math.floor(v["offset"] / 0x200000)
			rom_map[k]["sram_id"] = sram_id
			sram_id = "{:d}".format(sram_id)
			if "sram" in v:
				sram_id += " (imported)"
		else:
			v7002 += 0xF0
			sram_id = ""
		pos = addr_menu_param + (roms_added * 4)
		menu[pos+0] = x
		menu[pos+1] = v7002 # multirom bank
		menu[pos+2] = v7001 # rom size
		menu[pos+3] = v7000 # rom offset in current multirom bank
		if args.toc == "offset":
			table_index = v["offset"]
		else:
			table_index = v["index"]
		table_line = "{:3d} | {:16s} | 0x{:07X} | 0x{:06X} | {:02X}:{:02X}:{:02X}:{:02X} | {:4s}".format(v["index"]+1, v["title"], v["offset"], v["size"], v7000, v7001, v7002, x, sram_id)
		table_lines[table_index] = table_line
		roms_added += 1
		if roms_added >= max_roms: break
	if args.toc != "hide":
		lprint("\n    | Title            | Offset    | Size     | Parameters  | SRAM Slot    ")
		lprint("----+------------------+-----------+----------+-------------+--------------")
		table_lines = dict(sorted(table_lines.items()))
		for table_line in table_lines.values():
			lprint(table_line)
	
	# Add some metadata to menu ROM
	c = 0
	for k, v in rom_map.items():
		if not "sram_id" in v: continue
		temp = {"index":v["index"], "offset":v["offset"], "size":v["size"], "sram_size":v["sram_size"], "sram_id":v["sram_id"], "hash":v["hash"][:16]}
		keys = list(temp.keys())
		values = []
		for key in keys: values.append(temp[key])
		buffer = struct.pack("=HIIIH16s", *values)
		pos = 0x1000 + (c * 0x20)
		menu[pos:pos+0x20] = buffer
		c += 1

	menu[addr_num_items] = roms_added & 0xFF
	menu[addr_num_pages] = (math.ceil(roms_added / roms_per_page) - 1) & 0xFF
	signature = \
	"256M ROM Builder" \
	"by LK\x00\x02\x00"
	menu[0x150:0x150+len(signature)] = signature.encode("ascii")
	rom_code = "{:s}".format(hashlib.sha1(menu[0x150:0x8000]).hexdigest()[:4]).upper()
	output_file = output_file.replace("<CODE>", rom_code)
	menu[0x13F:0x13F+4] = rom_code.encode("ascii")
	created_string = "{:s}".format(now.strftime('%Y-%m-%d %H:%M:%S'))
	menu[0x168:0x168+len(created_string)] = created_string.encode("ascii")
	menu[addr_menu_title:addr_menu_title+16] = menu_title.center(16).encode("ascii")[:16]
	menu[0x104:0x134] = logodata
	output[0:len(menu)] = menu
	output = output.strip(b"\xFF")

	# Calculate next power of 2 for final ROM size
	rom_size = len(output)
	if ((rom_size & (rom_size - 1)) != 0):
		x = 128
		while (x < rom_size): x *= 2
		rom_size = x

	# Finalize ROM header
	header_size = 0
	temp = 0x8000
	while temp < 0x2000000:
		if temp >= rom_size: break
		header_size += 1
		temp = temp * 2
	output[0x148] = header_size

	# Fix checksums
	output = FixChecksums(output)

	# Pad to final ROM size
	output = output + bytearray([0xFF] * (rom_size - len(output)))
	
	# Write Output to File(s)
	(name, ext) = os.path.splitext(output_file)
	lprint("\nBuild date: {:s}\nROM code: {:s}\n".format(now.strftime('%Y-%m-%d %H:%M:%S'), rom_code))
	if args.split is True:
		for i in range(0, 4):
			pos = 0x800000 * i
			if pos >= len(output): break
			output_file = "{:s}_part{:d}{:s}".format(name, i+1, ext)
			with open(output_file, "wb") as f: f.write(output[pos:pos+0x800000])
			lprint("Compilation part {:d} saved to “{:s}”".format(i+1, output_file))
	else:
		with open(output_file, "wb") as f: f.write(output)
		lprint("Compilation ROM saved to “{:s}”".format(output_file))
		if output_sram != bytearray([0x00] * 0x80000):
			fn = os.path.splitext(output_file)[0] + ".sav"
			with open(fn, "wb") as f: f.write(output_sram)
			lprint("Compilation SRAM saved to “{:s}”".format(fn))

##############################
else: # ROM/SRAM Export/Import
	file_compilation = args.file
	fn = os.path.splitext(args.file)[0]
	dir = fn
	file_sram = "{:s}.sav".format(fn)
	compilation = None
	sram = None
	
	# Load files
	if file_compilation == default_file:
		parser.print_help()
		lprint("\nError: Compilation ROM file must be set via command line argument!")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)
	elif not os.path.exists(file_compilation):
		lprint("Error: Compilation ROM file not found!")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)
	else:
		with open(file_compilation, "rb") as f:
			compilation = bytearray(f.read())
	
	menu_version = compilation[0x14C]
	if menu_version < 1:
		lprint("Error: This Compilation ROM version is too old.")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)
	signature = compilation[0x150:0x165].decode("ascii", "ignore")
	if signature != "256M ROM Builderby LK":
		lprint("Error: Not a valid Compilation ROM. Please merge any split ROMs first.")
		if not args.no_wait: input("\nPress ENTER to exit.\n")
		sys.exit(1)
	build_date = compilation[0x168:0x17B].decode("ascii", "ignore")
	rom_code = compilation[0x13F:0x143].decode("ascii", "ignore")
	lprint("Compilation ROM loaded.")
	lprint("\nMenu Version: {:d}\nBuild date: {:s}\nROM code: {:s}".format(menu_version, build_date, rom_code))

	if os.path.exists(file_sram):
		with open(file_sram, "rb") as f:
			sram = bytearray(f.read())
		if len(sram) != 0x80000:
			lprint("Error: The compilation SRAM file must be 512 KB.")
			if not args.no_wait: input("\nPress ENTER to exit.\n")
			sys.exit(1)
	elif args.import_sram:
		sram = bytearray(0x80000)
	else:
		lprint("SRAM file not found.")
	
	c = 0
	sram_roms = []
	print("")
	for c in range(0, compilation[addr_num_items]):
		pos = addr_menu_text + (c * 16)
		data = {}
		if compilation[pos:pos+16] == bytearray([0xFF] * 16): break
		data["index"] = c
		data["title"] = compilation[pos:pos+16].decode("ascii", "ignore").strip()
		pos = addr_menu_param + (c * 4)
		x = compilation[pos+0]
		v7002 = compilation[pos+1]
		v7001 = compilation[pos+2]
		v7000 = compilation[pos+3]
		data["offset"] = (v7000 * 0x8000) + ((v7002 & 0b11) * 0x800000)
		size = [k for (k, v) in v7001_values.items() if v == v7001]
		if len(size) != 1: continue
		data["size"] = size[0]
		if (v7002 & 0xF0 >> 2) == 0x10:
			data["sram_id"] = math.floor(data["offset"] / 0x200000)
		
		no_sram = ""
		if data["offset"] >= len(compilation):
			lprint("{:s} not found inside {:s}.".format(data["title"], args.file))
			continue
		buffer = compilation[data["offset"]:data["offset"]+0x150]
		if buffer[0x149] > 0:
			if buffer[0x149] < len(sram_sizes):
				sram_size = sram_sizes[buffer[0x149]]
			else:
				sram_size = 0x8000
		elif buffer[0x147] == 0x06: # MBC2
			sram_size = 512
		else:
			sram_size = 0
		if "sram_id" in data:
			if buffer[0x143] in (0xC0, 0x80):
				ext = ".gbc"
			elif buffer[0x146] == 0x03:
				ext = ".sgb"
			else:
				ext = ".gb"
			data["sram_size"] = sram_size
			data["sram_address"] = data["sram_id"] * 0x8000
		elif sram_size > 0:
			no_sram = "#"
		
		if not os.path.exists(dir):
			if args.import_sram:
				lprint("Error: No files found for importing!\nWill now instead export files to the “{:s}” directory.\nYou can then replace the individual .sav files and run the import again.".format(dir))
				args.export = True
				args.import_sram = False
				try:
					input("\nPress ENTER to continue or Ctrl+C to cancel.\n")
				except KeyboardInterrupt:
					sys.exit(0)
			os.mkdir(dir)
		sram_file_game = "{:s}/#{:03d} {:s}.sav".format(dir, data["index"]+1, data["title"])
		rom_file_game = "{:s}/#{:03d} {:s}{:s}{:s}".format(dir, data["index"]+1, data["title"], "#" if no_sram else "", ext)
		if args.export:
			lprint("Exporting ROM #{:d} to “{:s}”".format(data["index"]+1, rom_file_game))
			with open(rom_file_game, "wb") as f: f.write(compilation[data["offset"]:data["offset"]+data["size"]])
			if sram is not None and "sram_id" in data:
				lprint("Exporting SRAM #{:d} to “{:s}”".format(data["sram_id"], sram_file_game))
				with open(sram_file_game, "wb") as f: f.write(sram[data["sram_address"]:data["sram_address"]+data["sram_size"]])
		elif args.import_sram:
			if not os.path.exists(sram_file_game): continue
			with open(sram_file_game, "rb") as f: sram_game = f.read(data["sram_size"])
			sram[data["sram_address"]:data["sram_address"]+data["sram_size"]] = sram_game
			with open(file_sram, "wb") as f: f.write(sram)
			lprint("Importing “{:s}” into SRAM #{:d}".format(sram_file_game, data["sram_id"]))

################################
if not args.no_log:
	log += "\nArgument List: {:s}\n".format(str(sys.argv[1:]))
	log += "\n################################\n\n"
	with open("log.txt", "a") as f: f.write(log)
if not args.no_wait: input("\nPress ENTER to exit.\n")
