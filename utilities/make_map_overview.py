#!/usr/bin/env python

import os, sys
import Image

from tools import makelevels

if __name__ == "__main__":

    if len(sys.argv) != 2:
    
        sys.stderr.write("Usage: %s <image file>\n" % sys.argv[0])
        sys.exit(1)
    
    output_path = sys.argv[1]
    
    level = makelevels.level
    
    width = 0
    height = len(level) + 6
    
    for row in level:
        width = max(len(row), width)
    
    level_image = Image.new("P", (width * 4 * 2, height * 8), 0)
    
    black = (0,0,0)
    red = (255,0,0)
    green = (0,255,0)
    yellow = (255,255,0)
    level_image.putpalette(black + red + green + yellow)
    
    palette = {black: 0, red: 1, green: 2, yellow: 3}
    
    tile_images = {}
    for key, path in makelevels.tile_ref.items():
    
        im = Image.open(path)
        im = im.convert("RGB")
        s = im.tostring()
        
        n = ""
        i = 0
        while i < len(s):
        
            v = tuple(map(ord, s[i:i+3]))
            n += chr(palette[v]) + chr(palette[v])
            i += 3
        
        tile_image = Image.fromstring("P", (4 * 2, 8), n)
        tile_image.putpalette(black + red + green + yellow)
        tile_images[key] = tile_image
    
    y = 8 * 6
    for row in level:
    
        x = 0
        for tile in row:
        
            if tile in makelevels.special:
                n, flags, initial = makelevels.special[tile]
                if initial:
                    tile = n
                else:
                    tile = "."
            
            tile_image = tile_images[tile]
            level_image.paste(tile_image, (x, y))
            
            x += 4 * 2
        
        y += 8
    
    level_image.save(output_path)
    sys.exit()
