############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
# standard solutions
import logging
# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from support.mw_widget import MwWidget
from support.coordinate_dialog_ui import Ui_CoordinateDialog


def getXYEllipse(az, alt, height, width, border, esize):                                                                    # calculation of the ellipse
    x = border - esize / 2 + int(az / 360 * (width - 2 * border))
    y = height - border - esize / 2 - int(alt / 90 * (height - 2 * border))
    return int(x), int(y)


def getXYRectangle(az, width, border):
    x = (az - 15) * (width - 2 * border) / 360 + border
    y = border
    return int(x), int(y)


class ShowCoordinatePopup(MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, uiMain, model, mount, dome, modelLogQueue):
        super(ShowCoordinatePopup, self).__init__()

        self.borderModelPointsView = 20
        self.textheightModelPointsView = 10
        self.ellipseSizeModelPointsView = 12
        self.pointerTrackingWidget = QGraphicsEllipseItem(0, 0, 0, 0)
        self.pointerDomeWidget = QGraphicsRectItem(0, 0, 0, 0)
        self.groupTrackPreviewItems = QGraphicsItemGroup()
        self.uiMain = uiMain
        self.model = model
        self.mount = mount
        self.dome = dome
        self.modelLogQueue = modelLogQueue
        self.showStatus = False
        self.ui = Ui_CoordinateDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.ui.windowTitle.setPalette(self.palette)
        self.showAllPoints()
        self.mount.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.mount.signalMountTrackPreview.connect(self.drawTrackPreview)
        self.model.signalModelRedraw.connect(self.showAllPoints)
        self.dome.signalDomPointer.connect(self.setDomePointer)
        self.ui.btn_selectClose.clicked.connect(self.closeAnalyseWindow)
        self.mainLoop()

    def closeAnalyseWindow(self):
        self.showStatus = False
        self.close()

    def setAzAltPointer(self, az, alt):
        x, y = getXYEllipse(az, alt, self.ui.modelPointsPlot.height(),
                            self.ui.modelPointsPlot.width(),
                            self.borderModelPointsView,
                            2 * self.ellipseSizeModelPointsView)
        self.pointerTrackingWidget.setPos(x, y)
        self.pointerTrackingWidget.setVisible(True)
        self.pointerTrackingWidget.update()

    def setDomePointer(self, az):
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        x, y = getXYRectangle(az, width, border)
        self.pointerDomeWidget.setPos(x, y)
        self.pointerDomeWidget.setVisible(True)
        self.pointerDomeWidget.update()

    def drawTrackPreview(self):
        self.groupTrackPreviewItems = QGraphicsItemGroup()
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        height = self.ui.modelPointsPlot.height()
        esize = self.ellipseSizeModelPointsView
        for i in range(0, 75, 2):                                                                                           # round model point from actual az alt position 24 hours
            ra = self.mount.ra                                                                                              # Transform text to hours format
            ra -= float(i) / 12.0
            dec = self.mount.dec                                                                                            # Transform text to degree format
            az, alt = self.model.transformCelestialHorizontal(ra, dec)                                                      # transform to az alt
            if alt > 0:                                                                    # we only take point above horizon
                x, y = getXYEllipse(az, alt, height, width, border, esize / 2)
                item = QGraphicsEllipseItem(x, y, esize / 2, esize / 2)
                item.setPen(pen)
                self.groupTrackPreviewItems.addToGroup(item)
        self.groupTrackPreviewItems.setVisible(True)
        self.groupTrackPreviewItems.update()
        QApplication.processEvents()

    def constructHorizon(self, scene, horizon, height, width, border):
        for i, p in enumerate(horizon):
            if (i != len(horizon)) and (i != 0):                                                                            # horizon in between
                pen = QPen(self.COLOR_GREEN_LIGHT, 3, Qt.SolidLine, Qt.RoundCap,
                           Qt.RoundJoin)                                                                                    # define the pen style thickness 3
                scene.addLine(border + int(p[0] / 360 * (width - 2 * border)),
                              height - border - int(p[1] * (height - 2 * border) / 90),
                              border + int(horizon[i - 1][0] / 360 * (width - 2 * border)),
                              height - border - int(horizon[i - 1][1] * (height - 2 * border) / 90),
                              pen)                                                                                          # and add it to the scene
        return scene

    def constructModelGrid(self, height, width, border, textheight, scene):                                                 # adding the plot area
        scene.setBackgroundBrush(self.COLOR_WINDOW)                                                                         # background color
        pen = QPen(self.COLOR_BACKGROUND, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # building the grid of the plot and the axes
        for i in range(0, 361, 30):                                                                                         # set az ticks
            scene.addLine(border + int(i / 360 * (width - 2 * border)), height - border,
                          border + int(i / 360 * (width - 2 * border)), border, pen)
        for i in range(0, 91, 10):                                                                                          # set alt ticks
            scene.addLine(border, height - border - int(i * (height - 2 * border) / 90),
                          width - border, height - border - int(i * (height - 2*border) / 90), pen)
        scene.addRect(border, border, width - 2*border, height - 2*border, pen)                                             # set frame around graphics
        for i in range(0, 361, 30):                                                                                         # now the texts at the plot x
            text_item = QGraphicsTextItem('{0:03d}'.format(i), None)                                                        # set labels
            text_item.setDefaultTextColor(self.COLOR_ASTRO)                                                                 # coloring of label
            text_item.setPos(int(border / 2) + int(i / 360 * (width - 2 * border)), height - border)                        # placing the text
            scene.addItem(text_item)                                                                                        # adding item to scene to be shown
        for i in range(10, 91, 10):                                                                                         # now the texts at the plot y
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(width - border, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(0, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
        return scene

    def showAllPoints(self):
        height = self.ui.modelPointsPlot.height()
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        textheight = self.textheightModelPointsView
        esize = self.ellipseSizeModelPointsView
        scene = QGraphicsScene(0, 0, width-2, height-2)                                                                     # set the size of the scene to to not scrolled
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                            # outer circle is white
        brush = QBrush(self.COLOR_BACKGROUND)
        self.pointerDomeWidget = scene.addRect(0, 0, int((width - 2 * border) * 30 / 360), int(height - 2 * border), pen, brush)
        self.pointerDomeWidget.setVisible(False)
        self.pointerDomeWidget.setOpacity(0.5)
        scene = self.constructModelGrid(height, width, border, textheight, scene)
        for i, p in enumerate(self.model.BasePoints):                                                                       # show the points
            pen = QPen(self.COLOR_RED, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                          # outer circle is white
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize)
            scene.addEllipse(x, y, esize, esize, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize/2)
            item = scene.addEllipse(0, 0, esize/2, esize/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(x+1, y+1)
            scene.addItem(text_item)
            self.model.BasePoints[i] = (p[0], p[1], item, True)                                                             # storing the objects in the list
        for i, p in enumerate(self.model.RefinementPoints):                                                                 # show the points
            pen = QPen(self.COLOR_GREEN, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                        # outer circle is white
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize)
            scene.addEllipse(x, y, esize, esize, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize/2)
            item = scene.addEllipse(0, 0, esize/2, esize/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_WHITE)
            text_item.setPos(x+1, y+1)
            scene.addItem(text_item)
            self.model.RefinementPoints[i] = (p[0], p[1], item, True)                                                       # storing the objects in the list
        scene = self.constructHorizon(scene, self.model.horizonPoints, height, width, border)
        pen = QPen(self.COLOR_POINTER, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.pointerTrackingWidget = scene.addEllipse(0, 0, 2 * esize, 2 * esize, pen)
        scene.addItem(self.groupTrackPreviewItems)
        self.ui.modelPointsPlot.setScene(scene)
        return

    def mainLoop(self):
        while not self.modelLogQueue.empty():                                                                               # checking if in queue is something to do
            text = self.modelLogQueue.get()                                                                                 # if yes, getting the work command
            if text == 'delete':                                                                                            # delete logfile for modeling
                self.ui.modellingLog.setText('')                                                                            # reset window text
            else:
                self.ui.modellingLog.setText(self.ui.modellingLog.toPlainText() + text)                                     # otherwise add text at the end
            self.ui.modellingLog.moveCursor(QTextCursor.End)                                                                # and move cursor up
            self.modelLogQueue.task_done()
        # noinspection PyCallByClass,PyTypeChecker
        QTimer.singleShot(200, self.mainLoop)                                                                               # 200ms repeat time cyclic
