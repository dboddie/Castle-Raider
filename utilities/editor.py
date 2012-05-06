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

class LevelWidget(QWidget):

    def __init__(self, tile_images, parent = None):
    
        QWidget.__init__(self, parent)
        self.xs = 4
        self.ys = 2
        self.screen_width = 40 * 4
        self.screen_height = 22 * 8
        
        self.tile_images = tile_images
        self.currentTile = "."
        self.maximum_width = 1024
        
        self.initRows()
        
        font = QFont("Monospace")
        font.setPixelSize(min(4 * self.xs - 2, 8 * self.ys - 2))
        self.setFont(font)
        
        self.setAutoFillBackground(True)
        p = QPalette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)
    
    def initRows(self):
    
        self.rows = []
        self.level_width = 0
        
        for i in range(16):
        
            row = ["."] * self.maximum_width
            self.level_width = max(len(row), self.level_width)
            self.rows.append(row)
        
        self.special = {}
    
    def loadLevel(self, path):
    
        try:
            rows, special = makelevels.load_level(path)
            
            self.level_width = 0
            self.rows = []
            
            for row in rows:
            
                new_row = map(str, row)
                
                if len(new_row) < self.maximum_width:
                    new_row += (self.maximum_width - len(new_row)) * ["."]
                elif len(new_row) > self.maximum_width:
                    new_row = new_row[:self.maximum_width]
                
                self.rows.append(new_row)
                self.level_width = max(len(row), self.level_width)
            
            self.special = special
            return True
        
        except IOError:
            return False
    
    def saveLevel(self, path):
    
        try:
            f = open(unicode(path), "w")
            
            level_width = 40
            
            for row in self.rows:
            
                i = len(row) - 1
                
                while i > 39:
                    if row[i] != ".":
                        break
                    else:
                        i -= 1
                
                level_width = max(level_width, i + 1)
            
            for row in self.rows:
                f.write("".join(row[:level_width]) + "\n")
            
            f.write("\n")
            
            special_items = self.special.items()
            special_items.sort()
            
            for ch, (n, index, flags) in special_items:
            
                flags_word = []
                for k, v in flags_values.items():
                    if flags & v:
                        flags_word.append(k)
                f.write("%s %s %s\n" % (ch, n, ",".join(flags_word)))
            
            f.close()
            
            self.level_width = min(self.level_width, level_width)
            return True
        
        except IOError:
            return False
    
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.button() == Qt.RightButton:
            self.writeTile(event, ".")
        else:
            event.ignore()
    
    def mouseMoveEvent(self, event):
    
        if event.buttons() & Qt.LeftButton:
            self.writeTile(event, self.currentTile)
        elif event.buttons() & Qt.RightButton:
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
        
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
            
                tile = self.rows[r][c]
                
                if tile in self.special:
                
                    n, index, flags = self.special[tile]
                    tile_image = self.tile_images[n]
                    #if initial:
                    #    tile_image = self.tile_images[n]
                    #else:
                    #    tile_image = self.tile_images["."]
                else:
                    tile_image = self.tile_images[tile]
                
                painter.drawImage(c * 4 * self.xs, (6 + r) * 8 * self.ys,
                                  tile_image)
                
                if tile in self.special:
                    tx = ((c + 0.5) * 4 * self.xs) - self.font().pixelSize()*0.5
                    ty = ((6.5 + r) * 8 * self.ys) + self.font().pixelSize()*0.5
                    painter.drawText(tx, ty, tile)
        
        painter.end()
    
    def sizeHint(self):
    
        return QSize(max(self.screen_width, self.maximum_width * 4) * self.xs,
                     self.screen_height * self.ys)
    
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
        
            self.rows[r][c] = tile
            self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                              4 * self.xs, 8 * self.ys))
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
        
        self.levelWidget = LevelWidget(self.tile_images)
        
        self.createMenus()
        self.createToolBars()
        
        area = QScrollArea()
        area.setWidget(self.levelWidget)
        self.setCentralWidget(area)
    
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
            self.tile_images[key] = image
    
    def createMenus(self):
    
        fileMenu = self.menuBar().addMenu(self.tr("&File"))
        
        newAction = fileMenu.addAction(self.tr("&New"))
        newAction.setShortcut(QKeySequence.New)
        
        openAction = fileMenu.addAction(self.tr("&Open..."))
        openAction.setShortcut(QKeySequence.Open)
        openAction.triggered.connect(self.openLevel)
        
        self.saveAction = fileMenu.addAction(self.tr("&Save"))
        self.saveAction.setShortcut(QKeySequence.Save)
        self.saveAction.triggered.connect(self.saveLevel)
        self.saveAction.setEnabled(False)
        
        saveAsAction = fileMenu.addAction(self.tr("Save &As..."))
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveAsLevel)
        
        quitAction = fileMenu.addAction(self.tr("E&xit"))
        quitAction.setShortcut(self.tr("Ctrl+Q"))
        quitAction.triggered.connect(self.close)
    
    def createToolBars(self):
    
        self.tilesToolBar = self.addToolBar(self.tr("Tiles"))
        self.tileGroup = QActionGroup(self)
        
        for symbol in makelevels.tile_order[:16]:
        
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action = self.tilesToolBar.addAction(icon, symbol)
            action.setCheckable(True)
            self.tileGroup.addAction(action)
            action.triggered.connect(self.setCurrentTile)
        
        self.tileGroup.actions()[0].trigger()
        
        self.specialToolBar = self.addToolBar(self.tr("Special"))
        action = self.specialToolBar.addAction("New")
        action.triggered.connect(self.addSpecial)
        
        specialSelector = QComboBox()
        specialSelector.setModel(SelectorModel(self.tileGroup, self))
        self.specialToolBar.addWidget(specialSelector)
        
        tilesMenu = self.menuBar().addMenu(self.tr("&Tiles"))
    
    def newLevel(self):
    
        pass
    
    def openLevel(self):
    
        path = QFileDialog.getOpenFileName(self, self.tr("Open Level"),
                                           self.path)
        if not path.isEmpty():
        
            if self.levelWidget.loadLevel(unicode(path)):
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
                
                self.saveAction.setEnabled(True)
                self.setWindowTitle(self.tr(path))
            else:
                QMessageBox.warning(self, self.tr("Open Level"),
                                    self.tr("Failed to open level: %1").arg(path))
    
    def saveLevel(self):
    
        if not self.levelWidget.saveLevel(unicode(self.path)):
            QMessageBox.warning(self, self.tr("Save Level"),
                                self.tr("Failed to save level: %1").arg(self.path))
    
    def saveAsLevel(self):
    
        path = QFileDialog.getSaveFileName(self, self.tr("Save Level"),
                                           self.path)
        if not path.isEmpty():
        
            if self.levelWidget.saveLevel(unicode(path)):
                self.path = path
                self.saveAction.setEnabled(True)
                self.setWindowTitle(self.tr(path))
            else:
                QMessageBox.warning(self, self.tr("Save Level"),
                                    self.tr("Failed to save level: %1").arg(path))
    
    def setCurrentTile(self):
    
        self.levelWidget.currentTile = unicode(self.sender().text())
    
    def addSpecial(self):
    
        symbol = self.levelWidget.newSpecial()
        
        if symbol:
            self._addSpecialAction(symbol)
    
    def _addSpecialAction(self, symbol):
    
        icon = self.updateSpecialIcon(symbol)
        action = self.specialToolBar.addAction(icon, symbol)
        action.setCheckable(True)
        self.tileGroup.addAction(action)
        
        action.triggered.connect(self.setCurrentTile)
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
    
    def sizeHint(self):
    
        levelSize = self.levelWidget.sizeHint()
        menuSize = self.menuBar().sizeHint()
        scrollBarSize = self.centralWidget().verticalScrollBar().size()
        toolBarSize = self.tilesToolBar.size()
        
        return QSize(max(levelSize.width(), menuSize.width(), toolBarSize.width()),
                     levelSize.height() + menuSize.height() + \
                     scrollBarSize.height() + toolBarSize.height())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    window = EditorWindow()
    window.show()
    sys.exit(app.exec_())
