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

#               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a               a
levels = [
    [r"........................................................................................................................................................................................................................................................@@..@@......................................................................@@..@@..@@.....",
     r"........................................................................................................................................................................................................................................................@@@@@@......................................................................@@@@@@@@@@.....",
     r"........................................................................................................................................................................................................................................................@]..[@......................................................................@@@@@@@@@@.....",
     r"................................................................................................................................................................................................@@..@@..@@..@@..@@..@@..@@..............................@@@@@@......................................................................@@@]..[@@@.....",
     r".............................................................................@@..@@.............................................................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@...........@@............@@............@@.................................................................@@@@@@@@@@.....",
     r".............................................................................@@@@@@.............................................................................................................@@......................@@...........@@............@@............@@.................................................................@@@@@@@@@@.....",
     r"................@@..@@..@@..@@...............................................@]..[@.............................................................................................................@@.................................................@@............@@................................................................................",
     r"................@@@@@@@@@@@@@@...............................................@@@@@@.............................................................................................................@@................................................@@@....@@@@@@@@@@................................................................................",
     r".................@@@@@@@@@@@@................................................@@@@@@.............................................................................................................@@.................................................@@..............................................................................................",
     r".................@@@............................................................................................................................................................................@@.........@@@@@@@@@@@@@@@-----------@@............@@..............................................................................................",
     r"..................I.............................................................................................................................................................................@@.......@@.............@@...........@@@@..........@@.............................................++++++++++++]------aaaaaaaa------[@@@@@@@@@@@+...",
     r"..................I.............................................................................................................................................................................@@.....@@...............@@...........@@@@@@aaaaaaaa@@@@@@@@@@@@@@@@@@@@aaaaaa@@+++++++++++++++++++############@....................@@@@@@@@@@@@#+..",
     r"..................I.........................................................@@@@@@@@.....................................................................................................................................................@@@@................................@@###############################@....................@@@@@/\@@@@@##++",
     r"..................I.......................................................@@@@@@@@@@+++++++++++++++++++++++++++++++++++++++++++++++++++++++++~++++++++++++++++++++++++++++++++++~++++++....................................................@@@@............................@@@@###############################@....................@@@@]..[@@@@####",
     r".................@@@@@@@@@@@@...........................................@@@@@@@@@@@@###################################################################################################++++++................................................@@@@........................@@@@@@###############################@....................@@@@]..[@@@@####",
     r"+++@@------------@@@@@@@@@@@@++++++++~++++++++++++++++++++++++++++++~+++@@@@@@@@@@@@#########################################################################################################+++@@@@@@@@@@@@@@@@@@@@@@@@@@+++++++++++@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@###############################@....................@@@@@@@@@@@@####"]
    ]

tile_ref = {".": "images/blank.png",
            "@": "images/brick.png",
            "+": "images/grass.png",
            "~": "images/grass2.png",
            "#": "images/ground.png",
            "X": "images/rock.png",
            "-": "images/floor.png",
            "|": "images/door.png",
            "/": "images/window-topleft.png",
            "\\": "images/window-topright.png",
            "[": "images/brick-left.png",
            "]": "images/brick-right.png",
            "{": "images/rope.png",
            "?": "images/flag.png",
            "I": "images/gate.png",
            "%": "images/foliage.png"}

# The special dictionary maps symbols used in the level map to tuples
# containing corresponding tiles and flags.
special = {"a": ("@", 1)}

# Initial visibility of special tiles. (The 0 entry is for normal tiles.)
initial_special = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

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
                n, flags = special[ch]
                c = tiles[n] | (flags << 4)
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
        
        l += 1
    
    print "%i bytes (%04x) of level data" % (len(data), len(data))
    
    # Create a table of row offsets.
    table = "".join(map(lambda x: chr(x & 0xff), row_addresses)) + \
            "".join(map(lambda x: chr(x >> 8), row_addresses))
    
    # Append the data to the table of row offsets.
    data = table + data
    
    return data
