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

class LevelError(Exception):

    pass

class Action:

    def __init__(self):
        self.spans = set()
        self.initial = 0
        self.final = 0
    
    def __repr__(self):
        return "<Action [%x,%x] %i spans>" % (self.initial, self.final, len(self.spans))

tile_ref = {".": "images/blank.png",
            "@": "images/brick.png",
            "#": "images/ground.png",
            "=": "images/floor-middle.png",
            "+": "images/grass.png",
            "-": "images/floor.png",
            "X": "images/rock.png",
            "|": "images/door.png",
            "?": "images/flag.png",
            "[": "images/exit-gate.png",
            "]": "images/brick-alt2.png",
            "/": "images/window-topleft.png",
            "\\": "images/window-topright.png",
            "{": "images/stalactite.png",
            "I": "images/gate.png",
            "%": "images/brick-alt3.png",
            # End of scenery tile sprites
            
            # Start of collectable item sprites
            "K": "images/key.png",
            "L": "images/key1.png",
            "M": "images/key2.png",
            "N": "images/key3.png",
            "q": "images/exit-key.png",
            "C": "images/crown-left.png",
            "D": "images/crown-right.png",
            "E": "images/chest-left.png",
            "F": "images/chest-right.png"}

# Collectable items after the first 16 tiles are ignored by the editor.

tile_order = (".", "@", "#", "=", "+", "-", "X", "|",   # regular tiles
              "?", "[", "]", "/", "\\", "{", "I", "%",  #
              "K", "L", "M", "N", "q", "C", "D", "E", "F")   # collectable tiles

flags_values = {"visible": 0x80, "collectable": 0x40, "door": 0x20, "treasure": 0x10}

monster_ref = {"V": "images/bat1.png", "^": "images/spider1.png",
               "<": "images/bat1.png", ">": "images/spider1.png"}
monster_tiles = {"V": 1,    # bat (vertical)
                 "<": 1,    # bat (horizontal)
                 "^": 2,    # spider (vertical)
                 ">": 2}    # spider (horizontal)
monster_order = ("V", "^")
monster_axes = {"V": 1, "^": 1, "<": 0, ">": 0}
monster_axis_flip = {"V": "<", "^": ">", "<": "V", ">": "^"}

special_order = "abcdefghijklmnopqrstuvwxyz012345"
portals_order = "ZYWUTSRQPONMLKJH"

colours = {"black": 0, "red": 1, "green": 2, "yellow": 3, "blue": 4,
           "magenta": 5, "cyan": 6, "white": 7}

starting_row = 7

def load_level(path):

    # Sanitise the lines read from the file.
    lines = map(lambda x: x.rstrip(), open(path).readlines())
    lines = filter(lambda x: x, lines)
    
    # The special dictionary maps symbols used in the level map to tuples
    # containing corresponding tiles and indices. Each index is an offset into
    # the visibility table, the initial values for which are below.
    special = {}
    
    index = 16
    for line in lines[:16]:
    
        ch, tile, flags_word = line.split()
        flags = flags_word.split(",")
        special[ch] = (tile, index, flags)
        index += 1
    
    portals = {}
    index = 128
    for line in lines[16:32]:
    
        src, dest, colour = line.split()
        portals[src] = (index, dest, colour)
        index += 1
    
    levels = []
    l = 32
    
    while l < len(lines):
    
        name = lines[l]
        levels.append((name, lines[l + 1:l + 17]))
        l += 17
    
    return levels, special, portals

def create_level_data(levels, tiles, special, portals):

    global level_extent
    
    # Stitch the levels together.
    level = []
    
    for i in range(16):
    
        level.append("".join(map(lambda (name, rows): rows[i], levels)))
    
    level_extent = len(level[0]) - 40
    
    data = []
    monsters = {}
    portal_locations = {}
    l = 0
    
    for line in level:
    
        line_data = []
        current = None
        offset = 0
        i = 0
        while i < len(line):
        
            ch = line[i]
            
            if ch in special:
                n, index, flags = special[ch]
                # Special tiles have values greater than or equal to 16.
                c = index
            
            elif ch in portals:
                index, dest, colour = portals[ch]
                dest_index, other_dest, dest_colour = portals[dest]
                portal_locations.setdefault(ch, []).append((i, l))
                
                # Portal tiles have values greater than or equal to 128.
                c = (colours[dest_colour] << 4) | index
            
            elif ch in monster_tiles:
                # Record the monster's position and type.
                monsters[i] = (monster_tiles[ch], l + starting_row, monster_axes[ch])
                # Use the blank tile in the level itself.
                c = tiles["."]
            
            else:
                c = tiles[ch]
            
            if c != current:
            
                if current is not None:
                
                    # Store the tile offset and length of the tile span.
                    line_data.append((current, i - offset))
                
                current = c
                offset = i
            
            i += 1
        
        if i > offset:
            line_data.append((current, i - offset))
        
        data.append(line_data)
        l += 1
    
    monster_data = []
    previous_monster = 0
    previous_y = 0
    previous_axis = 0
    monster_offset = 0
    
    monsters = monsters.items()
    monsters.sort()
    
    for i, (monster, y, axis) in monsters:
    
        if i > monster_offset:
        
            # Add the previous monster to the list of monster spans.
            monster_data.append((previous_monster, previous_y, i - monster_offset, previous_axis))
        
        monster_offset = i
        previous_monster = monster
        previous_y = y
        previous_axis = axis
    
    if monster_offset < len(level[0]):
        monster_data.append((previous_monster, previous_y, len(level[0]) - monster_offset, axis))
    
    # For portal locations that span multiple cells, find the lowest, middle
    # location of the portal.
    
    for portal, locations in portal_locations.items():
    
        xs = set()
        ys = set()
        for x, y in locations:
        
            xs.add(x)
            ys.add(y)
        
        xs = list(xs)
        xs.sort()
        ys = list(ys)
        ys.sort()
        
        # For an even number of tiles, position the character one tile to the
        # left of centre.
        offset = 1 - (len(xs) % 2)
        portal_locations[portal] = (xs[len(xs)/2 - offset], ys[-1])
    
    return data, monster_data, portal_locations

def create_level(levels_address, level_path, maximum_number_of_special_tiles,
                 maximum_number_of_portals):
    
    levels, special, portals = load_level(level_path)
    
    tiles = {}
    for i in range(len(tile_order)):
        key = tile_order[i]
        tiles[key] = i
    
    special_tile_numbers_table_size = visibility_table_size = maximum_number_of_special_tiles
    
    portal_table_size = 3 * maximum_number_of_portals
    row_table_size = (16 * 2)
    
    # Convert the level descriptions into level data that can be encoded into
    # a form the game can use.
    level_data, monster_data, portal_locations = create_level_data(levels, tiles, special, portals)
    
    data = ""
    row_addresses = []
    
    r = 0
    for row in level_data:
    
        row_addresses.append(levels_address + special_tile_numbers_table_size + \
                             visibility_table_size + portal_table_size + \
                             row_table_size + len(data))
        row_data = ""
        
        for tile, number in row:
        
            # Split the span into pieces if it is too large to be
            # represented by a single byte. Each span length is reduced by 1
            # to enable a larger range of values to be represented. (There
            # are no zero length spans.)
            while number > 256:
            
                row_data += chr(tile) + chr(255)
                number -= 256
            
            if number > 0:
                row_data += chr(tile) + chr(number - 1)
        
        if len(row_data) >= 512:
            raise LevelError, "Level %i: Row %i too long or too detailed." % (l, r)
        
        used = len(row_data)
        print "%2i: %3i |%s%s|" % (r, used, "#" * (used/8), " " * (64 - (used/8)))
        
        data += row_data
        r += 1
    
    print "%i bytes (%04x) of level data" % (len(data), len(data))
    
    monster_row_address = levels_address + special_tile_numbers_table_size + \
                          visibility_table_size + portal_table_size + \
                          row_table_size + len(data)
    
    monster_row_data = chr(0) + chr(1)
    
    for monster, y, number, axis in monster_data:
    
        # Write spans to fill the space but only include a monster in the first
        # one.
        if monster > 0:
            type_number = (y << 3) | ((monster - 1) << 1) | axis
            if type_number == 0:
                raise LevelError, "Resulting monster type is zero (monster = 0 and y = 0)."
        else:
            type_number = 0
        
        while number > 256:
            monster_row_data += chr(type_number) + chr(255)
            type_number = 0
            number -= 256
        
        if number > 0:
            monster_row_data += chr(type_number) + chr(number - 1)
        
        if len(monster_row_data) >= 512:
            raise LevelError, "Monster data too long."
    
    used = len(monster_row_data)
    print "M:  %3i |%s%s|" % (used, "#" * (used/8), " " * (64 - (used/8)))
    
    data += monster_row_data
    
    # Create a table of special tile numbers and initial visibility values.
    
    special_visibility = dict(map(lambda (c, index, flags): (index, (c, flags)), special.values()))
    initial_visibility = []
    special_tile_numbers = []
    default_tile = [".", 0]
    
    for i in range(16, 16 + special_tile_numbers_table_size):
    
        c, flags_list = special_visibility.get(i, default_tile)
        special_tile_numbers.append(tiles[c])
        
        flags = 0
        for c in flags_list:
            flags = flags | flags_values.get(c, 0)
        
        initial_visibility.append(flags)
    
    special_tiles_table = "".join(map(chr, special_tile_numbers))
    visibility_table = "".join(map(chr, initial_visibility))
    
    portal_numbers = []
    
    for portal in portals:
    
        if portal in portal_locations:
        
            # Each portal definition references its destination.
            index, dest, colour = portals[portal]
            x, y = portal_locations[dest]
            
            # The scroll offset of the portal is 19 cells to the left of the
            # character.
            sx = x - 19
            portal_numbers.append((index, (sx, y)))
        
        else:
            # Fill in a placeholder value.
            index, dest, colour = portals[portal]
            portal_numbers.append((index, (0, 0)))
    
    portal_numbers.sort()
    portal_table = "".join(map(lambda (index, (x, y)):
                               chr(x & 0xff) + chr(x >> 8) + chr(y),
                               portal_numbers))
    portal_table += "\x00" * ((3 * maximum_number_of_portals) - len(portal_table))
    
    # Create a table of row offsets.
    table = "".join(map(lambda x: chr(x & 0xff), row_addresses)) + \
            "".join(map(lambda x: chr(x >> 8), row_addresses))
    
    # Append the data to the table of row offsets.
    data = special_tiles_table + visibility_table + portal_table + table + data
    
    return data, monster_row_address
