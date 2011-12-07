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


def read_sprite(lines):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):
    
        # Read 4 columns at a time.
        for column in range(0, len(lines[0]), 4):
        
            # Read the rows.
            for line in lines[row:row + 8]:
            
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

def make_scanline_bytes(lines):

    data = []
    for line in lines:
    
        line_data = ""
        # Read 4 columns at a time.
        for column in range(0, len(lines[0]), 4):
        
            shift = 3
            byte = 0
            for pixel in line[column:column + 4]:
            
                if pixel == "1":
                    byte = byte | (0x01 << shift)
                elif pixel == "2":
                    byte = byte | (0x10 << shift)
                elif pixel == "3":
                    byte = byte | (0x11 << shift)
                
                shift -= 1
            
            line_data += chr(byte)
        
        data.append(line_data)
    
    return data

def compress(data):

    output = []
    current = None
    length = 0
    
    for byte in data:
    
        if current != byte:
            if length > 0:
                output.append(current + chr(length))
            current = byte
            length = 1
        else:
            length += 1
            if length == 255:
                output.append(current + chr(length))
                length = 0
    
    if length > 0:
        output.append(current + chr(length))
    
    return "".join(output)

def read_tiles(paths, merged_tiles):

    sprites = []
    for path in paths:
    
        sprites.append(read_png(path))
    
    # Add a blank tile at the start of the merged tiles.
    sprites.append([[0]*4]*8)
    
    for left, right in merged_tiles:
    
        left_sprite = sprites[left]
        right_sprite = sprites[right]
        
        lines = []
        for i in range(len(left_sprite)):
        
            left_line = left_sprite[i]
            right_line = right_sprite[i]
            lines.append(left_line[len(left_line)/2:] + right_line[:len(right_line)/2])
        
        sprites.append(lines)
    
    # Add rotated sprites for bank 2.
    for i in range(len(paths)):
    
        sprite = sprites[i]
        
        lines = []
        for j in range(len(sprite)):
        
            line = sprite[j]
            lines.append(line[len(line)/2:] + line[:len(line)/2])
        
        sprites.append(lines)
    
    data = ""
    for lines in sprites:
    
        data += read_sprite(lines)
    
    print "%i bytes of tile data" % len(data)
    
    return data

def read_sprites(paths):

    sprites = []
    for path in paths:
    
        sprites.append(read_png(path))
    
    data = ""
    for lines in sprites:
    
        data += read_sprite(lines)
    
    print "%i bytes of sprite data" % len(data)
    
    return data

def encode(data):

    new_data = ""
    for c in data:
    
        i = ord(c)
        new_data += chr(i & 0x0f) + chr((i & 0xf0) >> 4)
    
    return new_data

def combine(encoded, overlay):

    combined = ""
    offset = 0
    while offset < len(overlay):
        combined += chr(ord(encoded[offset]) | ord(overlay[offset]))
        offset += 1
    
    combined += encoded[offset:]
    return combined
