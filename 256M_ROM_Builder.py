import math, glob, re, os, datetime, hashlib, time, sys

# Configuration
rom_title = "256M COLLECTION"
menu_title = "256M COLLECTION"
output_file = "output.gbc"
info_table_sort = 1

################################

# Menu ROM Parameters
addr_num_items = 0x4046
addr_num_pages = 0x404B
addr_menu_title = 0x4272
addr_menu_param = 0x46FA
addr_menu_text = 0x4EA0
max_roms = 108
roms_per_page = 11

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

# Initialization
rom_map = {}
roms = []
roms_added = 0
uses_sram = False
output = bytearray([0xFF] * 0x2000000)
sram_slots_used = []
sram_addr = []
for i in range(0, 0x2000000, 0x200000): sram_addr.append(i)

print("\n256M ROM Builder v0.1\nby Lesserkuma\n")
# Load Menu ROM
if not os.path.exists("menu.gbc"):
	print("Error: Menu ROM file not found!")
	time.sleep(1)
	sys.exit(1)
with open("menu.gbc", "rb") as f: menu = bytearray(f.read())
if len(sys.argv) > 1:
	menu_title = sys.argv[1]
	menu_title = re.sub(r"[^A-Z0-9 ]+", "", menu_title.upper()).strip()[:16]
	print("Setting menu title to: {:s}\n".format(menu_title))
output[0:0x8000] = menu

# Load Game ROMs
files = glob.glob("./roms/*.*")
files.sort()
for file in files:
	info = {}
	with open(file, "rb") as f: buffer = bytearray(f.read())
	if len(buffer) > 0x800000: continue
	if (hashlib.sha1(buffer[0x104:0x134]).digest() != bytearray([ 0x07, 0x45, 0xFD, 0xEF, 0x34, 0x13, 0x2D, 0x1B, 0x3D, 0x48, 0x8C, 0xFB, 0xDF, 0x03, 0x79, 0xA3, 0x9F, 0xD5, 0x4B, 0x4C ])): continue
	
	has_sram = (buffer[0x149] > 0) or (buffer[0x147] == 0x06)
	
	fn = os.path.split(file)[1]
	fn = os.path.splitext(fn)[0]
	m = re.search(r'^\#[0-9]+ (.+)', fn)
	if m is not None:
		game_title = m.group(1)[:16]
		if game_title.endswith("#"):
			game_title = game_title[:-1]
			has_sram = False
		game_title = game_title[:16]
	else:
		if buffer[0x143] in (0x00, 0x80, 0xC0):
			game_title = bytearray(buffer[0x134:0x143]).decode("ascii", "replace")
		else:
			game_title = bytearray(buffer[0x134:0x144]).decode("ascii", "replace")
	game_title = re.sub(r"[^A-Z0-9 ]+", "", game_title.upper()).strip()
	
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
	info["has_sram"] = has_sram
	info["size"] = len(buffer)
	buffer = FixChecksums(buffer)
	info["rom"] = buffer
	roms.append(info)

print("Found {:d} ROM(s)".format(len(roms)))
# Re-order loaded ROMs by size
roms.sort(key=lambda item: item["size"])

# Carefully align ROMs
# - They must always be in a location that is divisible by their ROM size
# - There also can only be one SRAM-enabled ROM every 0x200000 bytes
# SRAM-enabled ROMs go first
for rom in roms:
	if rom["has_sram"] is True:
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
				break
		if "offset" not in rom:
			print("Error: Can’t add {:s} because no SRAM slots are available or it would exceed the maximum size of the compilation".format(rom["title"]))
print("\nAdded {:d} ROM(s) that use SRAM to the compilation".format(len(sram_slots_used)))

# Now fill up the rest
for rom in roms:
	pos = rom["size"]
	if rom["has_sram"] is False:
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
			print("Error: Can’t add {:s} (size: 0x{:X}) because it exceeds the maximum size of the compilation".format(rom["filename"], rom["size"]))
print("Added {:d} ROM(s) that do not use SRAM to the compilation".format(len(rom_map) - len(sram_slots_used)))
time.sleep(0.1)

# Patch Menu ROM
v7001_values = {0x800000:0x00, 0x400000:0x80, 0x200000:0xC0, 0x100000:0xE0, 0x80000:0xF0, 0x40000:0xF8, 0x20000:0xFC, 0x10000:0xFE, 0x8000:0xFF}
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

	if v["has_sram"]:
		v7002 += 0x90
		sram_id = math.floor(v["offset"] / 0x200000)
		sram_id = "{:d} (0x{:05X}~)".format(sram_id, sram_id * 0x8000)
	else:
		v7002 += 0xF0
		sram_id = ""
	pos = addr_menu_param + (roms_added * 4)
	menu[pos+0] = x
	menu[pos+1] = v7002 # multirom bank
	menu[pos+2] = v7001 # rom size
	menu[pos+3] = v7000 # rom offset in current multirom bank
	if info_table_sort == 2:
		table_index = v["offset"]
	else:
		table_index = v["index"]
	table_line = "{:3d} | {:16s} | 0x{:07X} | 0x{:06X} | {:02X}:{:02X}:{:02X}:{:02X} | {:4s}".format(v["index"]+1, v["title"], v["offset"], v["size"], v7000, v7001, v7002, x, sram_id)
	table_lines[table_index] = table_line
	roms_added += 1
	if roms_added >= max_roms: break
print("\nGenerated Menu Configuration:\n")
print("  # | Title            | Offset    | Size     | Parameters  | SRAM Slot    ")
print("----+------------------+-----------+----------+-------------+--------------")
table_lines = dict(sorted(table_lines.items()))
for table_line in table_lines.values():
	print(table_line)

menu[addr_num_items] = roms_added & 0xFF
menu[addr_num_pages] = (math.ceil(roms_added / roms_per_page) - 1) & 0xFF
menu[addr_menu_title:addr_menu_title+16] = menu_title.center(16).encode("ascii")[:16]
rom_title = rom_title.strip()
menu[0x134:0x134+15] = rom_title.encode("ascii").ljust(15, b"\x00")[:15]
created_string = \
"256M ROM Builder" \
"by LK\x00\x01\x00{:s}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
menu[0x150:0x150+len(created_string)] = created_string.encode("ascii")
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

# Write Output Buffer to File
with open(output_file, "wb") as f: f.write(output)
print("\nDone! Compilation saved to {:s}".format(output_file))
time.sleep(1)
