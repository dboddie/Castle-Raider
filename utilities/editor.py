#!/usr/bin/env python

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
        self.maximum_width = 512
        
        self.initRows()
        
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
            
            for ch, (n, flags, initial) in self.special.items():
                f.write("%s %s %i %i\n" % (ch, n, flags, initial))
            
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
                
                    n, flags, initial = self.special[tile]
                    if initial:
                        tile = n
                    else:
                        tile = "."
                
                tile_image = self.tile_images[tile]
                painter.drawImage(c * 4 * self.xs, (6 + r) * 8 * self.ys,
                                  tile_image)
        
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
        
        if 0 <= r < 16 and 0 <= c < 512:
        
            self.rows[r][c] = tile
            self.update(QRect(self._x_from_column(c), self._y_from_row(r),
                              4 * self.xs, 8 * self.ys))


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
        tileGroup = QActionGroup(self)
        
        for symbol in makelevels.tile_order:
        
            icon = QIcon(QPixmap.fromImage(self.tile_images[symbol]))
            action = self.tilesToolBar.addAction(icon, symbol)
            action.setCheckable(True)
            tileGroup.addAction(action)
            action.triggered.connect(self.setCurrentTile)
        
        tileGroup.actions()[0].setChecked(True)
    
    def newLevel(self):
    
        pass
    
    def openLevel(self):
    
        path = QFileDialog.getOpenFileName(self, self.tr("Open Level"),
                                           self.path)
        if not path.isEmpty():
        
            if self.levelWidget.loadLevel(unicode(path)):
                self.path = path
                self.levelWidget.update()
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
