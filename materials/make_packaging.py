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
    
    if not os.path.exists(source) or os.path.isfile(source):
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
        self.ox = self.oy = 0
        self.defs = ""
    
    def _escape(self, text):
    
        for s, r in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
            text = text.replace(s, r)
        
        return text
    
    def open(self):
    
        self.text = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                     '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
                     '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    
    def add_defs(self, defs):
    
        self.defs = defs
    
    def add_page(self, width, height):
    
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n'
                      '     width="%fcm" height="%fcm"\n'
                      '     viewBox="0 0 %i %i">\n') % (width/100.0, height/100.0, width, height)
        
        self.text += '<defs>\n' + defs + '\n</defs>\n'
    
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

    def __init__(self, path, page_rects, total_size):
    
        SVG.__init__(self, path)
        
        self.page_rects = page_rects
        self.total_size = total_size
        self.page_number = 0
        self.reverse = False
    
    def open(self):
    
        SVG.open(self)
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n')
        
        w, h = self.total_size
        self.text += ('     width="%fcm" height="%fcm"\n'
                      '     viewBox="0 0 %i %i">\n' % (w/100.0, h/100.0, w, h))
        
        self.text += '<defs>\n' + defs + '\n</defs>\n'
    
    def add_page(self, width, height):
    
        if self.page_number > 0:
        
            rect, reverse = self.page_rects[self.page_number - 1]
        
            if reverse:
                self.text += '</g>\n'
            
            self.text += self.crop_marks(rect)
        
        rect, self.reverse = self.page_rects[self.page_number]
        self.ox, self.oy, w, h = rect
        self.page_number += 1
        
        if self.reverse:
            self.text += '<g transform="rotate(180) translate(%f, %f)">\n' % \
                         (-(self.ox*2 + w), -(self.oy*2 + h))
    
    def add_image(self, x, y, width, height, path):
    
        SVG.add_image(self, self.ox + x, self.oy + y, width, height, path)
    
    def add_text(self, x, y, font, text):
    
        SVG.add_text(self, self.ox + x, self.oy + y, font, text)
    
    def close(self):
    
        if self.page_number > 0:
        
            rect, reverse = self.page_rects[self.page_number - 1]
            
            if self.reverse:
                self.text += '</g>\n'
            
            self.text += self.crop_marks(rect)
        
        SVG.close(self)
    
    def crop_marks(self, rect):
    
        return ('<path d="M %f %f l 0 16 l 0 -8 l 8 0" '
                          'stroke="black" fill="none" stroke-width="0.5" />\n'
                          '<path d="M %f %f l 0 -16 l 0 8 l 8 0" '
                          'stroke="black" fill="none" stroke-width="0.5" />\n'
                          '<path d="M %f %f l 0 16 l 0 -8 l -8 0" '
                          'stroke="black" fill="none" stroke-width="0.5" />\n'
                          '<path d="M %f %f l 0 -16 l 0 8 l -8 0" '
                          'stroke="black" fill="none" stroke-width="0.5" />\n' % \
                          (rect[0], rect[1] - 8, rect[0], rect[1] + rect[3] + 8,
                           rect[0] + rect[2], rect[1] - 8, rect[0] + rect[2],
                           rect[1] + rect[3] + 8))


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

    def __init__(self, bbox, text_items, line_spacing = 1.0, follow = False, index = -1):
    
        self.bbox = bbox
        self.text_items = text_items
        self.line_spacing = line_spacing
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
                
                y += line_height * self.line_spacing
        
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
                    yield self.format([word], width), self.height([word])
                    
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


class Transform:

    def __init__(self, transformation, elements):
    
        self.transformation = transformation
        self.elements = elements
    
    def render(self, svg, positions):
    
        svg.text += '<g transform="translate(%f,%f) ' % (svg.ox, svg.oy)
        svg.text += ' '.join(map(lambda (k,v): '%s(%s)' % (k, v), self.transformation))
        svg.text += '">\n'
        
        ox, oy = svg.ox, svg.oy
        svg.ox, svg.oy = 0, 0
        
        for element in self.elements:
        
            x, y = element.render(svg, positions)
        
        svg.text += '</g>\n'
        svg.ox, svg.oy = ox, oy
        return x, y

# Font definitions

#sans = "FreeSans"
sans = "Futura Md BT"

regular = {"family": "FreeSans",
           "size": 20,
           "align": "justify"}

title = {"family": sans,
         "size": 28,
         "weight": "bold"}

subtitle = {"family": "FreeSans",
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

keys_quote = {"family": "FreeSans",
              "size": regular["size"],
              "left indent": 40,
              "right indent": 40}

key_descriptions_quote = {"family": "FreeSans",
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

back_cover_centred = {"family": sans,
                      "size": 22,
                      "align": "centre"}

back_cover_regular = {"family": sans,
                      "size": 20}

back_cover_publisher1 = {"family": sans, "size": 46,
                         "weight": "bold", "align": "centre",
                         "colour": "#202020"}

back_cover_publisher2 = {"family": sans, "size": 46,
                         "weight": "bold", "align": "centre",
                         "colour": "#ffffc0"}

front_cover_publisher1 = {"family": sans, "size": 34,
                          "weight": "bold", "align": "centre",
                          "colour": "#202020"}

front_cover_publisher2 = {"family": sans, "size": 34,
                          "weight": "bold", "align": "centre",
                          "colour": "#ffffc0"}

spine_publisher1 = {"family": sans, "size": 20,
                    "weight": "bold", "align": "centre",
                    "colour": "#202020"}

spine_publisher2 = {"family": sans, "size": 20,
                    "weight": "bold", "align": "centre",
                    "colour": "#ffffc0"}

front_cover_platforms = {"family": sans, "size": 42,
                         "weight": "bold", "align": "centre"}

front_cover_title = {"family": sans, "size": 66,
                     "weight": "bold", "align": "centre"}

spine_title = {"family": sans, "size": 44,
               "weight": "bold", "align": "centre"}

back_flap_text = {"family": "FreeSerif", "size": 32, "align": "centre"}

back_flap_bold_text = {"family": "FreeSerif", "size": 32,
                       "weight": "bold", "align": "centre"}

# Functions to generate common elements

def curved_box(x, y, w, h, style):

    r = w/10.0
    hr = r/2.0
    ll = w - (4 * r)
    
    return Path((x, y, w, h),
                 [("M",r,0), ("l",ll,0), ("c",hr,0,r,hr,r,r),
                  ("l",0,ll), ("c",0,hr,-hr,r,-r,r),
                  ("l",-ll,0), ("c",-hr,0,-r,-hr,-r,-r),
                  ("l",0,-ll), ("c",0,-hr,hr,-r,r,-r)], style)

def make_checkered(w, h, sx, sy, background = "#ffdd77"):

    checkered = []
    x = sx
    while x < w:
        checkered += [("M",x,0), ("l",0,h)]
        x += 20
    
    y = sy
    while y < h:
        checkered += [("M",0,y), ("l",w,0)]
        y += 20
    
    components = [int(background[1:][:2], 16),
                  int(background[1:][2:4], 16),
                  int(background[1:][4:], 16)]
    c = (min(components)/16) * 8
    line_colour = "#%02x%02x%02x" % (c, c, c)
    return Path((0, 0, w, h), checkered, {"stroke": line_colour, "stroke-width": 1})

def make_logo(cx, y, w, h, font1, font2):

    logo = []
    x = cx - (len("RETRO") * w)/2.0
    lr = h/10.0
    lhr = lr/2.0
    
    font2 = font2.copy()
    font2["colour"] = logo_background
    
    for ch in "RETRO":
        logo.append(curved_box(x - lhr, y + lr + lhr, w, h,
                               {"fill": logo_shadow, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": logo_background, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(TextBox((x + lr, y + lr + h/2 + 1, w - (lr * 2), h),
                            [Text(font1, ch)]))
        x += w
    
    x = cx - (len("SOFTWARE") * w)/2.0
    y += h
    
    for ch in "SOFTWARE":
        logo.append(curved_box(x - lhr, y + lr + lhr, w, h,
                               {"fill": logo_shadow, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": "#202020", "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(TextBox((x + lr, y + lr + h/2, w - (lr * 2), h),
                            [Text(font2, ch)]))
        x += w
    
    return logo

def make_back_flap(r, hr, o, background):

    sbx = 200
    sbw = 600
    sbh = 200
    
    return Page((200, 1000),
                [Path((0, 0, 200, 1000),
                      [("M",0,0), ("l",650,0), ("l",0,1000), ("l",-650,0), ("l",0,-1000)],
                      {"fill": background, "stroke": "#000000", "stroke-width": 1}),
                 make_checkered(200, 1000, 10, 10, background),
                 Path((0, 0, 200, 1000),
                      [("M",200,0), ("l",-200,200), ("l",0,600), ("l",200,200), ("z",)],
                      {"fill": "white", "stroke": "#000000", "stroke-width": 1}),

                 Transform([("rotate", 90)],
                     [Transform([("translate", "0,-200")],
                          [TextBox((sbx - 20, 56, sbw + 40, sbh),
                               [Text(back_flap_text,
                                     u"Copyright \u00a9 2014 David Boddie"),
                                Text(back_flap_text,
                                     u"Licensed under the GNU GPL version 3 or later"),
                                Text(back_flap_text,
                                     u"An Infukor production for Retro Software"),
                                Text(back_flap_bold_text,
                                     u"http://www.retrosoftware.co.uk/")])
                          ])
                     ]),
                ])

def make_spine(r, hr, o, background):

    sbx = 300
    sbw = 400
    sbh = 60
    
    return Page((100, 1000),
                [Path((0, 0, 100, 1000),
                      [("M",0,0), ("l",650,0), ("l",0,1000), ("l",-650,0), ("l",0,-1000)],
                       {"fill": background, "stroke": "none"}),
                 make_checkered(100, 1000, 10, 10, background),

                 Transform([("rotate", 90)],
                     [Transform([("translate", "0,-105")],
                          make_logo(150, 25, 30, 30, spine_publisher1, spine_publisher2) + \
                          make_logo(850, 25, 30, 30, spine_publisher1, spine_publisher2) + \
                          [Path((sbx-r+(r*o)+10, 15, sbw+r-(r*o*2), sbh+r-(r*o)),
                                [("M",sbw+r-(r*o*2),sbh-(r*o)),
                                 ("l",-r*0.5,r*0.5), ("c",-r*0.5,r*0.5,-r*0.5,r*0.5,-r,r*0.5),
                                 ("l",-sbw+(r*o*2)+(r*1.5),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                                 ("l",0,-sbh+(r*o*2)+(r*1.5)), ("c",0,-r*0.5,0,-r*0.5,r*0.5,-r),
                                 ("l",r*0.5,-r*0.5), ("z",)],
                                {"fill": box_shadow, "stroke": "#000000", "stroke-width": 4}),
                            Path((sbx+10, 15, sbw, sbh),
                                [("M",r,0), ("l",sbw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                                 ("l",0,sbh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                                 ("l",-(sbw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                                 ("l",0,-(sbh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                                {"fill": box_background, "stroke": "#000000", "stroke-width": 4}),
                            TextBox((sbx+10, 61, sbw, sbh),
                               [Text(spine_title, "CASTLE RAIDER")])
                          ])
                     ]),
                ])

def make_title_box(bx, by, bw, bh, r, hr, o):

    return [Path((bx-r+(r*o), by, bw+r-(r*o*2), bh+r-(r*o)),
                 [("M",bw+r-(r*o*2),bh-(r*o)),
                  ("l",-r*0.5,r*0.5), ("c",-r*0.5,r*0.5,-r*0.5,r*0.5,-r,r*0.5),
                  ("l",-bw+(r*o*2)+(r*1.5),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                  ("l",0,-bh+(r*o*2)+(r*1.5)), ("c",0,-r*0.5,0,-r*0.5,r*0.5,-r),
                  ("l",r*0.5,-r*0.5), ("z",)],
                 {"fill": box_shadow, "stroke": "#000000", "stroke-width": 4}),

            Path((bx, by, bw, bh),
                 [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                  ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                  ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                  ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                 {"fill": box_background, "stroke": "#000000", "stroke-width": 4})]


def make_front_cover(bx, bw, bh, title_by, title_bh, py, r, hr, o, background):

    cax = 265
    bat = [("M",0,15), ("l",12,-10), ("l",3,0), ("l",5,5), ("l",5,-5), ("l",3,0),
           ("l",12,10), ("l",-12,-2),
           ("l",-4,6), ("l",-4,-6), ("l",-4,6), ("l",-4,-6), ("l",-12,2), ("z",)]
    
    return Page((650, 1000),
                [Path((0, 0, 650, 1000),
                      [("M",0,0), ("l",650,0), ("l",0,1000), ("l",-650,0), ("l",0,-1000)],
                      {"fill": background, "stroke": "none"}),
                 make_checkered(650, 1000, 10, 10, background)

                ] + make_title_box(bx, title_by, bw, title_bh, r, hr, o) + [

                 TextBox((bx, title_by + 115, bw, title_bh-(r*2)),
                     [Text(front_cover_platforms, "%s" % platform.upper()),
                      Text(front_cover_title, "CASTLE RAIDER")],
                      line_spacing = 1.25)

                ] + make_logo(bx + bw/2.0, 40, 50, 50, front_cover_publisher1, front_cover_publisher2) + \

                [Path((bx-r+(r*o), py, bw+r-(r*o*2), bh+r-(r*o)),
                      [("M",bw+r-(r*o*2),bh-(r*o)),
                       ("l",-r*0.5,r*0.5), ("c",-r*0.5,r*0.5,-r*0.5,r*0.5,-r,r*0.5),
                       ("l",-bw+(r*o*2)+(r*1.5),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                       ("l",0,-bh+(r*o*2)+(r*1.5)), ("c",0,-r*0.5,0,-r*0.5,r*0.5,-r),
                       ("l",r*0.5,-r*0.5), ("z",)],
                      {"fill": box_shadow, "stroke": "#000000", "stroke-width": 4}),

                 Path((bx, py, bw, bh),
                      [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                       ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                       ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                       ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                      {"fill": "url(#box-background)", "stroke": "none", "stroke-width": 4}),

                 # Hills
                 Path((bx, py, 550, 550),
                      [("M",80,320), ("c",70,-15,150,-30,220,-35),
                       ("c",100,5,150,10,210,25),
                       ("L",550,320), ("z",)],
                      {"stroke": "black", "fill": "url(#distant-hills)"}),

                 Path((bx, py, 550, 550),
                      [("M",0,300), ("c",90,10,120,20,170,30),
                       ("L",0,350), ("z",)],
                      {"stroke": "black", "fill": "url(#distant-hills)"}),

                 Path((bx, py, 550, 550),
                      [("M",400,320), ("c",70,-10,110,-15,150,-20),
                       ("L",550,350), ("L",400,350), ("z",)],
                      {"stroke": "black", "fill": "url(#distant-hills)"}),

                 Path((bx, py, 550, 550),
                      [("M",0,350), ("c",80,-10,130,-25,280,-30),
                       ("c",120,0,220,5,270,15),
                       ("L",550,550-r), ("c",0,hr,-r+hr,r,-r,r),
                       ("L",r,550), ("c",-hr,0,-r,-r+hr,-r,-r),
                       ("z",)],
                      {"stroke": "black", "fill": "url(#hills)"}),

                 # Castle

                 # Base
                 Path((bx, py, 550, 550),
                      [("M",cax-45,350), ("L",cax+75,370), ("L",cax+195,350),
                       ("L",cax+75,330), ("Z",)],
                      {"stroke": "none", "fill": "#001000"}),

                 # Left wall
                 Path((bx, py, 550, 550),
                      [("M",cax,350), ("l",0,-200),
                       ("l",15,-3), ("l",0,9), ("l",15,-3), ("l",0,-9),
                       ("l",15,-3), ("l",0,9), ("l",15,-3), ("l",0,-9),
                       ("l",15,-3), ("l",0,224), ("z",)],
                      {"stroke": "black", "fill": "url(#walls)", "stroke-width": 2}),

                 # Left window and doorway
                 Path((bx, py, 550, 550),
                      [("M",cax+26,200), ("l",10,-15), ("l",10,10), ("l",0,50), ("l",-20,2), ("z",)],
                      {"stroke": "none", "fill": "black"}),

                 Path((bx, py, 550, 550),
                      [("M",cax+21,300), ("l",10,-15), ("l",10,0), ("l",10,17), ("l",0,53), ("l",-30,-2), ("z",)],
                      {"stroke": "black", "stroke-width": 2, "fill": "black"}),

                 # Shadow
                 Path((bx, py, 550, 550),
                      [("M",cax+75,359), ("L",550,389), ("L",550,349),
                       ("L",cax+150,339), ("z",)],
                      {"stroke": "none", "fill": "black", "opacity": 0.5}),

                 # Right wall
                 Path((bx, py, 550, 550),
                      [("M",cax+75,359), ("l",0,-224),
                       ("l",15,3), ("l",0,9), ("l",15,3), ("l",0,-9),
                       ("l",15,3), ("l",0,9), ("l",15,3), ("l",0,-9),
                       ("l",15,3), ("l",0,200), ("z",)],
                      {"stroke": "black", "fill": "url(#dark-walls)", "stroke-width": 2}),

                 # Right window
                 Path((bx, py, 550, 550),
                      [("M",cax+124,200), ("l",-10,-15), ("l",-10,10), ("l",0,50), ("l",20,2), ("z",)],
                      {"stroke": "none", "fill": "black"}),

                 Path((bx, py, 550, 550),
                      [("M",cax+121,200), ("l",-7,-11), ("l",-6.5,6), ("l",0,47.5), ("l",13.5,1.5), ("z",)],
                      {"stroke": "none", "fill": "url(#lit-window)"}),

                 # Path
                 Path((bx, py, 550, 550),
                      [("M",cax+21,353), ("C",120,400,90,450,50,550),
                       ("L",200,550), ("C",160,450,200,400,cax+51,353), ("Z",)],
                      {"stroke": "black", "fill": "url(#path)", "stroke-width": 2}),

                 # Bats
                 Transform([("translate", "%i,%i" % (bx + 70, py + 90)),
                            ("scale", 0.65)],
                           [Path((0, 0, 40, 23), bat,
                                 {"stroke": "none", "fill": "black"}),
                            Path((30, 60, 40, 23), bat,
                                 {"stroke": "none", "fill": "black"}),
                            Path((40, 20, 40, 23), bat,
                                 {"stroke": "none", "fill": "black"})]),
                 Transform([("translate", "%i,%i" % (bx + 140, py + 150)),
                            ("scale", 0.8)],
                           [Path((0, 0, 40, 23), bat,
                                 {"stroke": "none", "fill": "black"})]),
                 Path((bx + 210, py + 180, 40, 23), bat,
                      {"stroke": "none", "fill": "#1c1c1c"}),

                 # Drawing border
                 Path((bx, py, bw, bh),
                      [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                       ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                       ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                       ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                      {"fill": "none", "stroke": "#000000", "stroke-width": 4})
                ])

def inner_instructions_decoration(sx, sy, w, h, offset, size):

    text = "RETROSOFTWARE"
    i = 0
    decor = []
    x = sx + offset
    y = offset
    font = {"family": sans, "size": size * 0.7, "weight": "bold", "align": "centre"}
    
    while True:
        
        decor.append(curved_box(x, y, size, size,
                                {"fill": "none", "stroke": "#000000", "stroke-width": 2}))
        decor.append(TextBox((x, y + size * 0.65, size * 0.8, size * 0.8),
                             [Text(font, text[i])]))
        x += size * 0.96
        i = (i + 1) % len(text)
        
        if x + (size * 1.8) >= w:
            break
    
    while True:
    
        decor.append(curved_box(x, y, size, size,
                                {"fill": "none", "stroke": "#000000", "stroke-width": 2}))
        decor.append(Transform([("translate", "%f,%f" % (x, y)), ("rotate", 90)],
                               [TextBox((0, -size * 0.8 + size * 0.65, size * 0.8, size * 0.8),
                                        [Text(font, text[i])])]))
        y += size * 0.94
        i = (i + 1) % len(text)
        
        if y + (size * 1.8) >= h:
            break
    
    while True:
    
        decor.append(curved_box(x, y, size, size,
                                {"fill": "none", "stroke": "#000000", "stroke-width": 2}))
        decor.append(Transform([("translate", "%f,%f" % (x, y)), ("rotate", 180)],
                               [TextBox((-size * 0.8, -size * 0.8 + size * 0.65, size * 0.8, size * 0.8),
                                        [Text(font, text[i])])]))
        x -= size * 0.96
        i = (i + 1) % len(text)
        
        if x - size <= 0:
            break
    
    while True:
    
        decor.append(curved_box(x, y, size, size,
                                {"fill": "none", "stroke": "#000000", "stroke-width": 2}))
        decor.append(Transform([("translate", "%f,%f" % (x, y)), ("rotate", 270)],
                               [TextBox((-size * 0.8, size * 0.65, size * 0.8, size * 0.8),
                                        [Text(font, text[i])])]))
        y -= size * 0.94
        i = (i + 1) % len(text)
        
        if y - size <= 0:
            break
    
    return decor


if __name__ == "__main__":

    app = QApplication([])
    
    if not 3 <= len(sys.argv) <= 4:
    
        sys.stderr.write("Usage: %s [--inlay] <platform> <output directory>\n" % sys.argv[0])
        sys.exit(1)
    
    if sys.argv[1] == "--inlay":
        platform = sys.argv[2]
        output_dir = sys.argv[3]
        inlay = True
    else:
        platform = sys.argv[1]
        output_dir = sys.argv[2]
        inlay = False
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    r = 25
    hr = 0.5*r
    
    # Background colour
    if platform == "Acorn Electron":
        background = "#509040"
        box_background = "#ffffff"
        box_shadow = "#ffb060"
        logo_background = "#ffffc0"
        logo_shadow = "#ff4040"
    elif platform == "BBC Model B":
        background = "#00a0ff"
        box_background = "#ffff30"
        box_shadow = "#ff4040"
        logo_background = box_background
        logo_shadow = box_shadow
    else:
        background = "#ffdd77"
        box_background = "#ffffff"
        box_shadow = "#ffb060"
        logo_background = "#ffffc0"
        logo_shadow = box_shadow
    
    # Placement of boxes on the front cover
    bx = 60
    bw = 550
    bh = bw
    # Title box vertical position and height
    tby = 70
    tbh = 200
    
    # Picture position
    py = 360
    
    # Shadow offset and castle position
    o = 0.32 # 1 - 1/(2**0.5)
    
    # Screenshot scale and horizontal positions
    scale = 200/256.0
    sw = scale * 320
    sr = (bw - (2 * sw))/3.0
    
    back_flap = make_back_flap(r, hr, o, background)
    spine = make_spine(r, hr, o, background)
    blank_spine = Page((100, 1000),
                       [Path((0, 0, 100, 1000),
                             [("M",0,0), ("l",100,0), ("l",0,1000), ("l",-100,0), ("z",)],
                             {"stroke": "none", "fill": "none"})])
    front_cover = make_front_cover(bx, bw, bh, tby, tbh, py, r, hr, o, background)
    
    instructions = [
        Page((650, 1000),
            [TextBox((57, 77, 570, 0), 
                 [Text(title, "Castle Raider")]),
             TextBox((57, -5, 570, 0),
                 [Text(regular,
                       "As the sun dips below the ramparts of the old town, the last of the troops file "
                       "in. As they make their way through the narrow, cobbled streets, small groups of "
                       "them quietly slink away into the many taverns that give this district its bad "
                       "reputation. The lamps are lit and the merriment spills out onto the streets "
                       "with laughing, singing, pushing and shoving. There will be trouble later, but "
                       "by then you will be long gone.")], follow = True),
             TextBox((57, 8, 570, 0),
                 [Text(regular,
                       "It is time for the guard to change, time for the night watch to begin their "
                       "duties, but they are in no hurry; though the outlaws in the countryside know "
                       "the force stationed here will be no threat tonight, they gave them a wide "
                       "berth during their march here. The people in the nearby villages can sleep "
                       "soundly for a change.")], follow = True),
             TextBox((57, 8, 570, 0),
                 [Text(regular,
                       "As the members of the night watch slowly begin to take their places on the "
                       "ramparts you take your chance and slip through the open gate, taking refuge in "
                       "the long shadows fleeing the sunset. The few eyes looking in your direction are "
                       "hardly able to make out your form as you wait for the approaching nightfall.")],
                       follow = True),
             TextBox((57, 8, 570, 0),
                 [Text(regular,
                       "You recall the stories told when you were young. When the town itself was "
                       "already old, the last of the elders told of a time when it was still a village, "
                       "not much more than a few houses and shelters. The road that ran through it went "
                       "to the castle on the edge of the wasteland that now lies derelict and deserted.")],
                       follow = True),
             TextBox((57, 8, 570, 0),
                 [Text(regular,
                       "Night falls quickly in this season at the edge of the kingdom. Memories of "
                       "fireside tales about the king's lost crown and the hidden treasure of the old "
                       "kingdom make the journey across the plains more bearable. Soon you arrive at "
                       "the outer fortifications. Crossing a bridge, you enter. As you pass beneath the "
                       "outer gate it suddenly crashes into place, cutting off your exit. It was just "
                       "as well you hadn't planned to return that way.")],
                       follow = True),
             TextBox((57, 8, 570, 0),
                 [Text(regular,
                       "Nature has reclaimed parts of the castle, its ruins crumbling in places and "
                       "crawling with creatures that people once knew well to leave alone. To make your "
                       "way through it to the lands beyond, you will need to unlock the few doors and "
                       "gates that still stand. Perhaps the folk tales were true and the king's "
                       "treasure still remains, but survival is more important here. If you live to "
                       "pass through the outer gate then the story alone will have made the journey "
                       "worthwhile.")],
                  follow = True)

             ] + inner_instructions_decoration(0, 0, 650*2, 1000, 7, 48)),
        Page((650, 1000),
             [TextBox((25, 85, 555, 0),
                  [Text(subtitle, "Loading the Game\n"),
                   Text(regular, "Insert the cassette and type\n")]),
              TextBox((25, -2, 555, 0),
                  [Text(monospace_quote, 'CHAIN "CASTLE"\n')], follow = True),
              TextBox((25, -2, 555, 0),
                  [Text(regular,
                        "then press Return. Press play on the cassette recorder.")],
                        follow = True),

              TextBox((25, 20, 555, 0),
                  [Text(subtitle, "Playing the Game\n"),
                   Text(regular,
                        "The player must help their character escape the castle, "
                        "ideally with some hidden treasure.\n"),
                   Text(regular,
                        "Your character can roam the castle and its surroundings using the following "
                        "control keys:\n")],
                  follow = True),
              TextBox((25, 0, 555, 0),
                  [Text(keys_quote,
                        "Z\n"
                        "X\n"
                        "Return\n"
                        "/")], follow = True),
              TextBox((25, 0, 555, 0),
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
              TextBox((25, 0, 555, 0),
                  [Text(keys_quote,
                        "Left\n"
                        "Right\n"
                        "Fire\n"
                        "Down\n")], follow = True),
              TextBox((25, 0, 555, 0),
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
              TextBox((25, 0, 555, 0),
                  [Text(keys_quote,
                        "S\n"
                        "Q\n"
                        "P\n"
                        "O\n"
                        "Escape")], follow = True),
              TextBox((25, 0, 555, 0),
                  [Text(key_descriptions_quote,
                        "enable sound effects\n"
                        "disable sound effects\n"
                        "pause the game\n"
                        "resume the game\n"
                        "quit the game, returning to the title screen\n")],
                  follow = True, index = -2),
              TextBox((25, 6, 555, 0),
                  [Text(regular, "Good luck!")], follow = True)
             ]),
        Page((650, 1000),
             [Path((0, 0, 650, 1000),
                   [("M",0,0), ("l",650,0), ("l",0,1000), ("l",-650,0), ("l",0,-1000)],
                   {"fill": background, "stroke": "none"}),
              make_checkered(650, 1000, 0, 10, background),

             ] + make_logo(bx + bw/2.0, 40, 70, 70, back_cover_publisher1, back_cover_publisher2) + [

             ] + make_title_box(bx + bw - sw - 22, 190, sw + 20, 222, r, hr, o) + \
                 make_title_box(bx, 190, sw + 22, 222, r, hr, o) + [

              #Image((35.333, 0, 450, 0), "images/2014-11-30-loading.png", scale = 0.85, follow = True),
              Image((bx + 11, 201, sw, 0), "images/2014-11-30-action.png", scale = scale),
              #Image((35.333, 25, 450, 0), "images/2014-11-30-basement.png", scale = 0.85, follow = True),
              Image((bx + bw - sw - 11, 201, sw, 0), "images/2014-11-30-basement.png", scale = scale),

             ] + make_title_box(bx, 445, bw, 465, r, hr, o) + [

              TextBox((bx, 479, bw, 0),
                      [Text(back_cover_centred,
                            u"Copyright \u00a9 2014 David Boddie\n"
                            u"An Infukor production for Retro Software\n"
                            u"http://www.retrosoftware.co.uk/")]),

              TextBox((bx + 25, 5, bw - 50, 0),
                      [Text(back_cover_regular,
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
                            "along with this program.\nIf not, see <http://www.gnu.org/licenses/>.")],
                      follow = True)

             ])
        ]
    
    defs = ('<linearGradient id="box-background" x1="20%" y1="0%" x2="80%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#4040a0" />\n'
            '  <stop offset="40%" stop-color="#000000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="hills" x1="0%" y1="0%" x2="100%" y2="100%">\n'
            '  <stop offset="20%" stop-color="#003000" />\n'
            '  <stop offset="100%" stop-color="#001000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="distant-hills" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="20%" stop-color="#002000" />\n'
            '  <stop offset="100%" stop-color="#000000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="walls" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#603030" />\n'
            '  <stop offset="100%" stop-color="#502020" />\n'
            '</linearGradient>\n'
            '<linearGradient id="dark-walls" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#401010" />\n'
            '  <stop offset="100%" stop-color="#301010" />\n'
            '</linearGradient>\n'
            '<linearGradient id="path" x1="100%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#303030" />\n'
            '  <stop offset="100%" stop-color="#404040" />\n'
            '</linearGradient>\n'
            '<linearGradient id="lit-window" x1="10%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="50%" stop-color="#00000" />\n'
            '  <stop offset="100%" stop-color="#de8600" />\n'
            '</linearGradient>\n')
    
    if inlay:
    
        pages = instructions + [spine, front_cover]
        
        file_name = "%s-inlay.svg" % platform.replace(" ", "-")
        
        page_rects = [((0, 0, 650, 1000), False),
                      ((650, 0, 650, 1000), False),
                      ((650*2, 0, 650, 1000), False),
                      ((650*3, 0, 100, 1000), False),
                      ((650*3 + 100, 0, 650, 1000), False)]
        
        # A4 paper
        total_size = (2970, 2100)
        
        path = os.path.join(output_dir, file_name)
        dx = (2970 - 1400*2 - 50)/2.0
        dy = (2100 - 1000*2 - 50)/2.0
        
        for i in range(len(page_rects)):
            rect, rev = page_rects[i]
            page_rects[i] = ((rect[0] + dx, rect[1] + dy,) + rect[2:], rev)
            page_rects.append(((rect[0] + dx, rect[1] + dy + 1050) + rect[2:], rev))
            pages.append(pages[i])
        
        inlay = Inlay(path, page_rects, total_size)
        inlay.open()
        inlay.add_defs(defs)
        
        i = 0
        for page in pages:
            page.render(inlay)
            i += 1
        
        inlay.close()
    else:
        pages = [front_cover] + instructions
        
        i = 0
        for page in pages:
        
            path = os.path.join(output_dir, "page-%i.svg" % i)
            svg = SVG(path)
            svg.open()
            svg.add_defs(defs)
            page.render(svg)
            svg.close()
            i += 1
    
    sys.exit()
