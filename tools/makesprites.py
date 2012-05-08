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

import Image

palette = {"\x00\x00\x00": 0,
           "\xff\x00\x00": 1,
           "\x00\xff\x00": 2,
           "\xff\xff\x00": 3,
           "\x00\x00\xff": 1,
           "\xff\x00\xff": 2,
           "\x00\xff\xff": 2,
           "\xff\xff\xff": 3}

def read_png(path):

    im = Image.open(path).convert("RGB")
    s = im.tostring()
    
    data = []
    a = 0
    
    i = 0
    while i < im.size[1]:
    
        line = []
        
        j = 0
        while j < im.size[0]:
        
            line.append(palette[s[a:a+3]])
            a += 3
            j += 1
        
        i += 1
        data.append(line)
    
    return data

def read_sprite(lines, shifted = False):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):
    
        if shifted:
            width = len(lines[0]) + 4
        else:
            width = len(lines[0])
        
        # Read 4 columns at a time.
        for column in range(0, width, 4):
        
            # Read the rows.
            for line in lines[row:row + 8]:
            
                if shifted:
                    line = [0, 0] + line + [0, 0]
                
                shift = 3
                byte = 0
                for pixel in line[column:column + 4]:
                
                    if pixel == 1:
                        byte = byte | (0x01 << shift)
                    elif pixel == 2:
                        byte = byte | (0x10 << shift)
                    elif pixel == 3:
                        byte = byte | (0x11 << shift)
                    
                    shift -= 1
                
                data += chr(byte)
    
    return data

def read_tile_data(sprites):

    """Creates edges and rotated versions of original sprites, appending the
    new versions to the list, and returning a string containing the data.
    """
    number = len(sprites)
    
    # Add left edge sprites for bank 2.
    for i in range(number):
    
        sprite = sprites[i]
        
        lines = []
        for i in range(len(sprite)):
        
            right_line = sprite[i]
            lines.append([0] * (len(right_line)/2) + right_line[:len(right_line)/2])
        
        sprites.append(lines)
    
    # Add rotated sprites for bank 2.
    for i in range(number):
    
        sprite = sprites[i]
        
        lines = []
        for j in range(len(sprite)):
        
            line = sprite[j]
            lines.append(line[len(line)/2:] + line[:len(line)/2])
        
        sprites.append(lines)
    
    # Add right edge sprites for bank 2.
    for i in range(number):
    
        sprite = sprites[i]
        
        lines = []
        for i in range(len(sprite)):
        
            left_line = sprite[i]
            lines.append(left_line[len(left_line)/2:] + [0] * (len(left_line)/2))
        
        sprites.append(lines)
    
    data = ""
    for lines in sprites:
    
        data += read_sprite(lines)
    
    print "%i bytes (%04x) of tile data" % (len(data), len(data))
    
    return data

def read_tiles(paths):

    sprites = []
    for path in paths:
    
        sprites.append(read_png(path))
    
    return sprites

def read_sprites(paths, base_address = 0):

    sprites = []
    for path in paths:
    
        sprites.append(read_png(path))
    
    data = ""
    addresses = []
    for lines in sprites:
    
        addresses.append(base_address + len(data))
        data += read_sprite(lines)
    
    print "%i bytes (%04x) of sprite data" % (len(data), len(data))
    
    return data, addresses

def read_shifted_sprites(paths, base_address = 0):

    sprites = []
    for path in paths:
    
        sprites.append(read_png(path))
    
    data = ""
    addresses = []
    for lines in sprites:
    
        addresses.append(base_address + len(data))
        data += read_sprite(lines, shifted = True)
    
    print "%i bytes (%04x) of sprite data" % (len(data), len(data))
    
    return data, addresses
