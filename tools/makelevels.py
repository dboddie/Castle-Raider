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
    [r"#######++++++........................................................................................................................................................@@..@@..@@.............................................................................................................................................................@",
     r"#############++......................................................................................................................................................@@@@@@@@@@.............................................................................................................................................................@",
     r"##########%####..............................................................@@..@@..................................................................................@@@@@@@@@@.............................................................................................................................................................@",
     r"################.............................................................@@@@@@..................................................................................@@@]..[@@@.............................................................@@..@@..@@......................................................................................@",
     r"################.............................................................@]..[@..................................................................................@@@@@@@@@@.............................................................@@@@@@@@@@......................................................................................@",
     r"#################............................................................@@@@@@..................................................................................@@@@@@@@@@.............................................................C........C......................................................................................@",
     r"#################............................................................@@@@@@.........................................................................................................................................................C........C....@@@@..............................................................................@",
     r"####%############.............................................................E.............................................................................................................................................................C........C....@@@@..............................................................................@",
     r"##################............................................................E...........................................................................................................................................................@@@@@@@@@@@@@@@@@@@@..............................................................................@",
     r"##################+.......................................@@@@................E...............................................................................................................................@@....@@....................@@................................................................................................@",
     r"###################................................................@@@@@....@@@@@@@@...............................................+@@@@@@@@@@@]-------AAAAAA-------[aaaaaaaaaaa+.............................@@-DDD@@....................@@................................................................................................@",
     r"#######%###########.................................@@@.....................@@@@@@@@.............................................++#@@@@@@@@@@@@....................@@@@@@@@@@@@#+............................@@....@@...................B@@................................................................................................@",
     r"###################.........................................................@@@@@@@@#.........................................+++###@@@@@/\@@@@@....................@@@@@/\@@@@@##++........................@@@@....@@@@....................................................................................................................@",
     r"###################...........................@@@@..........................@@@@@@@@#+++...................................+++######@@@@]..[@@@@....................@@@@]..[@@@@####+++~++++++++++++++++++++@@@@....@@@@++~++++++...........................................................................................................@",
     r"###################...........................####..........................@@@@@@@@####+++++++~++++++++++++++++++++~++++++#########@@@@]..[@@@@....................@@@@]..[@@@@##################################b##############++++++.....................................................................................................@",
     r"###################+++++~++++++++++++~++++++++####+++++++++++++++++++++++ee+########################################################@@@@@@@@@@@@....................@@@@@@@@@@@@#######################################################+++@d@@@@@@@@@@c@@@@@@@++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++@"]
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
            "?": "images/flag.png",
            "^": "images/brick-trigger0.png",
            "=": "images/brick-trigger1.png",
            "*": "images/ground-trigger2.png",
            "'": "images/grass-trigger3.png"}

# The triggers dictionary maps each symbol used in the level map to a tuple
# containing the corresponding tile and action group.
triggers = {"a": "^",
            "b": "*",
            "c": "=",
            "d": "^",
            "e": "'"}

# The spans dictionary maps each symbols used in the level map to a pair of tiles used for
# the initial and final states of that action.
spans = {"A": ("-", "."),
         "B": (".", "@"),
         "C": ("@", "."),
         "D": ("-", "."),
         "E": ("|", ".")}

def create_level_data(level, tiles):

    triggers_dict = {}
    used_triggers = {}
    
    for trigger, ch in triggers.items():
    
        # Each time a tile is used in a trigger, ensure that the next one is
        # given a different action number.
        
        value = used_triggers.setdefault(ch, 0)
        triggers_dict[trigger] = (ch, value)
        
        used_triggers[ch] += 1
    
    actions_dict = {}
    data = []
    l = 0
    
    for line in level:
    
        line_data = []
        current = None
        offset = 0
        i = 0
        while i < len(line):
        
            ch = line[i]
            try:
                c = tiles[ch]
            
            except KeyError:
            
                # Check for a predefined trigger or span.
                if triggers_dict.has_key(ch):
                
                    # Use the tile mapped to by the trigger dictionary, setting
                    # one or more of the top 4 bits to indicate that the span
                    # contains a trigger.
                    tile, group = triggers_dict[ch]
                    c = tiles[tile] | (group << 5)
                
                elif spans.has_key(ch):
                
                    # Use the first tile in the action.
                    c = ch
                
                else:
                    raise
            
            if c != current:
            
                if isinstance(current, str):
                
                    tile, group = triggers_dict[current.lower()]
                    number = (tiles[tile] | (group << 5))
                    number = (number & 0x0f) | ((number & 0xe0) >> 1)
                    
                    action = actions_dict.setdefault(number, Action())
                    action.initial = tiles[spans[current][0]]
                    action.final = tiles[spans[current][1]]
                    action.spans.add((l, len(line_data)))
                    
                    current = action.initial
                
                if current is not None:
                
                    # Store the length of the tile span, reduced by one to
                    # increase the range of tiles that can be described.
                    line_data.append((current, i - offset - 1))
                
                current = c
                offset = i
            
            i += 1
        
        if i > offset:
            line_data.append((current, i - offset))
        
        data.append(line_data)
        l += 1
    
    return data, actions_dict

def create_levels(tile_paths, levels_address):

    tiles = {}
    for key, value in tile_ref.items():
    
        tiles[key] = tile_paths.index(value)
    
    data = ""
    
    l = 0
    for level in levels:
    
        level_data, actions_dict = create_level_data(level, tiles)
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
    
    # Actions are stored as a table of addresses followed by the actions
    # themselves. Even though
    
    actions_list = actions_dict.items()
    actions_list.sort()
    actions = max(actions_dict.keys()) + 1
    
    actions_table = ""
    actions_data = ""
    actions_table_length = actions * 2
    actions_start_address = levels_address + len(data) + actions_table_length
    
    number = 0
    while number < actions:
    
        try:
            action = actions_dict[number]
        except KeyError:
            actions_table += chr(0) + chr(0)
            number += 1
            continue
        
        # Store the spans described in the action in the following format:
        # <original tile type>, <replacement tile type>,
        # <number of spans, n>,
        # <address 0>, ... <address n - 1>
        
        original_tile_type = action.initial
        replacement_tile_type = action.final
        number_of_spans = len(action.spans)
        
        addresses = []
        
        for span in action.spans:
        
            line, offset = span
            address = row_addresses[line] + offset*2
            addresses += chr(address & 0xff) + chr(address >> 8)
        
        action_address = actions_start_address + len(actions_data)
        actions_table += chr(action_address & 0xff) + chr(action_address >> 8)
        
        actions_data += chr(original_tile_type) + chr(replacement_tile_type) + \
                        chr(number_of_spans) + "".join(addresses)
        
        number += 1
    
    actions_data = actions_table + actions_data
    
    print "%i bytes (%04x) of actions data" % (len(actions_data), len(actions_data))
    
    return data, actions_data
