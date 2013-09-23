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

import os, shutil, stat, struct, sys
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

char_sprites = ["images/g-left1.png", "images/g-left2.png",
                "images/g-right1.png", "images/g-right2.png",
                "images/b-left1.png", "images/b-left2.png",
                "images/b-right1.png", "images/b-right2.png"]

monster_sprites = ["images/bat1.png", "images/bat2.png",
                 "images/spider1.png", "images/spider2.png"]


if __name__ == "__main__":

    if not 3 <= len(sys.argv) <= 4:
    
        sys.stderr.write("Usage: %s -e|-b <new UEF file> [level file]\n" % sys.argv[0])
        sys.exit(1)
    
    machine_type = sys.argv[1]
    if machine_type not in ("-e", "-b"):
        sys.stderr.write("Please specify a valid machine type.\n")
        sys.exit(1)
    
    out_uef_file = sys.argv[2]
    
    if len(sys.argv) == 3:
        level_file = "levels/default.txt"
    else:
        level_file = sys.argv[3]
    
    # Memory map
    code_start = 0x0e00
    
    number_of_special_tiles = 32
    maximum_number_of_portals = 16
    
    data_start = 0x2040
    
    # Monster positions
    monster_positions_address       = data_start
    
    # Working information about tile visibility.
    tile_visibility_address       = monster_positions_address + 0x10
    # Low and high bytes are adjusted by 16 bytes so that entries can be
    # addressed directly, starting with an index of 16.
    tile_visibility_low = (tile_visibility_address - 0x10) & 0xff
    tile_visibility_high = (tile_visibility_address - 0x10) >> 8
    
    # The furthest that spans can be displaced to the right.
    max_row_offsets               = tile_visibility_address + number_of_special_tiles
    
    player_information            = max_row_offsets + 0x10
    player_x                      = player_information + 0
    player_y                      = player_information + 1
    bank_number                   = player_information + 2
    player_animation              = player_information + 3
    player_jumping                = player_information + 4
    player_moving                 = player_information + 5
    player_falling                = player_information + 6
    player_ys                     = player_information + 7
    player_lives                  = player_information + 8
    player_lost                   = player_information + 9
    tracking_low                  = player_information + 10
    tracking_high                 = player_information + 11
    tracking_y                    = player_information + 12
    
    monster_information           = player_information + 0x10
    monster_movement_counter      = monster_information
    monster_left_index            = monster_information + 1
    monster_left_offset           = monster_information + 2
    monster_left_max_offset       = monster_information + 3
    monster_right_index           = monster_information + 4
    monster_right_offset          = monster_information + 5
    monster_right_max_offset      = monster_information + 6
    visible_monster_left_index    = monster_information + 7
    visible_monster_right_index   = monster_information + 8
    
    # The tile type occurring at the left edge of the screen.
    initial_row_tiles             = monster_information + 0x10
    # Indices into each row of the level data.
    row_indices                   = initial_row_tiles + 0x10
    # Initial displacements for the rows.
    initial_row_offsets           = row_indices + 0x10
    
    # Level data
    level_data_start = initial_row_offsets + 0x10
    
    # Visibility flags for special tiles
    special_tile_numbers_address  = level_data_start
    # Low and high bytes are adjusted by 16 bytes so that entries can be
    # addressed directly, starting with an index of 16.
    special_tile_numbers_low      = (special_tile_numbers_address - 0x10) & 0xff
    special_tile_numbers_high     = (special_tile_numbers_address - 0x10) >> 8
    
    # Visibility flags for special tiles
    initial_tile_visibility_address = special_tile_numbers_address + number_of_special_tiles
    
    # Portal destinations
    portal_table_address = initial_tile_visibility_address + number_of_special_tiles
    
    # Low bytes for the addresses of the rows.
    row_table_low                 = portal_table_address + (maximum_number_of_portals * 3)
    # High bytes for the addresses of the rows.
    row_table_high                = row_table_low + 0x10
    level_data                    = row_table_high + 0x10
    level_data_low                = level_data & 0xff
    level_data_high               = level_data >> 8
    
    # 2a00      tile sprites
    # 2e00      character and object sprites
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
    
    char_area_address = 0x2d40
    char_data, player_sprite_offsets = \
        makesprites.read_sprites(char_sprites, char_area_address)
    
    monster_sprites_address = char_area_address + len(char_data)
    monster_sprites_data, monster_sprites_addresses = \
        makesprites.read_sprites(monster_sprites, monster_sprites_address)
    char_data += monster_sprites_data
    
    monster_sprites_shifted_address = char_area_address + len(char_data)
    monster_sprites_data, monster_sprites_shifted_addresses = \
        makesprites.read_shifted_sprites(monster_sprites, monster_sprites_shifted_address)
    char_data += monster_sprites_data
    
    levels_address = level_data_start
    level_data, monster_row_address = makelevels.create_level(
        levels_address, level_file, number_of_special_tiles, maximum_number_of_portals)
    
    level_extent = len(makelevels.level[0]) - 40
    
    panel_address = 0x3000
    panel, offsets = makesprites.read_sprites(["images/panel.png"], panel_address)
    
    top_panel_objects_bank1 = 0x31f0
    top_panel_objects_bank1_low = top_panel_objects_bank1 & 0xff
    top_panel_objects_bank1_high = top_panel_objects_bank1 >> 8
    top_panel_objects_bank2 = 0x59f0
    top_panel_objects_bank2_low = top_panel_objects_bank2 & 0xff
    top_panel_objects_bank2_high = top_panel_objects_bank2 >> 8
    
    title_data = makesprites.read_title("images/title.png")
    
    # Create the contents of a file containing constant values.
    
    constants_oph = (
        ".alias max_row_offsets                 $%x\n"
        ".alias player_x                        $%x\n"
        ".alias player_y                        $%x\n"
        ".alias bank_number                     $%x\n"
        ".alias player_animation                $%x\n"
        ".alias player_jumping                  $%x\n"
        ".alias player_moving                   $%x\n"
        ".alias player_falling                  $%x\n"
        ".alias player_ys                       $%x\n"
        ".alias player_lives                    $%x\n"
        ".alias player_lost                     $%x\n"
        ".alias tracking_low                    $%x\n"
        ".alias tracking_high                   $%x\n"
        ".alias tracking_y                      $%x\n"
        "\n"
        ) % (max_row_offsets, player_x, player_y, bank_number,
             player_animation, player_jumping, player_moving,
             player_falling, player_ys, player_lives, player_lost,
             tracking_low, tracking_high, tracking_y)
    
    constants_oph += (
        ".alias initial_row_tiles               $%x\n"
        ".alias row_indices                     $%x\n"
        ".alias initial_row_offsets             $%x\n"
        ".alias special_tile_numbers_address    $%x\n"
        ".alias initial_tile_visibility_address $%x\n"
        ".alias portal_table_address            $%x\n"
        ".alias row_table_low                   $%x\n"
        ".alias row_table_high                  $%x\n"
        ".alias level_data_low                  $%02x\n"
        ".alias level_data_high                 $%02x\n"
        "\n"
        ) % (initial_row_tiles, row_indices, initial_row_offsets,
             special_tile_numbers_address, initial_tile_visibility_address,
             portal_table_address,
             row_table_low, row_table_high, level_data_low, level_data_high)
    
    constants_oph += (
        ".alias sprite_area_low                 $%02x\n"
        ".alias sprite_area_high                $%02x\n"
        ".alias sprite_area_length_low          $%02x\n"
        ".alias sprite_area_length_high         $%02x\n"
        ".alias sprite_area_end_low             $%02x\n"
        ".alias sprite_area_end_high            $%02x\n"
        "\n"
        ) % address_length_end(sprite_area_address, sprite_data)
    
    constants_oph += (
        ".alias left_sprites_low                $%02x\n"
        ".alias left_sprites_high               $%02x\n"
        ".alias rotated_sprites_low             $%02x\n"
        ".alias rotated_sprites_high            $%02x\n"
        ".alias right_sprites_low               $%02x\n"
        ".alias right_sprites_high              $%02x\n"
        "\n"
        ) % (left_sprites_low, left_sprites_high,
         rotated_sprites_low, rotated_sprites_high,
         right_sprites_low, right_sprites_high)
    
    constants_oph += (
        ".alias levels_address_low              $%02x\n"
        ".alias levels_address_high             $%02x\n"
        ".alias levels_length_low               $%02x\n"
        ".alias levels_length_high              $%02x\n"
        ".alias levels_end_low                  $%02x\n"
        ".alias levels_end_high                 $%02x\n"
        ".alias level_extent                    %i\n"
        ".alias level_extent_low                $%02x\n"
        ".alias level_extent_high               $%02x\n"
        "\n"
        ) % (address_length_end(levels_address, level_data) + (
            level_extent, level_extent & 0xff, level_extent >> 8))
    
    constants_oph += (
        ".alias special_tile_numbers_low        $%02x\n"
        ".alias special_tile_numbers_high       $%02x\n"
        ".alias tile_visibility_address         $%x\n"
        ".alias tile_visibility_low             $%02x\n"
        ".alias tile_visibility_high            $%02x\n"
        "\n"
        ) % (special_tile_numbers_low, special_tile_numbers_high,
             tile_visibility_address, tile_visibility_low,
             tile_visibility_high)
    
    constants_oph += (
        ".alias char_area                       $%x\n"
        ".alias char_area_low                   $%02x\n"
        ".alias char_area_high                  $%02x\n"
        ".alias char_area_length_low            $%02x\n"
        ".alias char_area_length_high           $%02x\n"
        ".alias char_area_end_low               $%02x\n"
        ".alias char_area_end_high              $%02x\n"
        "\n"
        ) % ((char_area_address,) + \
        address_length_end(char_area_address, char_data))
    
    constants_oph += (
        ".alias top_panel_address_low           $%02x\n"
        ".alias top_panel_address_high          $%02x\n"
        ".alias top_panel_length_low            $%02x\n"
        ".alias top_panel_length_high           $%02x\n"
        ".alias top_panel_end_low               $%02x\n"
        ".alias top_panel_end_high              $%02x\n"
        "\n"
        ".alias top_panel_objects_bank1_low     $%02x\n"
        ".alias top_panel_objects_bank1_high    $%02x\n"
        ".alias top_panel_objects_bank2_low     $%02x\n"
        ".alias top_panel_objects_bank2_high    $%02x\n"
        "\n"
        ) % (address_length_end(panel_address, panel) + \
            (top_panel_objects_bank1_low,
             top_panel_objects_bank1_high,
             top_panel_objects_bank2_low,
             top_panel_objects_bank2_high))
    
    constants_oph += (
        ".alias player_left1                    $%04x\n"
        ".alias player_left2                    $%04x\n"
        ".alias player_right1                   $%04x\n"
        ".alias player_right2                   $%04x\n"
        ".alias player_left_alt1                $%04x\n"
        ".alias player_left_alt2                $%04x\n"
        ".alias player_right_alt1               $%04x\n"
        ".alias player_right_alt2               $%04x\n\n"
        ) % tuple(player_sprite_offsets)
    
    s = 0
    for address, shifted_address in zip(monster_sprites_addresses, monster_sprites_shifted_addresses):
    
        constants_oph += (
            ".alias monster_spr_low%i                $%02x\n"
            ".alias monster_spr_high%i               $%02x\n"
            ) % (s, address & 0xff, s, address >> 8)
        
        constants_oph += (
            ".alias monster_spr_sh_low%i             $%02x\n"
            ".alias monster_spr_sh_high%i            $%02x\n"
            ) % (s, shifted_address & 0xff, s, shifted_address >> 8)
        
        s += 1
    
    constants_oph += (
        "\n"
        ".alias monster_positions_address       $%x\n"
        ".alias monster_positions_low           $%02x\n"
        ".alias monster_positions_high          $%02x\n\n"
        ) % (monster_positions_address, monster_positions_address & 0xff,
             monster_positions_address >> 8)
    
    constants_oph += (
        ".alias monster_row_address             $%x\n"
        ".alias monster_movement_counter        $%x\n"
        ".alias monster_left_index              $%x\n"
        ".alias monster_left_offset             $%x\n"
        ".alias monster_left_max_offset         $%x\n"
        ".alias monster_right_index             $%x\n"
        ".alias monster_right_offset            $%x\n"
        ".alias monster_right_max_offset        $%x\n"
        ".alias visible_monster_left_index      $%x\n"
        ".alias visible_monster_right_index     $%x\n\n"
        ) % (monster_row_address,
             monster_movement_counter,
             monster_left_index,
             monster_left_offset,
             monster_left_max_offset,
             monster_right_index,
             monster_right_offset,
             monster_right_max_offset,
             visible_monster_left_index,
             visible_monster_right_index)
    
    # Assemble the main game code and loader code.
    
    open("constants.oph", "w").write(constants_oph)
    
    if machine_type == "-e":
        shutil.copy2("electron.oph", "bank_routines.oph")
    elif machine_type == "-b":
        shutil.copy2("bbc.oph", "bank_routines.oph")
    
    system("ophis code.oph -o CODE")
    code = open("CODE").read()
    
    loader_start = 0x3500
    
    marker_info = [(sprite_area_address, sprite_data),
                   (char_area_address, char_data),
                   (levels_address, level_data),
                   (panel_address, panel),
                   (code_start, code)]
    markers = ""
    n = 0
    
    for address, data in marker_info:
    
        ptr = 64
        while ptr < len(data):
        
            low = (address + ptr) & 0xff
            high = (address + ptr) >> 8
            markers += chr(low) + chr(high) + data[ptr]
            ptr += 128
            n += 1
    
    markers = chr(n) + markers
    
    extras_oph = constants_oph + (
        ".alias code_start_address              $%02x\n"
        ".alias code_start_low                  $%02x\n"
        ".alias code_start_high                 $%02x\n"
        ".alias code_length_low                 $%02x\n"
        ".alias code_length_high                $%02x\n"
        ".alias code_end_low                    $%02x\n"
        ".alias code_end_high                   $%02x\n"
        "\n"
        ".alias markers_length                  $%02x\n"
        "\n"
        ) % ((code_start,) + address_length_end(code_start, code) + \
             (len(markers),))
    
    open("constants.oph", "w").write(extras_oph)
    
    system("ophis loader.oph -o LOADER")
    loader_code = open("LOADER").read() + markers + title_data
    
    bootloader_start = 0xe00
    bootloader_code = ("\r\x00\x0a\x0d*FX 229,1"
                       "\r\x00\x14\x0f*RUN LOADER\r\xff\x0a\x14\x00")
    
    files = [("CASTLE", bootloader_start, bootloader_start, bootloader_code),
             ("LOADER", loader_start, loader_start, loader_code),
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
    
    print "data    runs from %04x to %04x" % (data_start, level_data_start)
    
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
