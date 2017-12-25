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
import copy
import datetime
import logging
import os
import platform
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from baseclasses import widget
from astrometry import transform
import matplotlib
from gui import coordinate_dialog_ui


def getXYRectangle(az, width, border):
    x = (az - 15) * (width - 2 * border) / 360 + border
    y = border
    return int(x + 0.5), int(y + 0.5)


def getXY(az, alt, height, width, border):                                                                                  # calculation of the position
    x = border + (az / 360 * (width - 2 * border))
    y = height - border - (alt / 90 * (height - 2 * border))
    return int(x + 0.5), int(y + 0.5)


BORDER_VIEW = 30                                                                                                            # 20 point from graphics border
TEXTHEIGHT_VIEW = 15                                                                                                        # text size for drawing
TEXTHEIGHT = 10
ELLIPSE_VIEW = 12                                                                                                           # size of the circles of points


class ModelPlotWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(ModelPlotWindow, self).__init__()
        self.app = app
        self.transform = transform.Transform(self.app)
        self.pointerAzAlt = QGraphicsItemGroup()
        self.pointerTrack = QGraphicsItemGroup()
        self.pointerTrackLine = []
        self.itemFlipTime = QGraphicsItemGroup()
        self.itemFlipTimeText = QGraphicsTextItem('')
        self.pointerDome = QGraphicsRectItem(0, 0, 0, 0)
        self.showStatus = False
        self.ui = coordinate_dialog_ui.Ui_CoordinateDialog()
        self.ui.setupUi(self)

        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)

        self.initUI()
        self.initConfig()
        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerMountDispatcher.signalMountTrackPreview.connect(self.drawTrackPreview)
        self.ui.checkRunTrackingWidget.toggled.connect(self.changeStatusTrackingWidget)
        # self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.redrawModelingWindow)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.drawHemisphere)

        if platform.system() == 'Windows':
            self.app.workerAscomDome.signalDomPointer.connect(self.setDomePointer)
        # self.redrawModelingWindow()
        self.drawHemisphere()
        self.setVisible(False)

    def initConfig(self):
        try:
            if 'CoordinatePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['CoordinatePopupWindowPositionX'], self.app.config['CoordinatePopupWindowPositionY'])
            if 'CoordinatePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['CoordinatePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['CoordinatePopupWindowPositionX'] = self.pos().x()
        self.app.config['CoordinatePopupWindowPositionY'] = self.pos().y()
        self.app.config['CoordinatePopupWindowShowStatus'] = self.showStatus

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def selectHorizonPointsMode(self):
        msg = self.app.workerModelingDispatcher.modelingRunner.modelPoints.loadHorizonPoints(self.app.ui.le_horizonPointsFileName.text(),
                                                                                             self.app.ui.checkUseFileHorizonLine.isChecked(),
                                                                                             self.app.ui.checkUseMinimumHorizonLine.isChecked(),
                                                                                             self.app.ui.altitudeMinimumHorizon.value())
        if msg:
            self.app.messageQueue.put(msg + '\n')
        # self.redrawModelingWindow()
        self.drawHemisphere()

    def selectHorizonPointsFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Text files (*.txt)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/config', 'Text files (*.txt)')
        if a[0] != '':
            self.app.ui.le_horizonPointsFileName.setText(os.path.basename(a[0]))
            self.selectHorizonPointsMode()
            self.app.ui.checkUseMinimumHorizonLine.setChecked(False)
            # self.redrawModelingWindow()

    def setAzAltPointer(self, az, alt):
        return
        x, y = getXY(az, alt, self.ui.modelPointsPlot.height(), self.ui.modelPointsPlot.width(), BORDER_VIEW)
        self.pointerAzAlt.setPos(x, y)
        self.pointerAzAlt.setVisible(True)
        self.pointerAzAlt.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    def setDomePointer(self, az):
        return
        width = self.ui.modelPointsPlot.width()
        x, y = getXYRectangle(az, width, BORDER_VIEW)
        self.pointerDome.setPos(x, y)
        self.pointerDome.setVisible(True)
        self.pointerDome.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    def changeStatusTrackingWidget(self):
        return
        if self.ui.checkRunTrackingWidget.isChecked():
            self.drawTrackPreview()
        else:
            self.pointerTrack.setVisible(False)

    def drawTrackPreview(self):
        return
        if not self.ui.checkRunTrackingWidget.isChecked() or 'RaJ2000' not in self.app.workerMountDispatcher.data:
            return
        raCopy = copy.copy(self.app.workerMountDispatcher.data['RaJ2000'])
        decCopy = copy.copy(self.app.workerMountDispatcher.data['DecJ2000'])
        width = self.ui.modelPointsPlot.width()
        height = self.ui.modelPointsPlot.height()
        self.pointerTrack.setVisible(True)
        for i in range(0, 50):
            ra = raCopy - float(i) * 10 / 50
            az, alt = self.transform.transformERFA(ra, decCopy, 1)
            x, y = getXY(az, alt, height, width, BORDER_VIEW)
            self.pointerTrackLine[i].setPos(x, y)
            if alt > 0:
                self.pointerTrackLine[i].setVisible(True)
            else:
                self.pointerTrackLine[i].setVisible(False)
        az, alt = self.transform.transformERFA(self.app.workerMountDispatcher.data['RaJ2000'] - float(self.app.workerMountDispatcher.data['TimeToFlip']) / 60, decCopy, 1)
        x, y = getXY(az, alt, height, width, BORDER_VIEW)
        self.itemFlipTime.setPos(x, y)
        delta = float(self.app.workerMountDispatcher.data['TimeToFlip'])
        fliptime = datetime.datetime.now() + datetime.timedelta(minutes=delta)
        self.itemFlipTimeText.setPlainText(' {0:%H:%M}\n{1:3.0f} min'.format(fliptime, delta))
        self.pointerTrack.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    def constructTrackWidget(self, esize):
        group = QGraphicsItemGroup()
        groupFlipTime = QGraphicsItemGroup()
        track = []
        group.setVisible(False)
        poly = QPolygonF()
        poly.append(QPointF(0, 0))
        poly.append(QPointF(45, 0))
        poly.append(QPointF(45, 35))
        poly.append(QPointF(0, 35))
        poly.append(QPointF(0, 0))
        item = QGraphicsPolygonItem(poly)
        pen = QPen(self.COLOR_BACKGROUND, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item.setPen(pen)
        item.setBrush(QBrush(self.COLOR_BACKGROUND))
        item.setOpacity(0.8)
        groupFlipTime.addToGroup(item)
        pen = QPen(self.COLOR_TRACKWIDGETPOINTS, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        for i in range(0, 50):
            item = QGraphicsEllipseItem(-esize / 8, -esize / 8, esize / 4, esize / 4)
            item.setPen(pen)
            group.addToGroup(item)
            track.append(item)
        itemText = QGraphicsTextItem(' 19:20\n  0 min', None)
        itemText.setDefaultTextColor(self.COLOR_TRACKWIDGETTEXT)
        groupFlipTime.addToGroup(itemText)
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item = QGraphicsEllipseItem(- esize / 4, -esize / 4, esize / 2, esize / 2)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        item = QGraphicsRectItem(0, -esize, 0, 2 * esize)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        group.addToGroup(groupFlipTime)
        return group, groupFlipTime, itemText, track

    def drawHemisphere(self):

        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.axes.grid(True, color='gray')
        self.hemisphereMatplotlib.axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        self.hemisphereMatplotlib.axes.tick_params(axis='x', colors='white')
        self.hemisphereMatplotlib.axes.set_xlim(0, 360)
        self.hemisphereMatplotlib.axes.set_ylim(0, 90)
        self.hemisphereMatplotlib.axes.tick_params(axis='y', colors='white', which='both', labelleft='on', labelright='on')
        # horizon
        horizon = copy.copy(self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints)
        if len(horizon) > 0:
            horizon.insert(0, (0, 0))
            horizon.append((360, 0))
            self.hemisphereMatplotlib.axes.fill([i[0] for i in horizon], [i[1] for i in horizon], color='#004000')
            self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#002000', lw=3)
        self.hemisphereMatplotlib.draw()
