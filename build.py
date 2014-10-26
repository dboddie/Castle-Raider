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

from tools import makeadf, makedfs, makelevels, makesprites

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

def encode_text(lines):

    # Store the text reversed to reduce the number of instructions needed to
    # print it.
    
    text_length = 0
    data = ""
    lines.reverse()
    
    for line in lines:
    
        text_values = []
        
        for piece in line:
        
            if type(piece) == int:
                text_values.append(chr(piece))
            else:
                text_values.append(piece[::-1])
        
        text_values.reverse()
        data += "".join(text_values)
    
    return data

def encode_data(bytes):

    data = []
    i = 0
    while i < len(bytes):
    
        data.append(".byte " + ",".join(map(lambda x: "$%02x" % ord(x), bytes[i:i+24])))
        i += 24
    
    return "\n".join(data)

tiles = map(lambda tile: makelevels.tile_ref[tile], makelevels.tile_order)

char_sprites = ["images/g-left1.png", "images/g-left2.png",
                "images/g-right1.png", "images/g-right2.png",
                "images/b-left1.png", "images/b-left2.png",
                "images/b-right1.png", "images/b-right2.png"]

monster_sprites = ["images/bat1.png", "images/bat2.png",
                 "images/spider1.png", "images/spider2.png"]

life_sprites = ["images/life1.png", "images/life2.png"]

misc_routines = [
    "print_title_text",
    "print_game_over_text",
    "check_key",
    "wait_for_key",
    "clear_bank",
    "clear_bank1",
    "clear_bank2",
    "read_joystick_axis",
    "read_joystick_fire",
    "disable_sound",
    "wait_for_space_or_fire",
    "next_cell",
    "next_cell_screen",
    ]

def encode_in_game_data_and_routines(in_game_data_address):

    # Encode the in-game title data.
    data = ""
    
    title_rows = 0
    for line in open("title.txt").readlines():
    
        line = line.rstrip("\n")
        
        for i in range(0, 40, 4):
        
            byte = 0
            shift = 0
            for char in line[i:i + 4]:
                byte = byte | (".@#+".index(char) << shift)
                shift += 2
            
            data += chr(byte)
        
        title_rows += 1
    
    in_game_title_text_address = in_game_data_address + len(data)
    
    title_text = [(26, 31, 3, 6, 17, 3, "Retro Software"),
                      (31, 6, 8, "presents"),
                      (31, 2, 27, 17, 2, "Press ", 17, 3, "SPACE/FIRE"),
                      (31, 6, 29, 17, 2, "to play")]
    
    title_data = encode_text(title_text)
    data += title_data
    in_game_title_text_length = len(title_data)
    
    in_game_game_over_text_address = in_game_title_text_address + \
                                     in_game_title_text_length
    
    game_over_text = [(26, 31, 1, 16, 17, 3, "Your quest is over"),
                          (31, 2, 29, 17, 1, "Press SPACE/FIRE")]
    
    game_over_data = encode_text(game_over_text)
    data += game_over_data
    in_game_game_over_text_length = len(game_over_data)
    
    in_game_title_routines_address = in_game_game_over_text_address + \
                                     in_game_game_over_text_length
    
    labels = (
        ".alias title_data_address              $%(title_data_address)x\n"
        ".alias title_rows                      %(title_rows)i\n"
        ".alias in_game_title_text_address      $%(in_game_title_text_address)x\n"
        ".alias in_game_title_text_length       %(in_game_title_text_length)i\n"
        ".alias in_game_game_over_text_address  $%(in_game_game_over_text_address)x\n"
        ".alias in_game_game_over_text_length   %(in_game_game_over_text_length)i\n"
    )
    
    details = {
        "title_data_address": in_game_data_address,
        "title_rows": title_rows,
        "in_game_title_text_address": in_game_title_text_address,
        "in_game_title_text_length": in_game_title_text_length,
        "in_game_game_over_text_address": in_game_game_over_text_address,
        "in_game_game_over_text_length": in_game_game_over_text_length,
        }
    
    routine_address = in_game_title_routines_address
    
    for name in misc_routines:
    
        routine = open(os.path.join("routines", name + ".oph")).read()
        print "Assembling", name, "at $%x" % routine_address
        
        # Substitute the routine address into the code if necessary and include
        # aliases so that the routine can call any previously defined routines.
        details["routine_address"] = routine_address
        routine = (routine % details) + "\n" + (labels % details)
        
        open("temp.oph", "w").write(routine)
        system("ophis temp.oph -o TEMP")
        
        # Include the routine in the title data file.
        data += open("TEMP").read()
        
        # Add the run-time address to the constants.
        labels += ".alias " + name + (" $%0x\n" % routine_address)
        details[name] = routine_address
        
        # Update the routine address.
        routine_address += os.stat("TEMP")[stat.ST_SIZE]
        
        os.remove("temp.oph")
        os.remove("TEMP")
    
    # Store the address of the end of the working area.
    details["working_end"] = routine_address
    
    # Define aliases for the start, length and end of the block of data
    # created by this function.
    
    labels += (
        ".alias routines_low                    $%02x\n"
        ".alias routines_high                   $%02x\n"
        ".alias routines_length_low             $%02x\n"
        ".alias routines_length_high            $%02x\n"
        ".alias routines_end_low                $%02x\n"
        ".alias routines_end_high               $%02x\n"
        ) % (in_game_data_address & 0xff, in_game_data_address >> 8,
             len(data) & 0xff, len(data) >> 8,
             (in_game_data_address + len(data)) & 0xff,
             (in_game_data_address + len(data)) >> 8)
    
    return labels, details, data

if __name__ == "__main__":

    if not 3 <= len(sys.argv) <= 4:
    
        sys.stderr.write("Usage: %s -e|-b -t|-a|-d <new UEF or ADF file> [level file]\n" % sys.argv[0])
        sys.exit(1)
    
    machine_type = sys.argv[1]
    if machine_type not in ("-e", "-b"):
        sys.stderr.write("Please specify a valid machine type.\n")
        sys.exit(1)
    
    make_tape_image = sys.argv[2] == "-t"
    make_adfs_image = sys.argv[2] == "-a"
    make_dfs_image = sys.argv[2] == "-d"
    out_file = sys.argv[3]
    
    if len(sys.argv) == 4:
        level_file = "levels/default.txt"
    else:
        level_file = sys.argv[4]
    
    # Memory map
    memory_map = {
        "working area": 0xb00,
        "code start": 0x0e00,
        "data start": 0x2150 + 0x20 + 6,
        "tile sprites": 0x2aa0 + 0xc0 + 0x20,
        "character and object sprites": 0x2de0 + 0xc0 + 0x20,
        "bank 1 (panel)": 0x3000,
        "(loader code)": 0x3500,
        "bank 2": 0x5800
        }
    
    code_start = memory_map["code start"]
    
    maximum_number_of_special_tiles = 16
    maximum_number_of_portals = 16
    
    data_start = memory_map["data start"]
    
    # Global variables
    
    # Use the Econet workspace for the player variables.
    player_information            = 0x90
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
    using_joystick                = player_information + 13
    
    # Use the filing system scratch space for the monster variables.
    monster_information           = 0xb0
    monster_left_index            = monster_information
    monster_left_offset           = monster_information + 1
    monster_left_max_offset       = monster_information + 2
    monster_right_index           = monster_information + 3
    monster_right_offset          = monster_information + 4
    monster_right_max_offset      = monster_information + 5
    
    # Working data
    # Place working data in pages B (the soft key buffer) and C (the user
    # defined characters buffer).
    
    # Monster positions
    monster_positions_address     = memory_map["working area"]
    
    # Working information about tile visibility.
    tile_visibility_address       = monster_positions_address + 0x14
    # Low and high bytes are adjusted by 16 bytes so that entries can be
    # addressed directly, starting with an index of 16.
    tile_visibility_low = (tile_visibility_address - 0x10) & 0xff
    tile_visibility_high = (tile_visibility_address - 0x10) >> 8
    
    # The furthest that spans can be displaced to the right.
    max_row_offsets               = tile_visibility_address + maximum_number_of_special_tiles
    
    # The tile type occurring at the left edge of the screen.
    initial_row_tiles             = max_row_offsets + 0x10
    # Indices into each row of the level data.
    row_indices                   = initial_row_tiles + 0x10
    # Initial displacements for the rows.
    initial_row_offsets           = row_indices + 0x10
    
    # Store the in-game text data and other routines above the working data.
    # The generated file is loaded in the game loader.
    title_data_address = initial_row_offsets + 0x10
    
    in_game_data_labels, in_game_data_details, title_data_routines = \
        encode_in_game_data_and_routines(title_data_address)
    working_end = in_game_data_details["working_end"]
    
    # Permanent data
    
    # Level data
    level_data_start = data_start
    
    # Visibility flags for special tiles
    special_tile_numbers_address  = level_data_start
    # Low and high bytes are adjusted by 16 bytes so that entries can be
    # addressed directly, starting with an index of 16.
    special_tile_numbers_low      = (special_tile_numbers_address - 0x10) & 0xff
    special_tile_numbers_high     = (special_tile_numbers_address - 0x10) >> 8
    
    # Visibility flags for special tiles
    initial_tile_visibility_address = special_tile_numbers_address + maximum_number_of_special_tiles
    
    # Portal destinations
    portal_table_address = initial_tile_visibility_address + maximum_number_of_special_tiles
    
    # Low bytes for the addresses of the rows.
    row_table_low                 = portal_table_address + (maximum_number_of_portals * 3)
    # High bytes for the addresses of the rows.
    row_table_high                = row_table_low + 0x10
    level_data                    = row_table_high + 0x10
    level_data_low                = level_data & 0xff
    level_data_high               = level_data >> 8
    
    # Create the level data.
    levels_address = level_data_start
    level_data, monster_row_address, finishing_offset = makelevels.create_level(
        levels_address, level_file, maximum_number_of_special_tiles, maximum_number_of_portals)
    
    level_extent = makelevels.level_extent
    
    files = []
    
    sprite_area_address = memory_map["tile sprites"]
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
    
    # Place the monster and character sprite data after the tile data.
    # Allow the end of the data to overlap where the panel data will be loaded
    # because we will discard one set of character sprites when the user
    # chooses a character.
    char_area_address = right_sprites + (all_tiles * 8)
    
    monster_sprites_address = char_area_address
    monster_sprites_data, monster_sprites_addresses = \
        makesprites.read_sprites(monster_sprites, monster_sprites_address)
    char_data = monster_sprites_data
    
    monster_sprites_shifted_address = char_area_address + len(char_data)
    monster_sprites_data, monster_sprites_shifted_addresses = \
        makesprites.read_shifted_sprites(monster_sprites, monster_sprites_shifted_address)
    char_data += monster_sprites_data
    
    life_sprites_address = char_area_address + len(char_data)
    life_sprites_data, life_sprites_addresses = \
        makesprites.read_sprites(life_sprites, life_sprites_address)
    char_data += life_sprites_data
    
    player_data, player_sprite_offsets = \
        makesprites.read_sprites(char_sprites, char_area_address + len(char_data))
    char_data += player_data
    
    panel_address = 0x3000
    panel, offsets = makesprites.read_sprites(["images/panel.png"], panel_address)
    
    top_panel_objects_bank1 = 0x31d8
    top_panel_objects_bank1_low = top_panel_objects_bank1 & 0xff
    top_panel_objects_bank1_high = top_panel_objects_bank1 >> 8
    top_panel_objects_bank2 = 0x59d8
    top_panel_objects_bank2_low = top_panel_objects_bank2 & 0xff
    top_panel_objects_bank2_high = top_panel_objects_bank2 >> 8
    
    top_panel_lives_bank1 = 0x3000 + (0x140 + 0x28)
    top_panel_lives_bank1_low = top_panel_lives_bank1 & 0xff
    top_panel_lives_bank1_high = top_panel_lives_bank1 >> 8
    top_panel_lives_bank2 = 0x5800 + (0x140 + 0x28)
    top_panel_lives_bank2_low = top_panel_lives_bank2 & 0xff
    top_panel_lives_bank2_high = top_panel_lives_bank2 >> 8
    
    title_data = makesprites.read_title("images/title.png")
    
    # Create the contents of a file containing constant values.
    
    constants_oph = (
        ".alias monster_movement_offset         $7e\n"
        ".alias scrolled                        $7f\n"
        ".alias scroll_offset_low               $8e\n"
        ".alias scroll_offset_high              $8f\n"
        ".alias finish_scroll_offset_low        $%02x\n"
        ".alias finish_scroll_offset_high       $%02x\n"
        "\n"
        "; Declare these here to make it easy to see that they are being used.\n"
        ".alias tile_visibility_table_low       $82\n"
        ".alias tile_visibility_table_high      $83\n"
        ".alias special_tile_numbers_table_low  $84\n"
        ".alias special_tile_numbers_table_high $85\n"
        ".alias monster_positions_table_low     $86\n"
        ".alias monster_positions_table_high    $87\n"
        "\n"
        ".alias check_monster_tile              $8a\n"
        "\n"
        ) % (finishing_offset & 0xff, finishing_offset >> 8)

    constants_oph += (
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
        ".alias using_joystick                  $%x\n"
        "\n"
        ) % (player_x, player_y, bank_number,
             player_animation, player_jumping, player_moving,
             player_falling, player_ys, player_lives, player_lost,
             tracking_low, tracking_high, tracking_y, using_joystick)
    
    constants_oph += (
        ".alias max_row_offsets                 $%x\n"
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
        ) % (max_row_offsets, initial_row_tiles, row_indices, initial_row_offsets,
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
        ".alias life_sprite1                    $%x\n"
        ".alias life_sprite2                    $%x\n"
        ".alias top_panel_lives_bank1           $%04x\n"
        ".alias top_panel_lives_bank1_low       $%02x\n"
        ".alias top_panel_lives_bank1_high      $%02x\n"
        ".alias top_panel_lives_bank2           $%04x\n"
        ".alias top_panel_lives_bank2_low       $%02x\n"
        ".alias top_panel_lives_bank2_high      $%02x\n"
        "\n"
        ) % (life_sprites_address, life_sprites_address + 0x10,
             top_panel_lives_bank1,
             top_panel_lives_bank1_low, top_panel_lives_bank1_high,
             top_panel_lives_bank2,
             top_panel_lives_bank2_low, top_panel_lives_bank2_high)
    
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
        ".alias monster_row_address_low         $%02x\n"
        ".alias monster_row_address_high        $%02x\n"
        "\n"
        ) % (address_length_end(levels_address, level_data) + (
            level_extent, level_extent & 0xff, level_extent >> 8) + (
            monster_row_address & 0xff, monster_row_address >> 8))
    
    constants_oph += (
        ".alias special_tile_numbers_low        $%02x\n"
        ".alias special_tile_numbers_high       $%02x\n"
        ".alias tile_visibility_address         $%x\n"
        ".alias tile_visibility_low             $%02x   ; 16 bytes less than full address\n"
        ".alias tile_visibility_high            $%02x   ; for easier referencing\n"
        ".alias tile_visibility_length          %i\n"
        "\n"
        ) % (special_tile_numbers_low, special_tile_numbers_high,
             tile_visibility_address, tile_visibility_low,
             tile_visibility_high, maximum_number_of_special_tiles)
    
    constants_oph += (
        ".alias sprites_file_area                       $%x\n"
        ".alias sprites_file_area_low                   $%02x\n"
        ".alias sprites_file_area_high                  $%02x\n"
        ".alias sprites_file_area_length_low            $%02x\n"
        ".alias sprites_file_area_length_high           $%02x\n"
        ".alias sprites_file_area_end_low               $%02x\n"
        ".alias sprites_file_area_end_high              $%02x\n"
        "\n"
        ) % ((sprite_area_address,) + \
        address_length_end(sprite_area_address, sprite_data + char_data))
    
    constants_oph += (
        ".alias top_panel_address_low           $%02x\n"
        ".alias top_panel_address_high          $%02x\n"
        ".alias top_panel_length_low            $%02x\n"
        ".alias top_panel_length_high           $%02x\n"
        ".alias top_panel_end_low               $%02x\n"
        ".alias top_panel_end_high              $%02x\n"
        "\n"
        ".alias top_panel_objects_bank1         $%04x\n"
        ".alias top_panel_objects_bank1_low     $%02x\n"
        ".alias top_panel_objects_bank1_high    $%02x\n"
        ".alias top_panel_objects_bank2         $%04x\n"
        ".alias top_panel_objects_bank2_low     $%02x\n"
        ".alias top_panel_objects_bank2_high    $%02x\n"
        "\n"
        ) % (address_length_end(panel_address, panel) + \
            (top_panel_objects_bank1,
             top_panel_objects_bank1_low,
             top_panel_objects_bank1_high,
             top_panel_objects_bank2,
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
        ".alias monster_left_index              $%x\n"
        ".alias monster_left_offset             $%x\n"
        ".alias monster_left_max_offset         $%x\n"
        ".alias monster_right_index             $%x\n"
        ".alias monster_right_offset            $%x\n"
        ".alias monster_right_max_offset        $%x\n\n"
        ) % (monster_row_address,
             monster_left_index,
             monster_left_offset,
             monster_left_max_offset,
             monster_right_index,
             monster_right_offset,
             monster_right_max_offset)
    
    constants_oph += (in_game_data_labels % in_game_data_details) + "\n"
    
    scenery_rows = 16
    extra_rows = 7
    top_char_row, top_monster_row, top_row = 0, 0, 0
    bottom_char_row = scenery_rows + extra_rows - 3
    bottom_monster_row = bottom_row = scenery_rows + extra_rows - 1
    
    char_rows = range(6, 13)
    rows = range(13, 29)
    banks_char_rows_low = map(lambda x: (0x3000 + (x * 0x140)) & 0xff, char_rows)
    bank1_char_rows_high = map(lambda x: (0x3000 + (x * 0x140)) >> 8, char_rows)
    bank2_char_rows_high = map(lambda x: (0x5800 + (x * 0x140)) >> 8, char_rows)
    banks_rows_low = map(lambda x: (0x3000 + (x * 0x140)) & 0xff, rows)
    bank1_rows_high = map(lambda x: (0x3000 + (x * 0x140)) >> 8, rows)
    bank2_rows_high = map(lambda x: (0x5800 + (x * 0x140)) >> 8, rows)
    
    screen_oph = (
        "banks_char_rows_low:  .byte %s\n"
        "banks_rows_low:       .byte %s\n"
        "bank1_char_rows_high: .byte %s\n"
        "bank1_rows_high:      .byte %s\n"
        "bank2_char_rows_high: .byte %s\n"
        "bank2_rows_high:      .byte %s\n\n"
        ) % (",".join(map(lambda x: "$%02x" % x, banks_char_rows_low)),
             ",".join(map(lambda x: "$%02x" % x, banks_rows_low)),
             ",".join(map(lambda x: "$%02x" % x, bank1_char_rows_high)),
             ",".join(map(lambda x: "$%02x" % x, bank1_rows_high)),
             ",".join(map(lambda x: "$%02x" % x, bank2_char_rows_high)),
             ",".join(map(lambda x: "$%02x" % x, bank2_rows_high)))
    
    screen_oph += (
        "; Define the vertical extent of the player area in terms of rows.\n"
        ".alias scenery_rows %i\n"
        ".alias extra_rows %i\n"
        ".alias top_char_row %i\n"
        ".alias top_monster_row %i\n"
        ".alias top_row %i\n"
        ".alias bottom_char_row %i\n"
        ".alias bottom_monster_row %i\n"
        ".alias bottom_row %i\n\n"
        ) % (scenery_rows, extra_rows,
             top_char_row, top_monster_row, top_row,
             bottom_char_row, bottom_monster_row, bottom_row)
    
    # Assemble the main game code and loader code.
    
    open("constants.oph", "w").write(constants_oph)
    open("screen.oph", "w").write(screen_oph)
    
    if machine_type == "-e":
        shutil.copy2("electron.oph", "bank_routines.oph")
    elif machine_type == "-b":
        shutil.copy2("bbc.oph", "bank_routines.oph")
    
    system("ophis code.oph -o CODE")
    code = open("CODE").read()
    os.remove("CODE")
    
    loader_start = 0x3500
    
    marker_info = [(levels_address, level_data),
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
        "; Additional definitions for the loader\n\n"
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
    
    open("loader-constants.oph", "w").write(extras_oph)
    
    system("ophis loader.oph -o LOADER")
    loader_code = open("LOADER").read() + markers + title_data
    os.remove("LOADER")
    
    bootloader_start = 0xe00
    bootloader_code = ("\r\x00\x0a\x0d*FX 229,1"
                       "\r\x00\x14\x0f*RUN LOADER\r\xff\x0a\x14\x00")
    
    files = [("CASTLE", bootloader_start, bootloader_start, bootloader_code),
             ("LOADER", loader_start, loader_start, loader_code),
             ("ROUTINES", title_data_address, title_data_address,
                          title_data_routines),
             ("SPRITES", sprite_area_address, sprite_area_address,
                         sprite_data + char_data),
             ("LEVELS", levels_address, levels_address, level_data),
             ("PANEL", panel_address, panel_address, panel),
             ("CODE", code_start, code_start, code)]
    
    loader_size = len(loader_code)
    print
    print "%i bytes (%04x) of loader code" % (loader_size, loader_size)
    
    code_size = len(code)
    print "%i bytes (%04x) of code" % (code_size, code_size)
    print
    
    # Calculate the amount of space used for the loader.
    
    loader_finish = loader_start + loader_size
    print "LOADER runs from %04x to %04x" % (loader_start, loader_finish)
    print
    
    # Calculate the amount of working space used.
    # 0xcfb is the start of a block of memory used for palette operations.
    
    working_free = 0xcfb - working_end
    print "Working data area runs from 0b00 to %04x" % working_end,
    if working_free < 0:
        print
        sys.stderr.write("Working data area overruns following data by %i bytes.\n" % -working_free)
        sys.exit(1)
    else:
        print "(%i bytes free)" % working_free
    print
    
    # Calculate the amount of memory used for each file.
    
    code_finish = code_start + code_size
    print "CODE    runs from %04x to %04x" % (code_start, code_finish),
    if code_finish > data_start:
        print
        sys.stderr.write("CODE overruns following data by %i bytes.\n" % (code_finish - data_start))
        sys.exit(1)
    else:
        print "(%i bytes free)" % (data_start - code_finish)
    
    levels_finish = levels_address + len(level_data)
    print "LEVELS  runs from %04x to %04x" % (levels_address, levels_finish),
    if levels_finish > sprite_area_address:
        print
        sys.stderr.write("LEVELS overruns following data by %i bytes.\n" % (levels_finish - sprite_area_address))
        sys.exit(1)
    else:
        print "(%i bytes free)" % (sprite_area_address - levels_finish)
    
    char_area_finish = sprite_area_address + len(sprite_data) + len(char_data)
    print "SPRITES runs from %04x to %04x" % (sprite_area_address, char_area_finish)
    #if char_area_finish > panel_address:
    #    sys.stderr.write("SPRITES overruns following data by %i bytes.\n" % (char_area_finish - panel_address))
    #    sys.exit(1)
    
    if make_tape_image:
    
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
            u.write(out_file, write_emulator_info = False)
        except UEFfile.UEFfile_error:
            sys.stderr.write("Couldn't write the new executable to %s.\n" % out_file)
            sys.exit(1)
        
        print
        print "Written", out_file
    
    elif make_adfs_image:
    
        disk = makeadf.Disk("M")
        disk.new()
        
        catalogue = disk.catalogue()
        
        disk_files = []
        for name, load, exec_, data in files:
            disk_files.append(makeadf.File(name, data, load, exec_, len(data)))
        
        dir_address = catalogue.sector_size * 2
        catalogue.write("$", "Castle Raider", disk_files, dir_address, dir_address)
        catalogue.write_free_space()
        
        disk.file.seek(0, 0)
        disk_data = disk.file.read()
        open(out_file, "w").write(disk_data)
        
        print
        print "Written", out_file
    
    elif make_dfs_image:
    
        disk = makedfs.Disk()
        disk.new()
        
        catalogue = disk.catalogue()
        catalogue.boot_option = 2
        
        disk_files = []
        for name, load, exec_, data in files:
            if name == "LOADER":
                name = "!BOOT"
            elif name == "CASTLE":
                continue
            disk_files.append(makedfs.File("$." + name, data, load, exec_, len(data)))
        
        catalogue.write("CastleRaider", disk_files)
        
        disk.file.seek(0, 0)
        disk_data = disk.file.read()
        open(out_file, "w").write(disk_data)
        
        print
        print "Written", out_file
    
    # Remove temporary files.
    os.remove("bank_routines.oph")
    os.remove("constants.oph")
    os.remove("loader-constants.oph")
    os.remove("screen.oph")
    
    # Exit
    sys.exit()
