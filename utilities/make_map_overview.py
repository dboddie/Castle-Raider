#!/usr/bin/env python

"""
Copyright (C) 2012 David Boddie <david@boddie.org.uk>

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

import os, sys
import Image

from tools import makelevels

colours = {
    "black": (0,0,0),
    "red": (255,0,0),
    "green": (0,255,0),
    "yellow": (255,255,0),
    "blue": (0,0,255),
    "magenta": (255,0,255),
    "cyan": (0,255,255),
    "white": (255,255,255)
    }

if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 3:
    
        sys.stderr.write("Usage: %s <output directory> [level file]\n" % sys.argv[0])
        sys.exit(1)
    
    output_dir = sys.argv[1]
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    palette = {colours["black"]: 0,
               colours["red"]: 1,
               colours["green"]: 2,
               colours["yellow"]: 3}
    
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
        #tile_image.putpalette(black + red + green + yellow)
        tile_images[key] = tile_image
    
    monster_images = {}
    for key, path in makelevels.monster_ref.items():
    
        im = Image.open(path)
        im = im.convert("RGB")
        s = im.tostring()
        
        n = ""
        i = 0
        while i < len(s):
        
            v = tuple(map(ord, s[i:i+3]))
            n += chr(palette[v]) + chr(palette[v])
            i += 3
        
        image = Image.fromstring("P", (8 * 2, 8), n)
        #tile_image.putpalette(black + red + green + yellow)
        monster_images[key] = image
    
    if len(sys.argv) == 2:
        level_file = "levels/default.txt"
    else:
        level_file = sys.argv[2]
    
    levels, special, portals, finish = makelevels.load_level(level_file)
    
    for name, rows in levels:
    
        width = 0
        height = len(rows) + 6
        
        for row in rows:
            width = max(len(row), width)
        
        level_image = Image.new("P", (width * 4 * 2, height * 8), 0)
        
        y = 8 * 6
        colours_used = {}
        
        for row in rows:
        
            x = 0
            was_monster = False
            for tile in row:
            
                skip = False
                
                if tile in monster_images:
                    image = monster_images[tile]
                    level_image.paste(image, (x, y))
                    was_monster = True
                
                elif was_monster:
                    # Skip this cell if we just plotted a monster.
                    was_monster = False
                    skip = True
                
                elif tile in special:
                    n, flags, initial = special[tile]
                    if initial:
                        tile = n
                    else:
                        tile = "."
                
                elif tile in portals:
                    portal_colour = portals[tile][-1]
                    colours_used.setdefault(portal_colour, []).append(x)
                    tile = "."
                
                if not skip and tile in tile_images:
                    image = tile_images[tile]
                    level_image.paste(image, (x, y))
                
                x += 4 * 2
            
            y += 8
        
        for portal_colour in colours_used.keys():
        
            level_image.putpalette(
                colours["black"] + colours["red"] + \
                colours[portal_colour] + colours["yellow"]
                )
            
            if len(colours_used) > 1:
                file_name = "%s-%s.png" % (name, portal_colour)
            else:
                file_name = "%s.png" % name
            
            level_image.save(os.path.join(output_dir, file_name))
    
    sys.exit()
