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

levels = [
    [r"#################...........................................................................................................................................................................@@..@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@...............................................................................################............@@@@################............@@@@",
     r"######%###########................................................................................................................@@..@@..@@..@@..@@..@@..@@..@@............................@@..@@@@@@@@@@@@@@@@@............@@@@@..............................................................................................################............@@@@################............@@@@",
     r"############%#####...........................................................@@..@@...............................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@............................@@@@@@@@@@@@@@@@@@@@...............|................................................................................................################............@@@@################............@@@@",
     r"###.##############...........................................................@@@@@@...............................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@............................@@@@@@@@@@@@@@@@@@@@...............|................................................................................................################............@@@@################............@@@@",
     r"##################...........................................................@]..[@...............................................@@@@@]..[@@@@]..[@@@@]..[@@@@@...............................................................|................................@@@.@@@.@@@.@@@.@@@.@@@.@@@.@@@.@@@.............................################............@@@@################............@@@@",
     r"##%###############...........................................................@@@@@@...............................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@...............................................................|................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@..............................################............@@@@################............@@@@",
     r"###########%######+..........................................................@@@@@@...............................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@............................................................@@@@@@@.............................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@.........@@.....................################............@@@@################............@@@@",
     r"####%##############...................................................................................................................................................................-----[@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@......................................................@@.......................################............@@@@################............@@@@",
     r"###################...........................................................................................................................................................................................................@@@................@@@.................................................@@.........................################............@@@@################............@@@@",
     r"%%#################.................................................................................................................................................................................................................................@@@............................................@@...........................################............@@@@################............@@@@",
     r"########.##########..............................................................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@]----------------[+.....................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@.@@.............................################............@@@@################............@@@@",
     r"#######.######%####...........................................................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@................@@++............................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@................................################............@@@@################............@@@@",
     r"###%###############........................................................++@@@@@@++......................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@................@@##++..........................................................................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@................................################............@@@@################............@@@@",
     r"###################...................................................+++++##@@@@@@##+++................................@@@@@@@@@@@@@@@@@@@@@@@@@/\@@@@@@@@@@@@@................@@####+++~+++++++++++++++++~++~+++++++++++++++@@@...............................@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@++++++++++++++++++++++++++++++++################............@@@@################............@@@@",
     r"#########%%%#######.........................................+++~++++++##################+++++++~++++++++++++++++++++~+++@@@@@@@@@@@@@@@@@@@@@@@@]..[@@@@@@@@@@@@................@@############################################@@@...+++....+++..................@@@@@@@@@@@@@@@@@@@..@@@@@@@@@@@################################################............@@@@################............@@@@",
     r"##%################+++++~++++++++++++~+++++++++~++++++++++++############################################################@@@@@@@@@@@@@@@@@@@@@@@@]..[@@@@@@@@@@@@................@@############################################@@@...###....###....@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@################################################............@@@@################............@@@@"]
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
            "S": "images/rope.png"}

def create_level_data(level, tile_paths):

    tiles = {}
    for key, value in tile_ref.items():
    
        tiles[key] = tile_paths.index(value)
    
    data = []
    
    for line in level:
    
        line_data = []
        previous = 0
        current = None
        offset = 0
        i = 0
        while i < len(line):
        
            c = tiles[line[i]]
            if c != current:
            
                if current is not None:
                
                    # Append the previous type and number of tiles to the data.
                    line_data.append(((previous, current), i - offset))
                    
                    previous = current
                
                current = c
                offset = i
            
            i += 1
        
        if i > offset:
            line_data.append(((previous, current), i - offset))
        
        data.append(line_data)
    
    return data

def create_levels(tile_paths):

    data = ""
    
    l = 0
    for level in levels:
    
        level_data = create_level_data(level, tile_paths)
        row_offsets = []
        
        r = 0
        for row in level_data:
        
            row_offsets.append(len(data))
            row_data = ""
            
            for (previous, current), number in row:
            
                if number > 256:
                    raise LevelError, "Level %i: Row %i has a span longer than 256 tiles.\n" % (l, r)
                
                tile = (current & 0xff)
                row_data += chr(tile) + chr(number - 1)
            
            if len(row_data) >= 512:
                raise LevelError, "Level %i: Row %i too long or too detailed.\n" % (l, r)
            
            data += row_data
            r += 1
        
        l += 1
    
    print "%i bytes of level data" % len(data)
    
    # Create a table of row offsets.
    table = "".join(map(lambda x: chr(x & 0xff), row_offsets)) + \
            "".join(map(lambda x: chr(x >> 8), row_offsets))
    
    # Append the data to the table of row offsets.
    data = table + data
    
    return data
