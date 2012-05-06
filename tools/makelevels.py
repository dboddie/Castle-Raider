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
            "+": "images/grass.png",
            "=": "images/floor-middle.png",
            "#": "images/ground.png",
            "X": "images/rock.png",
            "-": "images/floor.png",
            "|": "images/door.png",
            "/": "images/window-topleft.png",
            "\\": "images/window-topright.png",
            "[": "images/brick-left.png",
            "]": "images/brick-right.png",
            "{": "images/stalactite.png",
            "?": "images/flag.png",
            "I": "images/gate.png",
            "%": "images/foliage.png",  # End of scenery tile sprites
                                        # Start of collectable item sprites
            "K": "images/key.png",
            "L": "images/key1.png",
            "M": "images/key2.png",
            "N": "images/key3.png",
            "A": "images/axe.png",
            "C": "images/crown-left.png",
            "D": "images/crown-right.png",
            "E": "images/chest-left.png",
            "F": "images/chest-right.png"}

tile_order = (".", "@", "+", "=", "#", "X", "-", "|",
              "/", "\\", "[", "]", "{", "?", "I", "%",
              # Collectable items after the first 16 tiles are ignored by
              # the editor.
              "K", "L", "M", "N", "A", "C", "D", "E", "F")

flags_values = {"visible": 0x80, "collectable": 0x40, "door": 0x20, "treasure": 0x10}

def load_level(path):

    lines = map(lambda x: x.rstrip(), open(path).readlines())
    level = lines[:16]
    
    # The special dictionary maps symbols used in the level map to tuples
    # containing corresponding tiles and indices. Each index is an offset into
    # the visibility table, the initial values for which are below.
    special = {}
    index = 16
    for line in lines[16:]:
    
        if line:
            ch, tile, flags_word = line.split()
            flags = 0
            for c in flags_word.split(","):
                flags = flags | flags_values.get(c, 0)
            special[ch] = (tile, index, flags)
            index += 1
    
    return level, special

def create_level_data(level, tiles):

    data = []
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
    
    return data

def create_level(tile_paths, levels_address, level_path, number_of_special_tiles):

    global level, special
    
    level, special = load_level(level_path)
    
    tiles = {}
    for key, value in tile_ref.items():
        tiles[key] = tile_paths.index(value)
    
    special_tile_numbers_table_size = visibility_table_size = number_of_special_tiles
    row_table_size = (16 * 2)
    
    data = ""
    
    level_data = create_level_data(level, tiles)
    row_addresses = []
    
    r = 0
    for row in level_data:
    
        row_addresses.append(levels_address + special_tile_numbers_table_size + visibility_table_size + row_table_size + len(data))
        row_data = ""
        
        for tile, number in row:
        
            # Split the span into pieces if it is too large to be
            # represented by a single byte. Each span length is reduced by 1
            # to enable a larger range of values to be represented. (There
            # are no zero length spans.)
            while number > 256:
            
                row_data += chr(tile) + chr(255)
                number -= 256
            
            if number >= 0:
                row_data += chr(tile) + chr(number - 1)
        
        if len(row_data) >= 512:
            raise LevelError, "Level %i: Row %i too long or too detailed.\n" % (l, r)
        
        data += row_data
        r += 1
    
    print "%i bytes (%04x) of level data" % (len(data), len(data))
    
    # Create a table of special tile numbers and initial visibility values.
    
    special_visibility = dict(map(lambda (c, index, flags): (index, (c, flags)), special.values()))
    initial_visibility = []
    special_tile_numbers = []
    default_tile = [".", 0]
    
    for i in range(16, 16 + special_tile_numbers_table_size):
    
        c, flags = special_visibility.get(i, default_tile)
        special_tile_numbers.append(tiles[c])
        initial_visibility.append(flags)
    
    special_tiles_table = "".join(map(chr, special_tile_numbers))
    visibility_table = "".join(map(chr, initial_visibility))
    
    # Create a table of row offsets.
    table = "".join(map(lambda x: chr(x & 0xff), row_addresses)) + \
            "".join(map(lambda x: chr(x >> 8), row_addresses))
    
    # Append the data to the table of row offsets.
    data = special_tiles_table + visibility_table + table + data
    
    return data
