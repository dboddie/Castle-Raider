#!/usr/bin/env python

"""
Copyright (C) 2014 David Boddie <david@boddie.org.uk>

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

import codecs, os, sys
from PyQt4.QtCore import QSize
from PyQt4.QtGui import *

def relpath(source, destination):

    source = os.path.abspath(source)
    destination = os.path.abspath(destination)
    
    src_pieces = source.split(os.sep)
    dest_pieces = destination.split(os.sep)
    
    if os.path.isfile(source):
        src_pieces.pop()
    
    common = []
    for i in range(min(len(src_pieces), len(dest_pieces))):
    
        if src_pieces[i] == dest_pieces[i]:
            common.append(src_pieces[i])
            i -= 1
        else:
            break
    
    to_common = [os.pardir]*(len(src_pieces)-len(common))
    rel_pieces = to_common + dest_pieces[len(common):]
    return os.sep.join(rel_pieces)


class SVG:

    def __init__(self, path):
    
        self.path = path
    
    def _escape(self, text):
    
        for s, r in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
            text = text.replace(s, r)
        
        return text
    
    def open(self):
    
        self.text = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                     '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
                     '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    
    def add_page(self, width, height):
    
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n'
                      '     width="%fcm" height="%fcm"\n'
                      '     viewBox="0 0 %i %i">\n') % (width/100.0, height/100.0, width, height)
    
    def add_image(self, x, y, width, height, path):
    
        path = os.path.join(relpath(self.path, os.curdir), path)
        self.text += '<image x="%f" y="%f" width="%f" height="%f"\n' % (x, y, width, height)
        self.text += '       xlink:href="%s" />\n' % path
        
    def add_text(self, x, y, font, text):
    
        self.text += '<text x="%f" y="%f"\n' % (x, y)
        self.text += ('      font-family="%s"\n'
                      '      font-size="%i"\n') % (font["family"], font["size"])
        if font.has_key("weight"):
            self.text += '      font-weight="%s"\n' % font["weight"]
        if font.has_key("style"):
            self.text += '      font-style="%s"\n' % font["style"]
        if font.has_key("colour"):
            self.text += '      fill="%s"\n' % font["colour"]
        self.text += '>\n'
        self.text += self._escape(text)
        self.text += '</text>\n'
    
    def close(self):
    
        self.text += "</svg>\n"
        codecs.open(self.path, "w", "utf-8").write(self.text)


class Inlay(SVG):

    def __init__(self, path):
    
        SVG.__init__(self, path)
        
        self.page_offsets = [(0, 0), (650, 0), (2 * 650, 0), (2050, 0)]
        self.page_number = 0
    
    def open(self):
    
        SVG.open(self)
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n'
                      '     width="27.0cm" height="10cm"\n'
                      '     viewBox="0 0 2700 1000">\n')
    
    def add_page(self, width, height):
    
        self.ox, self.oy = self.page_offsets[self.page_number]
        self.text += ('<rect x="%i" y="0" width="0.1" height="1000"\n'
                      '      stroke="black" fill="none" stroke-width="0.1" />\n' % self.ox)
        self.page_number += 1
    
    def add_image(self, x, y, width, height, path):
    
        SVG.add_image(self, self.ox + x, self.oy + y, width, height, path)
    
    def add_text(self, x, y, font, text):
    
        SVG.add_text(self, self.ox + x, self.oy + y, font, text)
    
    def close(self):
    
        self.text += ('<rect x="1950" y="0" width="100" height="1000"\n'
                      '      stroke="black" fill="none" stroke-width="1" />\n')
        
        SVG.close(self)


class Page:

    def __init__(self, size, objects):
    
        self.size = size
        self.objects = objects
    
    def render(self, svg):
    
        svg.add_page(self.size[0], self.size[1])
        
        positions = [(0, 0)]
        for obj in self.objects:
        
            x, y = obj.render(svg, positions)
            positions.append((x, y))
        
        return svg


class TextBox:

    def __init__(self, bbox, text_items, follow = False, index = -1):
    
        self.bbox = bbox
        self.text_items = text_items
        self.follow = follow
        self.index = index
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        for text_item in self.text_items:
        
            left_indent = text_item.font.get("left indent", 0)
            right_indent = text_item.font.get("right indent", 0)
            item_x = x + left_indent
            item_width = width - left_indent - right_indent
            
            for pieces, line_height in text_item.readline(item_width):
            
                for font, word_x, text in pieces:
                
                    svg.add_text(item_x + word_x, y, font, text)
                
                y += line_height
        
        return x, y


class Text:

    def __init__(self, font, text):
    
        self.font = font
        self.text = text
        
        self.parse_text()
    
    def parse_text(self):
    
        lines = self.text.split("\n")
        self.lines = []
        
        for line in lines:
        
            words = []
            for word in line.split():
            
                words.append(Word(self.font, word))
            
            self.lines.append(words)
    
    def readline(self, width):
    
        for line in self.lines:
        
            w = 0
            used = 0
            words = []
            
            while w < len(line):
            
                word = line[w]
                word_width = word.width()
                
                if used + word_width <= width:
                    # Add words while there is still space.
                    used += word_width + word.space()
                    words.append(word)
                    w += 1
                
                elif words:
                    # When out of space, yield the words on the line.
                    yield self.format(words, width), self.height(words)
                    
                    used = 0
                    words = []
                
                else:
                    # If no words will fit on the line, just add the first
                    # word to the list.
                    yield self.format([word], width), self.height(words)
                    
                    used = 0
                    w += 1
            
            if words:
                yield self.format(words, width, last = True), self.height(words)
            elif not line:
                yield [], self.line_height()/2
    
    def format(self, words, width, last = False):
    
        output = []
        x = 0
        
        if len(words) == 0:
            spacing = 0
        
        elif self.font.get("align", "left") == "justify" and not last:
            # Full justify the text.
            total_width = sum(map(lambda word: word.width(), words))
            spacing = (width - total_width)/float(len(words) - 1)
        
        elif self.font.get("align", "left") == "centre":
            # Centre the text.
            total_width = sum(map(lambda word: word.width(), words))
            total_space = sum(map(lambda word: word.space(), words)[:-1])
            x = width/2.0 - total_width/2.0 - total_space/2.0
            spacing = None
        
        else:
            spacing = None
        
        for word in words:
        
            output.append((word._font, x, word.text))
            x += word.width()
            if spacing is not None:
                x += spacing
            else:
                x += word.space()
        
        return output
    
    def height(self, words):
    
        return max(map(lambda word: word.height(), words))
    
    def line_height(self):
    
        font = QFont(self.font.get("family"))
        font.setPixelSize(self.font.get("size"))
        if self.font.get("weight") == "bold":
            font.setWeight(QFont.Bold)
        if self.font.get("style") == "italic":
            font.setItalic(True)
        
        metrics = QFontMetrics(font)
        return metrics.height()


class Word:

    def __init__(self, font, text):
    
        self._font = font
        self.text = text
    
    def font(self):
    
        font = QFont(self._font.get("family"))
        font.setPixelSize(self._font.get("size"))
        if self._font.get("weight") == "bold":
            font.setWeight(QFont.Bold)
        if self._font.get("style") == "italic":
            font.setItalic(True)
        return font
    
    def width(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.width(self.text)
    
    def height(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.height()
    
    def space(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.width(" ")


class Image:

    def __init__(self, bbox, path, scale = None, follow = False, index = -1):
    
        self.bbox = bbox
        self.path = path
        self.follow = follow
        self.index = index
        self.scale = scale
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        im = QImage(self.path)
        width = im.size().width()
        height = im.size().height()
        
        if self.scale:
            width = width * self.scale
            height = height * self.scale
        
        svg.add_image(x, y, width, height, self.path)
        
        return x + width, y + height


class Path:

    def __init__(self, bbox, elements, attributes = None, follow = False,
                 index = -1):
    
        self.bbox = bbox
        self.elements = elements
        self.attributes = attributes
        self.follow = follow
        self.index = index
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        svg.text += "<path "
        path = []
        
        for element in self.elements:
        
            path.append(element[0])
            absolute = element[0] == element[0].upper()
            
            for i in range(1, len(element)):
                if absolute:
                    if i % 2 == 1:
                        path.append(svg.ox + x + element[i])
                    else:
                        path.append(svg.oy + y + element[i])
                else:
                    path.append(element[i])
        
        svg.text += 'd="' + " ".join(map(str, path)) + '"'
        
        if self.attributes:
            for key, value in self.attributes.items():
                svg.text += ' %s="%s"' % (key, value)
        
        svg.text += " />\n"
        
        return x + width, y + height


def curved_box(x, y, w, h, style):

    r = w/10.0
    hr = r/2.0
    ll = w - (4 * r)
    
    return Path((x, y, w, h),
                 [("M",r,0), ("l",ll,0), ("c",hr,0,r,hr,r,r),
                  ("l",0,ll), ("c",0,hr,-hr,r,-r,r),
                  ("l",-ll,0), ("c",-hr,0,-r,-hr,-r,-r),
                  ("l",0,-ll), ("c",0,-hr,hr,-r,r,-r)], style)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if not 2 <= len(app.arguments()) <= 3:
    
        sys.stderr.write("Usage: %s [--inlay] <output directory>\n" % app.arguments()[0])
        sys.exit(1)
    
    if app.arguments()[1] == "--inlay":
        output_dir = sys.argv[2]
        inlay = True
    else:
        output_dir = sys.argv[1]
        inlay = False
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    regular = {"family": "FreeSerif",
               "size": 20,
               "align": "justify"}
    
    title = {"family": "FreeSerif",
             "size": 64,
             "weight": "bold",
             "align": "centre"}
    
    subtitle = {"family": "FreeSerif",
             "size": 22,
             "weight": "bold"}
    
    italic_quote = {"family": "FreeSerif",
                    "size": 22,
                    "style": "italic",
                    "left indent": 40,
                    "right indent": 40}
    
    quote = {"family": "FreeSerif",
             "size": 22,
             "left indent": 40,
             "right indent": 40}
    
    monospace_quote = {"family": "FreeMono",
                       "size": 22,
                       "left indent": 40,
                       "right indent": 40}
    
    keys_quote = {"family": "FreeSerif",
                  "size": regular["size"],
                  "left indent": 40,
                  "right indent": 40}
    
    key_descriptions_quote = {"family": "FreeSerif",
                              "size": regular["size"],
                              "left indent": 160,
                              "right indent": 0}
    
    exclamation = {"family": "FreeSerif",
                   "size": 28,
                   "style": "italic",
                   "weight": "bold",
                   "align": "centre"}

    back_cover_title = {"family": "FreeSerif",
                        "size": 36,
                        "weight": "bold",
                        "align": "centre"}
    
    back_cover_subtitle = {"family": "FreeSerif",
                           "size": 28,
                           "weight": "bold",
                           "align": "centre"}
    
    back_cover_centred = {"family": "FreeSerif",
                          "size": 24,
                          "align": "centre"}
    
    front_cover_publisher1 = {"family": "FreeSans", "size": 32,
                              "weight": "bold", "align": "centre",
                              "colour": "#202020"}
    
    front_cover_publisher2 = {"family": "FreeSans", "size": 32,
                              "weight": "bold", "align": "centre",
                              "colour": "#ffffc0"}
    
    front_cover_platforms = {"family": "FreeSans", "size": 28,
                             "weight": "bold", "align": "centre"}
    
    front_cover_title = {"family": "FreeSans", "size": 52,
                         "weight": "bold", "align": "centre"}
    
    r = 25
    hr = r/2.0
    
    logo = []
    w = h = 50
    cx = 650/2.0
    x = cx - (len("RETRO") * w)/2.0
    y = 25
    lr = 5
    lhr = 2.5
    
    for ch in "RETRO":
        logo.append(curved_box(x, y + lr, w, h,
                               {"fill": "#ff4040", "stroke": "#000000",
                                "stroke-width": 1}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": "#ffffc0", "stroke": "#000000",
                                "stroke-width": 1}))
        logo.append(TextBox((x + lr, y + lr + h/2, w - (lr * 2), h),
                            [Text(front_cover_publisher1, ch)]))
        x += w
    
    x = cx - (len("SOFTWARE") * w)/2.0
    y += h
    
    for ch in "SOFTWARE":
        logo.append(curved_box(x, y + lr, w, h,
                               {"fill": "#ffffc0", "stroke": "#000000",
                                "stroke-width": 1}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": "#202020", "stroke": "#000000",
                                "stroke-width": 1}))
        logo.append(TextBox((x + lr, y + lr + h/2, w - (lr * 2), h),
                            [Text(front_cover_publisher2, ch)]))
        x += w
    
    pages = [
        Page((650, 1000),
            [TextBox((25, 75, 600, 0), 
                 [Text(title, "Castle Raider")]),
             TextBox((25, 0, 600, 0),
                 [Text(regular,
                       "As the sun dips below the ramparts of the old town, the last of the troops file "
                       "in. As they make their way through the narrow, cobbled streets, small groups of "
                       "them quietly slink away into the many taverns that give this district its bad "
                       "reputation. The lamps are lit and the merriment spills out onto the streets "
                       "with laughing, singing, pushing and shoving. There will be trouble later, but "
                       "by then you will be long gone.\n"),
                  Text(regular,
                       "It is time for the guard to change, time for the night watch to begin their "
                       "duties, but they are in no hurry; though the outlaws in the countryside know "
                       "the force stationed here will be no threat tonight, they gave them a wide "
                       "berth during their march here. The people in the nearby villages can sleep "
                       "soundly for a change.\n"),
                  Text(regular,
                       "As the members of the night watch slowly begin to take their places on the "
                       "ramparts you take your chance and slip through the open gate, taking refuge in "
                       "the long shadows fleeing the sunset. The few eyes looking in your direction are "
                       "hardly able to make out your form as you wait for the approaching nightfall.\n"),
                  Text(regular,
                       "You recall the stories told when you were young. When the town itself was "
                       "already old, the last of the elders told of a time when it was still a village, "
                       "not much more than a few houses and shelters. The road that ran through it went "
                       "to the castle on the edge of the wasteland that now lies derelict and deserted.\n"),
                  Text(regular,
                       "Night falls quickly in this season at the edge of the kingdom. Memories of "
                       "fireside tales about the king's lost crown and the hidden treasure of the old "
                       "kingdom make the journey across the plains more bearable. Soon you arrive at "
                       "the outer fortifications. Crossing a bridge, you enter. As you pass beneath the "
                       "outer gate it suddenly crashes into place, cutting off your exit. It was just "
                       "as well you hadn't planned to return that way.\n"),
                  Text(regular,
                       "Nature has reclaimed parts of the castle, its ruins crumbling in places and "
                       "crawling with creatures that people once knew well to leave alone. To make your "
                       "way through it to the lands beyond, you will need to unlock the few doors and "
                       "gates that still stand. Perhaps the folk tales were true and the king's "
                       "treasure still remains, but survival is more important here. If you live to "
                       "pass through the outer gate then the story alone will have made the journey "
                       "worthwhile.")],
                  follow = True)
             ]),
        Page((650, 1000),
             [TextBox((25, 35, 600, 0),
                  [Text(subtitle, "Loading the Game from Cassette\n"),
                   Text(regular, "Insert the cassette and type\n")]),
              TextBox((25, -2, 600, 0),
                  [Text(monospace_quote, 'CHAIN "CASTLE"\n')], follow = True),
              TextBox((25, -2, 600, 0),
                  [Text(regular,
                        "then press Return. Press play on the cassette recorder. "
                        "The game should now load.\n\n")], follow = True),
              
              TextBox((25, 12, 600, 0),
                  [Text(subtitle, "Loading the Game from Disk\n"),
                   Text(regular,
                        "Insert the disk and press Shift-Break. The game should now load.\n")],
                  follow = True),
              
              TextBox((25, 20, 600, 0),
                  [Text(subtitle, "Playing the Game\n"),
                   Text(regular,
                        "The player must help their character escape the castle, "
                        "ideally with some hidden treasure.\n"),
                   Text(regular,
                        "Your character can roam the castle and its surroundings using the following "
                        "control keys:\n")],
                  follow = True),
              TextBox((25, 0, 600, 0),
                  [Text(keys_quote,
                        "Z\n"
                        "X\n"
                        "Return\n"
                        "/")], follow = True),
              TextBox((25, 0, 600, 0),
                  [Text(key_descriptions_quote,
                        "left\n"
                        "right\n"
                        "jump\n"
                        "enter\n"),
                   Text(regular,
                        "The character may enter different parts of the castle by entering the arched "
                        "doorways that can be found in various places. While standing in a doorway, "
                        "press the / key to enter.\n\n"
                        "Alternatively, you may may use an analogue joystick with the following "
                        "controls:\n")],
                        follow = True, index = -2),
              TextBox((25, 0, 600, 0),
                  [Text(keys_quote,
                        "Left\n"
                        "Right\n"
                        "Fire\n"
                        "Down\n")], follow = True),
              TextBox((25, 0, 600, 0),
                  [Text(key_descriptions_quote,
                        "left\n"
                        "right\n"
                        "jump\n"
                        "enter\n"),
                   Text(regular,
                        "Select joystick controls by pressing the Fire button on the title page to start "
                        "the game. Press Space to start the game with keyboard controls.\n\n"
                        "Other keys are used to control features of the game:\n")],
                        follow = True, index = -2),
              TextBox((25, 0, 600, 0),
                  [Text(keys_quote,
                        "S\n"
                        "Q\n"
                        "P\n"
                        "O\n"
                        "Escape")], follow = True),
              TextBox((25, 0, 600, 0),
                  [Text(key_descriptions_quote,
                        "enable sound effects\n"
                        "disable sound effects\n"
                        "pause the game\n"
                        "resume the game\n"
                        "quit the game, returning to the title screen\n")],
                  follow = True, index = -2)
             ]),
        Page((650, 1000),
             [TextBox((25, 50, 600, 0),
                      [Text(back_cover_title, "Castle Raider"),
                       Text(back_cover_subtitle, "for the Acorn Electron and BBC Model B")]),
              Image((24.667, 0, 450, 0), "images/2014-11-30-loading.png", scale = 0.9, follow = True),
              Image((337.334, 0, 450, 0), "images/2014-11-30-action.png", scale = 0.9, follow = True, index = -2),
              Image((24.667, 25, 450, 0), "images/2014-11-30-basement.png", scale = 0.9, follow = True),
              Image((337.334, 25, 450, 0), "images/2014-11-30-dungeon.png", scale = 0.9, follow = True, index = -2),
              TextBox((25, 45, 600, 0),
                      [Text(back_cover_centred,
                            u"Copyright \u00a9 2014 David Boddie\n"
                            u"An Infukor production for Retro Software\n"
                            u"http://www.retrosoftware.co.uk/")], follow = True),
              TextBox((25, 15, 600, 0),
                      [Text(regular,
                            "This program is free software: you can redistribute it and/or modify "
                            "it under the terms of the GNU General Public License as published by "
                            "the Free Software Foundation, either version 3 of the License, or "
                            "(at your option) any later version.\n"
                            "\n"
                            "This program is distributed in the hope that it will be useful, "
                            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
                            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
                            "GNU General Public License for more details.\n"
                            "\n"
                            "You should have received a copy of the GNU General Public License "
                            "along with this program. If not, see <http://www.gnu.org/licenses/>.")],
                      follow = True)
             ]),
        Page((650, 1000),
            [Path((0, 0, 650, 1000),
                  [("M",0,0), ("l",650,0), ("l",0,1000), ("l",-650,0), ("l",0,-1000)],
                  {"fill": "#ffdd77", "stroke": "#000000", "stroke-width": 1}),
             Path((100-hr, 50+hr, 450, 250),
                  [("M",r,0), ("l",450-(r*2),0), ("c",hr,0,r,hr,r,r),
                   ("l",0,250-(r*2)), ("c",0,hr,-hr,r,-r,r),
                   ("l",-(450-(r*2)),0), ("c",-hr,0,-r,-hr,-r,-r),
                   ("l",0,-(250-(r*2))), ("c",0,-hr,hr,-r,r,-r)],
                  {"fill": "#8080e0", "stroke": "#000000", "stroke-width": 4}),
             Path((100, 50, 450, 250),
                  [("M",r,0), ("l",450-(r*2),0), ("c",hr,0,r,hr,r,r),
                   ("l",0,250-(r*2)), ("c",0,hr,-hr,r,-r,r),
                   ("l",-(450-(r*2)),0), ("c",-hr,0,-r,-hr,-r,-r),
                   ("l",0,-(250-(r*2))), ("c",0,-hr,hr,-r,r,-r)],
                  {"fill": "#ffffff", "stroke": "#000000", "stroke-width": 4}),
             TextBox((100+hr, 170, 450-(hr*2), 250-(r*2)),
                 [Text(front_cover_platforms, "ACORN ELECTRON\nBBC MODEL B\n\n"),
                  Text(front_cover_title, "CASTLE RAIDER")])
             ] + logo)
        ]
    
    if inlay:
        path = os.path.join(output_dir, "inlay.svg")
        inlay = Inlay(path)
        inlay.open()
        
        i = 0
        for page in pages:
        
            page.render(inlay)
            i += 1
        
        inlay.close()
    
    else:
        i = 0
        for page in pages:
        
            path = os.path.join(output_dir, "page-%i.svg" % i)
            svg = SVG(path)
            svg.open()
            page.render(svg)
            svg.close()
            i += 1
    
    sys.exit()
