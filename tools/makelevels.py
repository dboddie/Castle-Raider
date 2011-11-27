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

levels = [
    ["................................................................",
     ".+++++.@...+..@@...+..++..........+....@@...++..@...............",
     "...+...@.....@.......+......@@@...+...@..@.+....@...............",
     "...+...@@@.+..@@...+..++...@..@...+++.@@@...++..@@@.............",
     "...+...@.@.+....@..+....+..@..@...+...@.......+.@...............",
     "...+...@.@.+..@@...+..++....@@.@...++..@@...++...@@.............",
     "................................................................",
     "................................................................",
     "................................................................",
     "................................................................",
     ".............................++++++++...........................",
     ".............................@@@@@@@@...........................",
     "..........+...........@@@@...@.@@@@.@...........................",
     ".........+++...@@@@....++....@@@..@@@...........................",
     "......++++++++.........++....@@@..@@@...........................",
     "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"]
    ]

tiles = {".": 0, "@": 1, "+": 2}

def create_level_data(level):

    data = []
    merged_tiles = set()
    
    for line in level:
    
        line_data = []
        current = 0
        i = 0
        while i < len(line):
        
            c = tiles[line[i]]
            if c != current:
            
                line_data.append((i, c))
                merged_tiles.add((current, c))
                
                current = c
            
            i += 1
        
        line_data.append((i, c))
        
        data.append(line_data)
    
    return data, merged_tiles

def create_levels():

    data = ""
    all_merged_tiles = set()
    
    for level in levels:
    
        level_data, merged_tiles = create_level_data(level)
        all_merged_tiles.update(merged_tiles)
        
        row_offsets = []
        
        for row in level_data:
        
            row_offsets.append(len(data)/2)
            
            for offset, tile in row:
            
                data += chr(offset) + chr(tile)
    
    print "%i bytes of level data" % len(data)
    
    print row_offsets
    # Create a table of row offsets.
    table = "".join(map(chr, row_offsets))
    
    # Append the data to the table of row offsets.
    data = table + data
    
    return data, all_merged_tiles
