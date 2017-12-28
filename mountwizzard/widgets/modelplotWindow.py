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
        self.pointerAzAlt1 = None
        self.pointerAzAlt2 = None
        self.pointerDome1 = None
        self.pointerDome2 = None
        self.pointerTrack = None
        self.pointerTrackLine = []
        self.itemFlipTime = QGraphicsItemGroup()
        self.itemFlipTimeText = QGraphicsTextItem('')
        self.ui = coordinate_dialog_ui.Ui_CoordinateDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()
        # setup the plot styles
        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)
        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerMountDispatcher.signalMountTrackPreview.connect(self.drawTrackPreview)
        self.ui.checkRunTrackingWidget.toggled.connect(self.changeStatusTrackingWidget)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.drawHemisphere)
        self.ui.btn_deletePoints.clicked.connect(lambda: self.app.workerModelingDispatcher.commandDispatcher('DeletePoints'))
        self.ui.checkShowNumbers.stateChanged.connect(self.drawHemisphere)

        if platform.system() == 'Windows':
            self.app.workerAscomDome.signalDomePointer.connect(self.setDomePointer)
        self.showStatus = False
        self.setVisible(False)

    def initConfig(self):
        try:
            if 'CoordinatePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['CoordinatePopupWindowPositionX'], self.app.config['CoordinatePopupWindowPositionY'])
            if 'CoordinatePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['CoordinatePopupWindowShowStatus']
            if 'CheckShowNumbers' in self.app.config:
                self.ui.checkShowNumbers.setChecked(self.app.config['CheckShowNumbers'])
            if 'CheckRunTrackingWidget' in self.app.config:
                self.ui.checkRunTrackingWidget.setChecked(self.app.config['CheckRunTrackingWidget'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['CoordinatePopupWindowPositionX'] = self.pos().x()
        self.app.config['CoordinatePopupWindowPositionY'] = self.pos().y()
        self.app.config['CoordinatePopupWindowShowStatus'] = self.showStatus
        self.app.config['CheckShowNumbers'] = self.ui.checkShowNumbers.isChecked()
        self.app.config['CheckRunTrackingWidget'] = self.ui.checkRunTrackingWidget.isChecked()

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.drawHemisphere()
        self.show()

    def selectHorizonPointsMode(self):
        msg = self.app.workerModelingDispatcher.modelingRunner.modelPoints.loadHorizonPoints(self.app.ui.le_horizonPointsFileName.text(),
                                                                                             self.app.ui.checkUseFileHorizonLine.isChecked(),
                                                                                             self.app.ui.checkUseMinimumHorizonLine.isChecked(),
                                                                                             self.app.ui.altitudeMinimumHorizon.value())
        if msg:
            self.app.messageQueue.put(msg + '\n')
        self.drawHemisphere()

    def setAzAltPointer(self, az, alt):
        self.pointerAzAlt1.set_xy((az, alt))
        self.pointerAzAlt2.set_xy((az, alt))
        self.hemisphereMatplotlib.fig.canvas.draw()
        QApplication.processEvents()

    def setDomePointer(self, az):
        self.pointerDome1.set_xy((az, 1))
        self.pointerDome2.set_xy((az, 1))
        self.hemisphereMatplotlib.fig.canvas.draw()
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

    def drawHemisphere(self):
        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.axes.grid(True, color='gray')
        self.hemisphereMatplotlib.axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        self.hemisphereMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.hemisphereMatplotlib.axes.set_xlim(0, 360)
        self.hemisphereMatplotlib.axes.set_ylim(0, 90)
        self.hemisphereMatplotlib.axes.tick_params(axis='y', colors='#2090C0', which='both', labelleft='on', labelright='on', labelsize=12)
        # get the aspect ratio for circles etc:
        figW, figH = self.hemisphereMatplotlib.axes.get_figure().get_size_inches()
        _, _, w, h = self.hemisphereMatplotlib.axes.get_position().bounds
        displayRatio = (figH * h) / (figW * w)
        dataRatio = 90 / 360
        aspectRatio = displayRatio / dataRatio
        # horizon
        horizon = copy.copy(self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints)
        if len(horizon) > 0:
            horizon.insert(0, (0, 0))
            horizon.append((360, 0))
            self.hemisphereMatplotlib.axes.fill([i[0] for i in horizon], [i[1] for i in horizon], color='#002000', zorder=-20)
            self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        # model points
        number = 1
        offx = 7
        offy = offx / aspectRatio
        base = self.app.workerModelingDispatcher.modelingRunner.modelPoints.BasePoints
        if len(base) > 0:
            self.hemisphereMatplotlib.axes.plot([i[0] for i in base], [i[1] for i in base], 'o', markersize=10, color='#FF0000')
            self.hemisphereMatplotlib.axes.plot([i[0] for i in base], [i[1] for i in base], 'o', markersize=4, color='#FFFF00')
            if self.ui.checkShowNumbers.isChecked():
                for i in range(0, len(base)):
                    self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(number), xy=(base[i][0] - offx, base[i][1] - offy), color='#E0E0E0')
                    number += 1
        refine = self.app.workerModelingDispatcher.modelingRunner.modelPoints.RefinementPoints
        if len(refine) > 0:
            # draw points in two colors
            self.hemisphereMatplotlib.axes.plot([i[0] for i in refine], [i[1] for i in refine], 'o', markersize=10, color='#00FF00')
            self.hemisphereMatplotlib.axes.plot([i[0] for i in refine], [i[1] for i in refine], 'o', markersize=4, color='#FFFF00')
            # add text to points
            if self.ui.checkShowNumbers.isChecked():
                for i in range(0, len(refine)):
                    self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(number), xy=(refine[i][0] - offx, refine[i][1] - offy), color='#E0E0E0')
                    number += 1
        # adding the pointer of mount
        self.pointerAzAlt1 = matplotlib.patches.Ellipse((180, 45), 4 * aspectRatio, 4, zorder=-2, color='#FF00FF', lw=2, fill=False)
        self.pointerAzAlt2 = matplotlib.patches.Ellipse((180, 45), 1.5 * aspectRatio, 1.5, zorder=-2, color='#FF00FF', lw=1, fill=False)
        # adding pointer of dome
        self.pointerDome1 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#404040', lw=3, fill=True)
        self.pointerDome2 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#808080', lw=3, fill=False)
        # finishing up
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt2)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome2)
        self.hemisphereMatplotlib.draw()
