#!/usr/bin/env python3

"""
Copyright (C) 2020 David Boddie <david@boddie.org.uk>

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

import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import *

sans = "Futura Md BT"

front_cover_publisher1 = {"family": sans, "size": 22,
                          "weight": "bold", "align": "centre",
                          "colour": "#202020"}

front_cover_publisher2 = {"family": sans, "size": 22,
                          "weight": "bold", "align": "centre",
                          "colour": "#ffff40"}

def make_logo(w, h):

    width = len("RETRO POWER") * w
    height = h * 1.5
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(QColor(0,0,0))

    bw = w - 3
    bh = h - 3

    font = QFont(sans)
    font.setPixelSize(h - 6)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    painter.setFont(font)

    lr = 2
    lhr = 3

    x = w/4
    y = 0.25 * h

    painter.setPen(QColor(0,0,0))

    for ch in "RETRO":
        painter.setBrush(QColor(255,0,0))
        painter.drawRoundedRect(x - lhr, y + lhr, bw, bh, lr, lr)
        painter.setBrush(QColor(255,255,0))
        painter.drawRoundedRect(x, y, bw, bh, lr, lr)
        painter.drawText(x, y, bw, bh, Qt.AlignCenter, ch)
        x += w
    
    x += w/2
    
    for ch in "POWER":
        painter.setPen(QColor(0,0,0))
        painter.setBrush(QColor(255,0,0))
        painter.drawRoundedRect(x - lhr, y + lhr, bw, bh, lr, lr)
        painter.setPen(QColor(255,0,0))
        painter.setBrush(QColor(0,0,0))
        painter.drawRoundedRect(x, y, bw, bh, lr, lr)
        painter.setPen(QColor(255,255,0))
        painter.drawText(x, y, bw, bh, Qt.AlignCenter, ch)
        x += w

    painter.end()

    return image


if __name__ == "__main__":

    app = QGuiApplication(sys.argv)
    image = make_logo(29, 29)
    image.save("RetroPower-logo.png")
