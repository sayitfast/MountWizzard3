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
import datetime
import copy
# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from support.mw_widget import MwWidget
from support.coordinate_dialog_ui import Ui_CoordinateDialog


def getXYRectangle(az, width, border):
    x = (az - 15) * (width - 2 * border) / 360 + border
    y = border
    return int(x), int(y)


def getXY(az, alt, height, width, border):                                                                                  # calculation of the position
    x = border + int(az / 360 * (width - 2 * border))
    y = height - border - int(alt / 90 * (height - 2 * border))
    return int(x), int(y)


class ShowCoordinatePopup(MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, uiMain, model, mount, dome, modelLogQueue):
        super(ShowCoordinatePopup, self).__init__()

        self.borderModelPointsView = 20
        self.textheightModelPointsView = 10
        self.ellipseSizeModelPointsView = 12
        self.pointerAzAlt = QGraphicsItemGroup()
        self.pointerTrack = QGraphicsItemGroup()
        self.pointerTrackLine = []
        self.itemFlipTime = QGraphicsItemGroup()
        self.itemFlipTimeText = QGraphicsTextItem('')
        self.pointerDome = QGraphicsRectItem(0, 0, 0, 0)
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
        self.mount.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.mount.signalMountTrackPreview.connect(self.drawTrackPreview)
        self.uiMain.checkRunTrackingWidget.toggled.connect(self.changeStatusTrackingWidget)
        self.model.signalModelRedraw.connect(self.redrawCoordinateWindow)
        self.dome.signalDomPointer.connect(self.setDomePointer)
        self.ui.btn_selectClose.clicked.connect(self.hideCoordinateWindow)
        self.redrawCoordinateWindow()
        self.show()
        self.setVisible(False)

    def hideCoordinateWindow(self):
        self.showStatus = False
        self.setVisible(False)

    def setAzAltPointer(self, az, alt):
        x, y = getXY(az, alt, self.ui.modelPointsPlot.height(),
                     self.ui.modelPointsPlot.width(),
                     self.borderModelPointsView)
        self.pointerAzAlt.setPos(x, y)
        self.pointerAzAlt.setVisible(True)
        self.pointerAzAlt.update()

    def setDomePointer(self, az):
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        x, y = getXYRectangle(az, width, border)
        self.pointerDome.setPos(x, y)
        self.pointerDome.setVisible(True)
        self.pointerDome.update()

    def changeStatusTrackingWidget(self):
        if self.uiMain.checkRunTrackingWidget.isChecked():
            self.drawTrackPreview()
        else:
            self.pointerTrack.setVisible(False)

    def drawTrackPreview(self):
        if not self.uiMain.checkRunTrackingWidget.isChecked():
            return
        raCopy = copy.copy(self.mount.ra)
        decCopy = copy.copy(self.mount.dec)
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        height = self.ui.modelPointsPlot.height()
        self.pointerTrack.setVisible(True)
        for i in range(0, 50):                                                                                              # round model point from actual az alt position 24 hours
            ra = raCopy - float(i) * 10 / 50                                                                                # 12 hours line max
            az, alt = self.mount.transformNovas(ra, decCopy, 1)                                                             # transform to az alt
            x, y = getXY(az, alt, height, width, border)
            self.pointerTrackLine[i].setPos(x, y)
            if alt > 0:
                self.pointerTrackLine[i].setVisible(True)
            else:
                self.pointerTrackLine[i].setVisible(False)
        az, alt = self.mount.transformNovas(self.mount.ra - float(self.mount.timeToFlip) / 60, decCopy, 1)                  # transform to az alt
        x, y = getXY(az, alt, height, width, border)
        self.itemFlipTime.setPos(x, y)
        delta = float(self.mount.timeToFlip)
        fliptime = datetime.datetime.now() + datetime.timedelta(minutes=delta)
        self.itemFlipTimeText.setPlainText(' {0:%H:%M}\n{1:03.0f} min'.format(fliptime, delta))

    def constructTrackWidget(self, esize):
        group = QGraphicsItemGroup()
        groupFlipTime = QGraphicsItemGroup()
        track = []
        group.setVisible(False)
        pen = QPen(self.COLOR_TRACKWIDGETPOINTS, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        for i in range(0, 50):
            item = QGraphicsEllipseItem(-esize / 8, -esize / 8, esize / 4, esize / 4)
            item.setPen(pen)
            group.addToGroup(item)
            track.append(item)
        itemText = QGraphicsTextItem(' 19:20\n000 min', None)
        itemText.setDefaultTextColor(self.COLOR_TRACKWIDGETTEXT)
        groupFlipTime.addToGroup(itemText)
        item = QGraphicsEllipseItem(- esize / 4, -esize / 4, esize / 2, esize / 2)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        item = QGraphicsRectItem(0, -esize, 0, 2 * esize)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        group.addToGroup(groupFlipTime)
        return group, groupFlipTime, itemText, track

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

    def constructAzAltPointer(self, esize):
        group = QGraphicsItemGroup()
        group.setVisible(False)
        pen = QPen(self.COLOR_POINTER, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item = QGraphicsEllipseItem(-esize, -esize, 2 * esize, 2 * esize)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(-esize, 0, -esize / 2, 0)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(0, -esize, 0, -esize / 2)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(esize / 2, 0, esize, 0)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(0, esize / 2, 0, esize)
        item.setPen(pen)
        group.addToGroup(item)
        return group

    def redrawCoordinateWindow(self):
        height = self.ui.modelPointsPlot.height()
        width = self.ui.modelPointsPlot.width()
        border = self.borderModelPointsView
        textheight = self.textheightModelPointsView
        esize = self.ellipseSizeModelPointsView
        scene = QGraphicsScene(0, 0, width-2, height-2)                                                                     # set the size of the scene to to not scrolled
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                            # outer circle is white
        brush = QBrush(self.COLOR_BACKGROUND)
        self.pointerDome = scene.addRect(0, 0, int((width - 2 * border) * 30 / 360), int(height - 2 * border), pen, brush)
        self.pointerDome.setVisible(False)
        self.pointerDome.setOpacity(0.5)
        scene = self.constructModelGrid(height, width, border, textheight, scene)
        for i, p in enumerate(self.model.BasePoints):                                                                       # show the points
            pen = QPen(self.COLOR_RED, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                          # outer circle is white
            x, y = getXY(p[0], p[1], height, width, border)
            scene.addEllipse(x - esize / 2, y - esize / 2, esize, esize, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXY(p[0], p[1], height, width, border)
            item = scene.addEllipse(-esize / 4, -esize / 4, esize/2, esize/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(x - esize / 8, y - esize / 8)
            scene.addItem(text_item)
            self.model.BasePoints[i] = (p[0], p[1], item, True)                                                             # storing the objects in the list
        for i, p in enumerate(self.model.RefinementPoints):                                                                 # show the points
            pen = QPen(self.COLOR_GREEN, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                        # outer circle is white
            x, y = getXY(p[0], p[1], height, width, border)
            scene.addEllipse(x - esize / 2, y - esize / 2, esize, esize, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXY(p[0], p[1], height, width, border)
            item = scene.addEllipse(-esize/4, -esize/4, esize/2, esize/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_WHITE)
            text_item.setPos(x - esize / 8, y - esize / 8)
            scene.addItem(text_item)
            self.model.RefinementPoints[i] = (p[0], p[1], item, True)                                                       # storing the objects in the list
        scene = self.constructHorizon(scene, self.model.horizonPoints, height, width, border)
        self.pointerAzAlt = self.constructAzAltPointer(esize)
        self.pointerTrack, self.itemFlipTime, self.itemFlipTimeText, self.pointerTrackLine = self.constructTrackWidget(esize)
        scene.addItem(self.pointerAzAlt)
        scene.addItem(self.pointerTrack)
        self.ui.modelPointsPlot.setScene(scene)
