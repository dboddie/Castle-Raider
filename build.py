#!/usr/bin/env python

"""
Copyright (C) 2011 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, stat, struct, sys
import UEFfile

from tools import makelevels, makesprites

version = "0.1"

def system(command):

    if os.system(command):
        sys.exit(1)

def read_basic(path):

    t = open(path).read()
    t = t.replace("\n", "\r")
    lines = t.rstrip().split("\r")
    t = "\r".join(lines) + "\r"
    return t

def encode_text(text):

    words = text.split(" ")
    word_dict = {}
    
    # Count the number of occurrences of each word.
    for word in words:
        word_dict.setdefault(word, 0)
        word_dict[word] += 1
    
    # Sort the words in order of decreasing frequency.
    frequencies = map(lambda x: (x[1], x[0]), word_dict.items())
    frequencies.sort()
    frequencies.reverse()
    
    # Create encoding and decoding look up tables.
    decoding_lookup = {}
    encoding_lookup = {}
    
    i = 0
    for count, word in frequencies:
    
        if i >= 128:
            j = 1 + i * 2
        else:
            j = i * 2
        
        encoding_lookup[word] = j
        decoding_lookup[j] = word
        
        i += 1
    
    # Encode the text.
    encoded = []
    for word in words:
    
        encoded.append(encoding_lookup[word])
    
    encoded_string = ""
    for value in encoded:
    
        if value & 1 == 0:
            encoded_string += chr(value)
        else:
            encoded_string += struct.pack("<H", value)
    
    return decoding_lookup, encoded_string

def decode_text(data, lookup):

    words = ""
    i = 0
    while i < len(data):
    
        value = ord(data[i])
        if value & 1 != 0:
            value += ord(data[i+1]) << 8
            i += 2
        else:
            i += 1
        
        words += lookup[value]
        words += " "
    
    return words[:-1]

def address_length_end(address, data):

    address_low = address & 0xff
    address_high = address >> 8
    length = len(data)
    length_low = length & 0xff
    length_high = length >> 8
    end = address + length
    end_low = end & 0xff
    end_high = end >> 8
    return address_low, address_high, length_low, length_high, end_low, end_high


tiles = map(lambda tile: makelevels.tile_ref[tile], makelevels.tile_order)

char_sprites = ["images/left1.png", "images/left2.png",
                "images/right1.png", "images/right2.png",
                "images/birdl1.png","images/birdl2.png",
                "images/birdr1.png","images/birdr2.png"]

constants_oph = \
""".alias sprite_area_low              $%02x
.alias sprite_area_high             $%02x
.alias sprite_area_length_low       $%02x
.alias sprite_area_length_high      $%02x
.alias sprite_area_end_low          $%02x
.alias sprite_area_end_high         $%02x
.alias left_sprites_low             $%02x
.alias left_sprites_high            $%02x
.alias rotated_sprites_low          $%02x
.alias rotated_sprites_high         $%02x
.alias right_sprites_low            $%02x
.alias right_sprites_high           $%02x

.alias levels_address_low           $%02x
.alias levels_address_high          $%02x
.alias levels_length_low            $%02x
.alias levels_length_high           $%02x
.alias levels_end_low               $%02x
.alias levels_end_high              $%02x
.alias level_extent                 %i
.alias level_extent_low             $%02x
.alias level_extent_high            $%02x

.alias tile_visibility_address      $%x
.alias tile_visibility_low          $%02x
.alias tile_visibility_high         $%02x

.alias char_area                    $%x
.alias char_area_low                $%02x
.alias char_area_high               $%02x
.alias char_area_length_low         $%02x
.alias char_area_length_high        $%02x
.alias char_area_end_low            $%02x
.alias char_area_end_high           $%02x

.alias top_panel_address_low       $%02x
.alias top_panel_address_high      $%02x
.alias top_panel_length_low        $%02x
.alias top_panel_length_high       $%02x
.alias top_panel_end_low           $%02x
.alias top_panel_end_high          $%02x
"""

extras_oph = \
"""
.alias code_start_address           $%02x
.alias code_start_low               $%02x
.alias code_start_high              $%02x
.alias code_length_low              $%02x
.alias code_length_high             $%02x
.alias code_end_low                 $%02x
.alias code_end_high                $%02x
"""

if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 3:
    
        sys.stderr.write("Usage: %s <new UEF file> [level file]\n" % sys.argv[0])
        sys.exit(1)
    
    out_uef_file = sys.argv[1]
    
    if len(sys.argv) == 2:
        level_file = "levels/default.txt"
    else:
        level_file = sys.argv[2]
    
    # Memory map
    #
    # 0e00      code
    # 1f70      tile visibility flags
    # 1f80      max row offsets
    # 1f90      player information
    # 1fa0      initial row tiles
    # 1fb0      row indices
    # 1fc0      initial row offsets
    # 1fd0      initial tile visibility flags
    # 1fe0      row table low
    # 1ff0      row table high
    # 2000      level data
    # 2a00      tile sprites
    # 2d00      character sprites
    # 3000      bank 1 (panel)
    # 3500             (loader code)
    # 5800      bank 2
    
    files = []
    
    sprite_area_address = 0x2a00
    tile_sprites = makesprites.read_tiles(tiles)
    sprite_data = makesprites.read_tile_data(tile_sprites)
    all_tiles = len(tiles)
    
    left_sprites = sprite_area_address + (all_tiles * 8)
    left_sprites_low = left_sprites & 0xff
    left_sprites_high = left_sprites >> 8
    rotated_sprites = left_sprites + (all_tiles * 8)
    rotated_sprites_low = rotated_sprites & 0xff
    rotated_sprites_high = rotated_sprites >> 8
    right_sprites = rotated_sprites + (all_tiles * 8)
    right_sprites_low = right_sprites & 0xff
    right_sprites_high = right_sprites >> 8
    
    char_area_address = 0x2d00
    char_data = makesprites.read_sprites(char_sprites)
    
    levels_address = 0x1fd0
    level_data = makelevels.create_level(tiles, levels_address, level_file)
    
    level_extent = len(makelevels.level[0]) - 40
    
    # Visibility flags for special scenery.
    tile_initial_visibility_address = 0x1fd0
    tile_initial_visibility_low = tile_initial_visibility_address & 0xff
    tile_initial_visibility_high = tile_initial_visibility_address >> 8
    
    tile_visibility_address = 0x1f70
    tile_visibility_low = tile_visibility_address & 0xff
    tile_visibility_high = tile_visibility_address >> 8
    
    code_start = 0x0e00
    data_start = 0x1f70
    
    panel_address = 0x3000
    panel = makesprites.read_sprites(["images/panel.png"])
    
    # Create a tuple of template values.
    
    values = address_length_end(sprite_area_address, sprite_data) + \
        (left_sprites_low, left_sprites_high,
         rotated_sprites_low, rotated_sprites_high,
         right_sprites_low, right_sprites_high) + \
        address_length_end(levels_address, level_data) + \
        (level_extent, level_extent & 0xff, level_extent >> 8,
         tile_visibility_address, tile_visibility_low, tile_visibility_high,
         char_area_address,) + \
        address_length_end(char_area_address, char_data) + \
        address_length_end(panel_address, panel)
    
    # Assemble the main game code and loader code.
    
    open("constants.oph", "w").write(constants_oph % values)
    
    system("ophis code.oph CODE")
    code = open("CODE").read()
    
    loader_start = 0x3500
    
    values = values + (code_start,) + address_length_end(code_start, code)
    
    open("constants.oph", "w").write((constants_oph + extras_oph) % values)
    
    system("ophis loader.oph LOADER")
    loader_code = open("LOADER").read()
    
    files = [("LOADER", loader_start, loader_start, loader_code),
             ("TILES", sprite_area_address, sprite_area_address, sprite_data),
             ("SPRITES", char_area_address, char_area_address, char_data),
             ("LEVELS", levels_address, levels_address, level_data),
             ("PANEL", panel_address, panel_address, panel),
             ("CODE", code_start, code_start, code)]
    
    code_size = os.stat("CODE")[stat.ST_SIZE]
    print "%i bytes (%04x) of code" % (code_size, code_size)
    
    code_finish = code_start + code_size
    print "CODE    runs from %04x to %04x" % (code_start, code_finish)
    if code_finish > data_start:
        sys.stderr.write("CODE overruns following data.\n")
        sys.exit(1)
    
    levels_finish = levels_address + len(level_data)
    print "LEVELS  runs from %04x to %04x" % (levels_address, levels_finish)
    if levels_finish > sprite_area_address:
        sys.stderr.write("LEVELS overruns following data.\n")
        sys.exit(1)
    
    sprite_area_finish = sprite_area_address + len(sprite_data)
    print "TILES   runs from %04x to %04x" % (sprite_area_address, sprite_area_finish)
    if sprite_area_finish > char_area_address:
        sys.stderr.write("TILES overruns following data.\n")
        sys.exit(1)
    
    char_area_finish = char_area_address + len(char_data)
    print "SPRITES runs from %04x to %04x" % (char_area_address, char_area_finish)
    if char_area_finish > panel_address:
        sys.stderr.write("SPRITES overruns following data.\n")
        sys.exit(1)
    
    u = UEFfile.UEFfile(creator = 'build.py '+version)
    u.minor = 6
    u.target_machine = "Electron"
    
    u.import_files(0, files)
    
    # Insert a gap before each file.
    offset = 0
    for f in u.contents:
    
        # Insert a gap and some padding before the file.
        gap_padding = [(0x112, "\xdc\x05"), (0x110, "\xdc\x05"), (0x100, "\xdc")]
        u.chunks = u.chunks[:f["position"] + offset] + \
                   gap_padding + u.chunks[f["position"] + offset:]

        # Each time we insert a gap, the position of the file changes, so we
        # need to update its position and last position. This isn't really
        # necessary because we won't read the contents list again.
        offset += len(gap_padding)
        f["position"] += offset
        f["last position"] += offset
    
    # Write the new UEF file.
    try:
        u.write(out_uef_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % out_uef_file)
        sys.exit(1)

    # Exit
    sys.exit()
