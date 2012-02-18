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

levels = [
    [r".................................................................................................................................................................................@@..@@..@@.............................................................................................................................................................@",
     r".................................................................................................................................................................................@@@@@@@@@@.............................................................................................................................................................@",
     r".................................................................................................................................................................................@@@@@@@@@@.............................................................................................................................................................@",
     r"...............................................................................................................?.................................................................@@@]..[@@@.............................................................@@..@@..@@......................................................................................@",
     r".............................................................................@@..@@...........................@@..@@.............................................................@@@@@@@@@@.............................................................@@@@@@@@@@......................................................................................@",
     r".............................................................................@@@@@@...........................@@@@@@.............................................................@@@@@@@@@@.............................................................@...............................................................................................@",
     r"................@@..@@..@@..@@...............................................@]..[@...........................@]..[@....................................................................................................................................@.............@@@@..............................................................................@",
     r"................@@@@@@@@@@@@@@...............................................@@@@@@...........................@@@@@@....................................................................................................................................@.............@@@@..............................................................................@",
     r".................@@@@@@@@@@@@................................................@@@@@@...........................@@@@@@..................................................................................................................................@@@@@@@@@@@@@@@@@@@@..............................................................................@",
     r".................@@@..................................................................................................................................................................................................................................@@................................................................................................@",
     r"..................|............................................................................................................................+@@@@@@@@@@@]--------------------[@@@@@@@@@@@+.........................................................@@................................................................................................@",
     r"..................|..........................................................................................................................++#@@@@@@@@@@@@....................@@@@@@@@@@@@#+........................................................@@................................................................................................@",
     r"..................|.........................................................@@@@@@@@.........................@@@@@@@@.....................+++###@@@@@/\@@@@@....................@@@@@/\@@@@@##++........................................................................................................................................................@",
     r"..................|.......................................................@@@@@@@@@@@@+++++++++++++++++++++@@@@@@@@@@@@..................+######@@@@]..[@@@@....................@@@@]..[@@@@####+++~++++++++++++++++++++++++++++++++++~++++++...........................................................................................................@",
     r".................@@@@@@@@@@@@...........................................@@@@@@@@@@@@@@#####################@@@@@@@@@@@@@@++++++++++++++++#######@@@@]..[@@@@....................@@@@]..[@@@@#################################################++++++.....................................................................................................@",
     r"+++@@------------@@@@@@@@@@@@++++++++~++++++++++++++++++++++++++++++~+++@@@@@@@@@@@@@@#####################@@@@@@@@@@@@@@#######################@@@@@@@@@@@@....................@@@@@@@@@@@@#######################################################+++@@@@@@@@@@@@@@@@@@@@++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++@"]
    ]

tile_ref = {".": "images/blank.png",
            "@": "images/brick.png",
            "+": "images/grass.png",
            "~": "images/grass2.png",
            "#": "images/ground.png",
            "%": "images/ground2.png",
            "-": "images/floor.png",
            "|": "images/door.png",
            "/": "images/window-topleft.png",
            "\\": "images/window-topright.png",
            "[": "images/brick-left.png",
            "]": "images/brick-right.png",
            "{": "images/rope.png",
            "?": "images/flag.png"}

# The triggers dictionary maps each symbol used in the level map to a tuple
# containing the corresponding tile and action group.
triggers = {"a": "^",
            "b": "*",
            "c": "=",
            "d": "^",
            "e": "'"}

def create_level_data(level, tiles):

    triggers_dict = {}
    used_triggers = {}
    
    for trigger, ch in triggers.items():
    
        # Each time a tile is used in a trigger, ensure that the next one is
        # given a different action number.
        
        value = used_triggers.setdefault(ch, 0)
        triggers_dict[trigger] = (ch, value)
        
        used_triggers[ch] += 1
    
    data = []
    l = 0
    
    for line in level:
    
        line_data = []
        current = None
        offset = 0
        i = 0
        while i < len(line):
        
            ch = line[i]
            c = tiles[ch]
            
            if c != current:
            
                if current is not None:
                
                    # Store the tile offset and length of the tile span,
                    # reduced by one to increase the range of tiles that can be
                    # described.
                    line_data.append((current << 3, i - offset - 1))
                
                current = c
                offset = i
            
            i += 1
        
        if i > offset:
            line_data.append((current, i - offset))
        
        data.append(line_data)
        l += 1
    
    return data

def create_levels(tile_paths, levels_address):

    tiles = {}
    for key, value in tile_ref.items():
        tiles[key] = tile_paths.index(value)
    
    data = ""
    
    l = 0
    for level in levels:
    
        level_data = create_level_data(level, tiles)
        row_addresses = []
        
        r = 0
        for row in level_data:
        
            row_addresses.append(levels_address + (16 * 2) + len(data))
            row_data = ""
            
            for tile, number in row:
            
                if number > 256:
                    raise LevelError, "Level %i: Row %i has a span longer than 256 tiles.\n" % (l, r)
                
                row_data += chr(tile) + chr(number)
            
            if len(row_data) >= 512:
                raise LevelError, "Level %i: Row %i too long or too detailed.\n" % (l, r)
            
            data += row_data
            r += 1
        
        l += 1
    
    print "%i bytes (%04x) of level data" % (len(data), len(data))
    
    # Create a table of row offsets.
    table = "".join(map(lambda x: chr(x & 0xff), row_addresses)) + \
            "".join(map(lambda x: chr(x >> 8), row_addresses))
    
    # Append the data to the table of row offsets.
    data = table + data
    
    return data
