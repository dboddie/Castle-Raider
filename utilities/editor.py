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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tools import makelevels

standard_palette = [qRgb(0, 0, 0), qRgb(255, 0, 0), qRgb(0, 255, 0),
                    qRgb(255, 255, 0), qRgb(0, 0, 255), qRgb(255, 0, 255),
                    qRgb(0, 255, 255), qRgb(255, 255, 255)]

class ColourDialog(QDialog):

    def __init__(self, parent, title):
    
        QDialog.__init__(self, parent)
        
        group = QButtonGroup(self)
        group.buttonClicked[int].connect(self.selected)
        
        layout = QHBoxLayout(self)
        
        for i in range(len(standard_palette)):
        
            button = QToolButton()
            button.setText(str(i))
            
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(standard_palette[i]))
            palette.setColor(QPalette.ButtonText, QColor(standard_palette[7 - i]))
            button.setPalette(palette)
            layout.addWidget(button)
            
            group.addButton(button, i)
        
        self.setWindowTitle(title)
    
    def selected(self, id):
    
        self.colour = ("black", "red", "green", "yellow", "blue", "magenta",
                       "cyan", "white")[id]
        self.accept()


class DestinationDialog(QDialog):

    def __init__(self, parent, title, portals):
    
        QDialog.__init__(self, parent)
        
        group = QButtonGroup(self)
        group.buttonClicked[int].connect(self.selected)
        
        layout = QGridLayout(self)
        
        for i in range(len(makelevels.portals_order)):
        
            symbol = makelevels.portals_order[i]
            
            button = QToolButton()
            button.setText(symbol)
            
            index, dest, colour = portals[symbol]
            text_colour = standard_palette[7 - makelevels.colours[colour]]
            
            palette = QPalette()
            colour = standard_palette[makelevels.colours[colour]]
            palette.setColor(QPalette.Window, QColor(colour))
            palette.setColor(QPalette.ButtonText, QColor(text_colour))
            button.setPalette(palette)
            layout.addWidget(button, i / 4, i % 4)
            
            group.addButton(button, i)
        
        self.setWindowTitle(title)
    
    def selected(self, id):
    
        self.destination = makelevels.portals_order[id]
        self.accept()


class LevelWidget(QWidget):

    navigationRequested = pyqtSignal(unicode)
    
    def __init__(self, tile_images, monster_images, parent = None):
    
        QWidget.__init__(self, parent)
        self.xs = 4
        self.ys = 2
        self.screen_width = 40 * 4
        self.screen_height = 22 * 8
        
        self.tile_images = tile_images
        self.currentTile = "."
        self.maximum_width = 1024
        self.monster_images = monster_images
        
        self.finishing_offset = 0x304
        
        font = QFont("Monospace")
        font.setPixelSize(min(4 * self.xs - 2, 8 * self.ys - 2))
        self.setFont(font)
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
    
    def initRows(self, name):
    
        self.level = name
        self.rows = {name: []}
        self.order = [name]
        
        for i in range(16):
        
            row = ["."] * self.maximum_width
            self.rows[self.level].append(row)
        
        self.special = {}
        
        # Define default special tiles.
        
        for i in range(16):
        
            ch = makelevels.special_order[i]
            tile = "I"
            index = 16 + i
            flags = ["collectable"]
            self.special[ch] = (tile, index, flags)
        
        self.portals = {}
        self.portal_locations = {}
        
        # Define default portals.
        
        for i in range(16):
        
            src = makelevels.portals_order[i]
            index = 128 + i
            dest = makelevels.portals_order[0]
            colour = "green"
            self.portals[src] = (index, dest, colour)
    
    def loadMap(self, path):
    
        try:
            levels, special, portals, finish = makelevels.load_level(path)
            
            self.special = special
            self.portals = portals
            self.portal_locations = {}
            self.finishing_offset = finish
            
            self.rows = {}
            self.order = []
            
            for name, rows in levels:
            
                self.order.append(name)
                self.rows[name] = []
                
                for r in range(len(rows)):
                
                    # Record which level each portal is found in.
                    for portal in self.portals:
                        at = rows[r].find(portal)
                        if at != -1:
                            self.portal_locations[portal] = (name, at, r)
                    
                    # Convert the string to a list of characters.
                    row = map(str, rows[r])
                    
                    # Extend each level to the maximum width, or truncate it
                    # if it exceeds it.
                    if len(row) < self.maximum_width:
                        row += (self.maximum_width - len(row)) * ["."]
                    elif len(row) > self.maximum_width:
                        row = row[:self.maximum_width]
                    
                    self.rows[name].append(row)
            
            self.level = self.order[0]
            return True
        
        except IOError:
            return False
    
    def saveMap(self, path):
    
        try:
            f = open(unicode(path), "w")
            
            # Write the special tiles.
            special_items = self.special.items()
            sorted_special_items = []
            
            for ch, (n, index, flags) in special_items:
                sorted_special_items.append((index, ch, n, flags))
            
            sorted_special_items.sort()
            
            for index, ch, n, flags in sorted_special_items:
            
                if not flags:
                    flags = ["undefined"]
                f.write("%s %s %s\n" % (ch, n, ",".join(flags)))
            
            f.write("\n")
            
            # Write the portals.
            for src, (index, dest, colour) in self.portals.items():
            
                f.write("%s %s %s\n" % (src, dest, colour))
            
            f.write("\n")
            
            # Write the finishing offset.
            f.write("Finish: %i\n\n" % self.finishing_offset)
            
            for name in self.order:
            
                f.write(name + "\n")
                
                level_width = 40
                
                for row in self.rows[name]:
                
                    i = len(row) - 1
                    
                    while i > 39:
                        if row[i] != ".":
                            break
                        else:
                            i -= 1
                    
                    level_width = max(level_width, i + 1)
                
                for row in self.rows[name]:
                    f.write("".join(row[:level_width]) + "\n")
            
                f.write("\n")
            
            f.close()
            
            return True
        
        except IOError:
            return False
    
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.button() == Qt.MiddleButton:
            self.writeTile(event, ".")
        elif event.button() == Qt.RightButton:
            self.showMenu(event.pos(), event.globalPos())
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event):
    
        if event.buttons() & Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.buttons() & Qt.MiddleButton:
            self.writeTile(event, ".")
        else:
            event.ignore()
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QBrush(Qt.black))
        painter.setPen(Qt.white)
        
        y1 = event.rect().top()
        y2 = event.rect().bottom()
        x1 = event.rect().left()
        x2 = event.rect().right()
        
        r1 = max(0, self._row_from_y(y1))
        r2 = max(0, self._row_from_y(y2))
        c1 = self._column_from_x(x1)
        c2 = self._column_from_x(x2)
        
        # Record the visible monsters and plot them after the background.
        monsters = {}
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
            
                tile = self.rows[self.level][r][c]
                
                if tile in self.special:
                
                    n, index, flags = self.special[tile]
                    tile_image = self.tile_images[n]
                    #if initial:
                    #    tile_image = self.tile_images[n]
                    #else:
                    #    tile_image = self.tile_images["."]
                
                elif tile in self.portals:
                    tile_image = self.tile_images["."]
                    
                    index, dest, colour = self.portals[tile]
                    
                    colour = standard_palette[makelevels.colours[colour]]
                    painter.setPen(QPen(QColor(colour)))
                    painter.setBrush(QBrush(Qt.black))
                    painter.drawRect(c * 4 * self.xs, (6 + r) * 8 * self.ys,
                                     tile_image.width() - 1, tile_image.height() - 1)
                
                elif tile in self.monster_images:
                    monsters[(c, r)] = tile
                else:
                    tile_image = self.tile_images[tile]
                    
                    if c > 0 and self.rows[self.level][r][c-1] in self.monster_images:
                        monsters[(c-1, r)] = self.rows[self.level][r][c-1]
                    
                    painter.drawImage(c * 4 * self.xs, (6 + r) * 8 * self.ys,
                                      tile_image)
                
                if tile in self.special or tile in self.portals:
                
                    painter.setPen(QPen(Qt.white))
                    tx = ((c + 0.5) * 4 * self.xs) - self.font().pixelSize()*0.25
                    ty = ((6.5 + r) * 8 * self.ys) + self.font().pixelSize()*0.25
                    painter.drawText(tx, ty, tile)
        
        # Plot the monsters.
        for (c, r), tile in monsters.items():
        
            tile_image = self.monster_images[tile]
            painter.drawImage(c * 4 * self.xs, (6 + r) * 8 * self.ys,
                              tile_image)
        
        # Plot the start position.
        if self.level == self.order[0]:
        
            if r1 + 6 <= 19 and r2 + 6 >= 17 and c1 <= 20 and c2 >= 19:
            
                painter.setPen(QPen(Qt.white))
                painter.drawRect(19 * 4 * self.xs, 17 * 8 * self.ys,
                                 2 * 4 * self.xs - 1, 3 * 8 * self.ys - 1)
                
        
        # Plot the character's left scroll extent.
        if c1 <= 19 and c2 >= 19:
        
            pen = QPen(Qt.white)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(19 * 4 * self.xs, 0, 19 * 4 * self.xs, 24 * 8 * self.ys)
        
        # Plot the finishing position.
        if c1 <= self.finishing_offset + 20 and c2 >= self.finishing_offset + 19:
        
            pen = QPen(Qt.white)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect((self.finishing_offset + 19) * 4 * self.xs, 0,
                              8 * self.xs - 1, 24 * 8 * self.ys)
        
        painter.end()
    
    def sizeHint(self):
    
        return QSize(max(self.screen_width, self.maximum_width * 4) * self.xs,
                     self.screen_height * self.ys)
    
    def showMenu(self, pos, globalPos):
    
        r = max(0, self._row_from_y(pos.y()))
        c = self._column_from_x(pos.x())
        
        tile = self.rows[self.level][r][c]
        
        if tile in self.portals:
        
            menu = QMenu()
            colourAction = menu.addAction(self.tr("Set colour..."))
            destinationAction = menu.addAction(self.tr("Set destination..."))
            
            index, dest, colour = self.portals[tile]
            goAction = menu.addAction(self.tr("Go to portal %1").arg(dest))
            goAction.setEnabled(dest in self.portal_locations)
            
            action = menu.exec_(globalPos)
            if action == colourAction:
                dialog = ColourDialog(self, self.tr("Set Colour"))
                if dialog.exec_() == QDialog.Accepted:
                    self.portals[tile] = index, dest, dialog.colour
                    self.setPortalPalette(tile)
                    
            elif action == destinationAction:
                dialog = DestinationDialog(self, self.tr("Set Destination"), self.portals)
                if dialog.exec_() == QDialog.Accepted:
                    self.portals[tile] = index, dialog.destination, colour
            
            elif action == goAction:
                self.navigationRequested.emit(dest)
        
        elif tile in self.monster_images:
        
            axis = makelevels.monster_axes[tile]
            
            menu = QMenu()
            horizontalAction = menu.addAction(self.tr("Horizontal Motion"))
            horizontalAction.setCheckable(True)
            horizontalAction.setChecked(axis == 0)
            verticalAction = menu.addAction(self.tr("Vertical Motion"))
            verticalAction.setCheckable(True)
            verticalAction.setChecked(axis == 1)
            
            action = menu.exec_(globalPos)
            if action == horizontalAction and axis != 0:
                self.rows[self.level][r][c] = makelevels.monster_axis_flip[tile]
            elif action == verticalAction and axis != 1:
                self.rows[self.level][r][c] = makelevels.monster_axis_flip[tile]
    
    def _row_from_y(self, y):
    
        return (y - (6 * 8 * self.ys))/(8 * self.ys)
    
    def _column_from_x(self, x):
    
        return x/(4 * self.xs)
    
    def _y_from_row(self, r):
    
        return (6 + r) * 8 * self.ys
    
    def _x_from_column(self, c):
    
        return c * 4 * self.xs
    
    def writeTile(self, event, tile):
    
        r = self._row_from_y(event.y())
        c = self._column_from_x(event.x())
        
        if 0 <= r < 16 and 0 <= c < self.maximum_width:
        
            self.rows[self.level][r][c] = tile
            
            # If the tile is a portal then update the portal locations.
            if tile in self.portals:
                self.portal_locations[tile] = (self.level, c, r)
            
            # Update a larger region if the tile is occupied by a monster.
            if tile in self.monster_images:
                tw = 8 * self.xs
            else:
                tw = 4 * self.xs
            
            self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                              tw, 8 * self.ys))
    def newSpecial(self):
    
        if len(self.special) < 15:
        
            i = ord("a")
            while i <= ord("z"):
            
                if not self.special.has_key(chr(i)):
                    break
                i += 1
            
            if ord("a") <= ord(self.currentTile) <= ord("z") or self.currentTile == ".":
                tile = makelevels.tile_order[1]
            else:
                tile = self.currentTile
            
            self.special[chr(i)] = (tile, len(self.special) + 1, 1)
            return chr(i)
        
        else:
            return ""
    
    def addLevel(self, name):
    
        self.rows[name] = []
        self.order.insert(self.order.index(self.level) + 1, name)
        
        for i in range(16):
        
            row = ["."] * self.maximum_width
            self.rows[name].append(row)
    
    def removeLevel(self, name):
    
        if len(self.rows) == 1:
            return
        
        index = self.order.index(name)
        del self.order[index]
        del self.rows[name]
    
    def setPortalPalette(self, name):
    
        dest, index, colour = self.portals[name]
        
        for tile, image in self.tile_images.items():
        
            rgb = standard_palette[makelevels.colours[colour]]
            new_palette = standard_palette[:2] + [rgb] + standard_palette[3:]

            image.setColorTable(new_palette)
            self.tile_images[tile] = image


class SelectorModel(QAbstractListModel):

    def __init__(self, actionGroup, parent):
    
        QAbstractListModel.__init__(self, parent)
        self.actionGroup = actionGroup
    
    def rowCount(self, index):
    
        if not index.isValid():
            return len(self.actionGroup.actions()) - min(len(makelevels.tile_order), 16)
        else:
            return 0
    
    def flags(self, index):
    
        return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
    
    def data(self, index, role):
    
        if role != Qt.DisplayRole and role != Qt.CheckStateRole:
            return QVariant()
        
        actions = self.actionGroup.actions()
        row = index.row()
        minimum = min(len(makelevels.tile_order), 16)
        
        if 0 <= row < len(actions) - minimum and index.column() == 0:
            if role == Qt.DisplayRole:
                return QVariant(actions[row + minimum].text())
            elif role == Qt.CheckStateRole:
                return QVariant(actions[row + minimum].data().toBool())
        
        return QVariant()
    
    def setData(self, index, value, role):
    
        if index.isValid() and index.column() == 0 and role == Qt.CheckStateRole:
            row = index.row()
            actions = self.actionGroup.actions()
            minimum = min(len(makelevels.tile_order), 16)
            value = actions[row + minimum].data().toBool()
            actions[row + minimum].setData(not value)
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

class EditorWindow(QMainWindow):

    def __init__(self):
    
        QMainWindow.__init__(self)
        
        self.xs = 4
        self.ys = 2
        self.path = ""
        self.loadImages()
        
        self.levelWidget = LevelWidget(self.tile_images, self.monster_images)
        self.levelWidget.navigationRequested.connect(self.jumpToPortal)
        
        self.createMenus()
        self.createToolBars()
        
        self.levelWidget.initRows("Default")
        self.updateLevelActions()
        self.levelGroup.actions()[0].trigger()
        self.updatePortalActions()
        
        self.area = QScrollArea()
        self.area.setWidget(self.levelWidget)
        self.setCentralWidget(self.area)
    
    def sizeHint(self):
    
        levelSize = self.levelWidget.sizeHint()
        menuSize = self.menuBar().sizeHint()
        scrollBarSize = self.centralWidget().verticalScrollBar().size()
        toolBarSize = self.tilesToolBar.size()
        
        return QSize(max(levelSize.width(), menuSize.width(), toolBarSize.width()),
                     levelSize.height() + menuSize.height() + \
                     scrollBarSize.height() + 2 * toolBarSize.height())
    
    def loadImages(self):
    
        # Find the images.
        filepath = QFileInfo(__file__)
        d = filepath.dir()
        d.cdUp()
        d = QDir(d.absolutePath())
        
        self.tile_images = {}
        
        for key, image_path in makelevels.tile_ref.items():
        
            path = d.filePath(image_path)
            image = QImage(path).scaled(self.xs * 4, self.ys * 8)
            image = image.convertToFormat(QImage.Format_Indexed8,
                                          standard_palette)
            self.tile_images[key] = image
        
        self.monster_images = {}
        
        for key, image_path in makelevels.monster_ref.items():
        
            path = d.filePath(image_path)
            image = QImage(path).scaled(self.xs * 8, self.ys * 8)
            image = image.convertToFormat(QImage.Format_Indexed8,
                                          standard_palette)
            self.monster_images[key] = image
    
    def createMenus(self):
    
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        
        newAction = fileMenu.addAction(self.tr("&New"))
        newAction.setShortcut(QKeySequence.New)
        
        openAction = fileMenu.addAction(self.tr("&Open..."))
        openAction.setShortcut(QKeySequence.Open)
        openAction.triggered.connect(self.openMap)
        
        self.saveAction = fileMenu.addAction(self.tr("&Save"))
        self.saveAction.setShortcut(QKeySequence.Save)
        self.saveAction.triggered.connect(self.saveMap)
        self.saveAction.setEnabled(False)
        
        saveAsAction = fileMenu.addAction(self.tr("Save &As..."))
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveAsLevel)
        
        quitAction = fileMenu.addAction(self.tr("E&xit"))
        quitAction.setShortcut(self.tr("Ctrl+Q"))
        quitAction.triggered.connect(self.close)
        
        mapMenu = self.menuBar().addMenu(self.tr("&Map"))
        
        addLevelAction = mapMenu.addAction(self.tr("&Add level"))
        removeLevelAction = mapMenu.addAction(self.tr("&Remove level"))
        
        addLevelAction.triggered.connect(self.addLevel)
        removeLevelAction.triggered.connect(self.removeLevel)
    
    def createToolBars(self):
    
        self.tilesToolBar = self.addToolBar(self.tr("Tiles"))
        self.tileGroup = QActionGroup(self)
        self.tileGroup.triggered.connect(self.setCurrentTile)
        
        for symbol in makelevels.tile_order[:makelevels.normal_tiles]:
        
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action = self.tilesToolBar.addAction(icon, symbol)
            action.setCheckable(True)
            self.tileGroup.addAction(action)
        
        # Select the first tile in the tiles toolbar.
        self.tileGroup.actions()[0].trigger()
        
        self.monsterToolBar = self.addToolBar(self.tr("Monsters"))
        
        for symbol in makelevels.monster_order:
        
            icon = QIcon(QPixmap.fromImage(self.monster_images[symbol]))
            action = self.monsterToolBar.addAction(icon, symbol)
            action.setCheckable(True)
            self.tileGroup.addAction(action)
        
        self.specialToolBar = self.addToolBar(self.tr("Special"))
        action = self.specialToolBar.addAction("New")
        action.triggered.connect(self.addSpecial)
        
        self.portalToolBar = QToolBar(self.tr("Portals"))
        self.addToolBar(Qt.RightToolBarArea, self.portalToolBar)
        self.portalActions = []
        
        specialSelector = QComboBox()
        specialSelector.setModel(SelectorModel(self.tileGroup, self))
        self.specialToolBar.addWidget(specialSelector)
        
        self.levelToolBar = QToolBar(self.tr("Levels"))
        self.addToolBar(Qt.BottomToolBarArea, self.levelToolBar)
        self.levelToolBar.actionTriggered.connect(self.selectLevel)
        self.levelGroup = QActionGroup(self)
        
        docksMenu = self.menuBar().addMenu(self.tr("&Docks"))
        docksMenu.addAction(self.tilesToolBar.toggleViewAction())
        docksMenu.addAction(self.monsterToolBar.toggleViewAction())
        docksMenu.addAction(self.specialToolBar.toggleViewAction())
        docksMenu.addAction(self.portalToolBar.toggleViewAction())
        docksMenu.addAction(self.levelToolBar.toggleViewAction())
    
    def newLevel(self):
    
        pass
    
    def openMap(self):
    
        path = QFileDialog.getOpenFileName(self, self.tr("Open Level"),
                                           self.path)
        if not path.isEmpty():
            self._openMap(path)
    
    def _openMap(self, path):
    
        if self.levelWidget.loadMap(unicode(path)):
        
            self.path = path
            self.levelWidget.update()
            
            self.specialToolBar.clear()
            
            for action in self.specialToolBar.actions():
                self.tileGroup.removeAction(action)
            
            specialKeys = self.levelWidget.special.keys()
            specialKeys.sort()
            
            for symbol in specialKeys:
                self._addSpecialAction(symbol)
            
            action = self.specialToolBar.addAction("New")
            action.triggered.connect(self.addSpecial)
            
            specialSelector = QComboBox()
            specialSelector.setModel(SelectorModel(self.tileGroup, self))
            self.specialToolBar.addWidget(specialSelector)
            
            # Update the level and portal actions.
            self.updateLevelActions()
            self.levelGroup.actions()[0].trigger()
            self.updatePortalActions()
            
            self.tileGroup.actions()[0].trigger()
            
            self.saveAction.setEnabled(True)
            self.setWindowTitle(self.tr(path))
        else:
            QMessageBox.warning(self, self.tr("Open Level"),
                                self.tr("Failed to open level: %1").arg(path))
    
    def saveMap(self):
    
        if not self.levelWidget.saveMap(unicode(self.path)):
            QMessageBox.warning(self, self.tr("Save Level"),
                                self.tr("Failed to save level: %1").arg(self.path))
    
    def saveAsLevel(self):
    
        path = QFileDialog.getSaveFileName(self, self.tr("Save Level"),
                                           self.path)
        if not path.isEmpty():
        
            if self.levelWidget.saveMap(unicode(path)):
                self.path = path
                self.saveAction.setEnabled(True)
                self.setWindowTitle(self.tr(path))
            else:
                QMessageBox.warning(self, self.tr("Save Level"),
                                    self.tr("Failed to save level: %1").arg(path))
    
    def setCurrentTile(self, action):
    
        self.levelWidget.currentTile = unicode(action.text())
    
    def addSpecial(self):
    
        symbol = self.levelWidget.newSpecial()
        
        if symbol:
            self._addSpecialAction(symbol)
    
    def _addSpecialAction(self, symbol):
    
        icon = self.updateSpecialIcon(symbol)
        action = self.specialToolBar.addAction(icon, symbol)
        action.setCheckable(True)
        self.tileGroup.addAction(action)
        
        action.trigger()
    
    def editSpecial(self):
    
        pass
    
    def removeSpecial(self):
    
        symbol = unicode(self.sender().text())
        ### Remove the associated action and update the level widget.
    
    def updateSpecialIcon(self, symbol):
    
        font = QFont("Monospace")
        font.setPixelSize(min(4 * self.xs - 2, 8 * self.ys - 2))
        
        tile = self.levelWidget.special[symbol][0]
        pixmap = QPixmap.fromImage(self.tile_images[tile])
        
        painter = QPainter()
        painter.begin(pixmap)
        painter.setPen(Qt.white)
        painter.setFont(font)
        
        tx = (0.5 * 4 * self.xs) - font.pixelSize()*0.5
        ty = (0.5 * 8 * self.ys) + font.pixelSize()*0.5
        painter.drawText(tx, ty, symbol)
        painter.end()
        
        return QIcon(pixmap)
    
    def updateLevelActions(self):
    
        self.levelToolBar.clear()
        self.levelGroup.deleteLater()
        self.levelGroup = QActionGroup(self)
        
        for name in self.levelWidget.order:
        
            action = self.levelToolBar.addAction(name)
            action.setCheckable(True)
            self.levelGroup.addAction(action)
    
    def addLevel(self):
    
        name, ok = QInputDialog.getText(self, self.tr("Add Level"),
                                    self.tr("Level name:"))
        
        if ok and not name.isEmpty():
            self.levelWidget.addLevel(unicode(name))
            action = self.levelToolBar.addAction(name)
            action.setCheckable(True)
            self.levelGroup.addAction(action)
    
    def removeLevel(self):
    
        action = self.levelGroup.checkedAction()
        name = unicode(action.text())
        index = self.levelWidget.order.index(name)
        
        self.levelWidget.removeLevel(name)
        self.updateLevelActions()
        
        self.levelGroup.actions()[min(index, len(self.levelWidget.order) - 1)].trigger()
    
    def selectLevel(self, action):
    
        name = action.text()
        self.levelWidget.level = unicode(name)
        self.levelWidget.adjustSize()
        self.levelWidget.update()
    
    def jumpToPortal(self, name):
    
        name = unicode(name)
        level, c, r = self.levelWidget.portal_locations[name]
        
        index = self.levelWidget.order.index(level)
        self.levelGroup.actions()[index].trigger()
        self.area.horizontalScrollBar().setValue(self.levelWidget._x_from_column(c - 19))
        self.area.verticalScrollBar().setValue(self.levelWidget._y_from_row(r))
        
        self.levelWidget.setPortalPalette(name)
    
    def updatePortalActions(self):
    
        self.portalToolBar.clear()
        
        for action in self.portalActions:
            self.tileGroup.removeAction(action)
        
        self.portalActions = []
        
        for portal in self.levelWidget.portals:
        
            action = self.portalToolBar.addAction(portal)
            action.setCheckable(True)
            self.tileGroup.addAction(action)
            self.portalActions.append(action)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    window = EditorWindow()
    
    if len(app.arguments()) > 1:
        window._openMap(app.arguments()[1])
        
    window.show()
    sys.exit(app.exec_())
