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


tiles = ["images/blank.png", "images/brick.png", "images/grass.png",
         "images/grass2.png",
         "images/ground.png", "images/ground2.png", "images/floor.png",
         "images/door.png",
         "images/window-topleft.png", "images/window-topright.png",
         "images/brick-left.png", "images/brick-right.png",
         "images/rope.png", "images/flag.png"]

char_sprites = ["images/left1.png", "images/left2.png", "images/right1.png", "images/right2.png"]

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

.alias char_area                    $%x
.alias char_area_low                $%02x
.alias char_area_high               $%02x
.alias char_area_length_low         $%02x
.alias char_area_length_high        $%02x
.alias char_area_end_low            $%02x
.alias char_area_end_high           $%02x
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

    if len(sys.argv) != 2:
    
        sys.stderr.write("Usage: %s <new UEF file>\n" % sys.argv[0])
        sys.exit(1)
    
    out_uef_file = sys.argv[1]
    
    # Memory map
    #
    #  e00      code
    # 1fa0      player position, animation and bank number
    # 1fb0      (free)
    # 1fc0      row indices
    # 1fd0      initial row offsets
    # 1fe0      row table low
    # 1ff0      row table high
    # 2000      level data
    # 2a00      tile sprites
    # 2e00      character sprites
    # 3000      bank 1
    # 5800      bank 2
    
    files = []
    
    levels_address = 0x1fe0
    level_data = makelevels.create_levels(tiles)
    files.append(("LEVELS", levels_address, levels_address, level_data))
    
    level_extent = len(makelevels.levels[0][0]) - 40
    
    sprite_area_address = 0x2a00
    sprite_data = makesprites.read_tiles(tiles)
    files.append(("TILES", sprite_area_address, sprite_area_address, sprite_data))
    
    left_sprites = sprite_area_address + (len(tiles) * 8)
    left_sprites_low = left_sprites & 0xff
    left_sprites_high = left_sprites >> 8
    rotated_sprites = left_sprites + (len(tiles) * 8)
    rotated_sprites_low = rotated_sprites & 0xff
    rotated_sprites_high = rotated_sprites >> 8
    right_sprites = rotated_sprites + (len(tiles) * 8)
    right_sprites_low = right_sprites & 0xff
    right_sprites_high = right_sprites >> 8
    
    char_area_address = 0x2E00
    char_data = makesprites.read_sprites(char_sprites)
    files.append(("SPRITES", char_area_address, char_area_address, char_data))
    
    code_start = 0x0e00
    
    values = address_length_end(sprite_area_address, sprite_data) + \
        (left_sprites_low, left_sprites_high,
         rotated_sprites_low, rotated_sprites_high,
         right_sprites_low, right_sprites_high) + \
        address_length_end(levels_address, level_data) + \
        (level_extent, level_extent & 0xff, level_extent >> 8) + \
        (char_area_address,) + \
        address_length_end(char_area_address, char_data)
    
    open("constants.oph", "w").write(constants_oph % values)
    
    system("ophis code.oph CODE")
    code = open("CODE").read()
    files.append(("CODE", code_start, code_start, code))
    
    loader_start = 0x1900
    
    values = values + (code_start,) + address_length_end(code_start, code)
    
    open("constants.oph", "w").write((constants_oph + extras_oph) % values)
    
    system("ophis loader.oph LOADER")
    loader_code = open("LOADER").read()
    files.insert(0, ("LOADER", loader_start, loader_start, loader_code))
    
    code_size = os.stat("CODE")[stat.ST_SIZE]
    print "%i bytes (%04x) of code" % (code_size, code_size)
    
    print "CODE runs from %04x to %04x" % (code_start, code_start + code_size)
    print "TILES runs from %04x to %04x" % (sprite_area_address, sprite_area_address + len(sprite_data))
    print "SPRITES runs from %04x to %04x" % (char_area_address, char_area_address + len(char_data))
    
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
