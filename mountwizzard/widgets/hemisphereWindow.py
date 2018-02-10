############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import copy
import logging
from PyQt5.QtWidgets import *
from baseclasses import widget
from astrometry import transform
import numpy
import matplotlib
from gui import hemisphere_dialog_ui


class HemisphereWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(HemisphereWindow, self).__init__()
        self.app = app
        self.transform = transform.Transform(self.app)
        self.pointerAzAlt1 = None
        self.pointerAzAlt2 = None
        self.pointerDome1 = None
        self.pointerDome2 = None
        self.pointerTrack = None
        self.pointsPlotBig = None
        self.pointsPlotSmall = None
        self.maskPlotFill = None
        self.maskPlotMarker = None
        self.annotate = list()
        self.offx = 0
        self.offy = 0
        self.ui = hemisphere_dialog_ui.Ui_HemisphereDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()
        # setup the plot styles
        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)
        # signal connections
        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.drawHemisphere)
        self.ui.btn_deletePoints.clicked.connect(lambda: self.app.workerModelingDispatcher.commandDispatcher('DeletePoints'))
        # self.ui.checkShowNumbers.stateChanged.connect(self.drawHemisphere)
        self.app.workerDome.signalDomePointer.connect(self.setDomePointer)
        self.app.workerDome.signalDomePointerVisibility.connect(self.setDomePointerVisibility)

        self.ui.btn_editNone.clicked.connect(self.setEditModus)
        self.ui.btn_editModelPoints.clicked.connect(self.setEditModus)
        self.ui.btn_editHorizonMask.clicked.connect(self.setEditModus)
        # from start on invisible
        self.showStatus = False
        self.setVisible(False)

    def initConfig(self):
        try:
            if 'HemisphereWindowPositionX' in self.app.config:
                x = self.app.config['HemisphereWindowPositionX']
                y = self.app.config['HemisphereWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'HemisphereWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['HemisphereWindowShowStatus']
            if 'CheckEditNone' in self.app.config:
                self.ui.btn_editNone.setChecked(self.app.config['CheckEditNone'])
            if 'CheckEditModelPoints' in self.app.config:
                self.ui.btn_editModelPoints.setChecked(self.app.config['CheckEditModelPoints'])
            if 'CheckEditHorizonMask' in self.app.config:
                self.ui.btn_editHorizonMask.setChecked(self.app.config['CheckEditHorizonMask'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['HemisphereWindowPositionX'] = self.pos().x()
        self.app.config['HemisphereWindowPositionY'] = self.pos().y()
        self.app.config['HemisphereWindowShowStatus'] = self.showStatus
        self.app.config['CheckEditNone'] = self.ui.btn_editNone.isChecked()
        self.app.config['CheckEditModelPoints'] = self.ui.btn_editModelPoints.isChecked()
        self.app.config['CheckEditHorizonMask'] = self.ui.btn_editHorizonMask.isChecked()

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
        az += 0.5
        alt -= 0.125
        if self.showStatus:
            self.pointerAzAlt1.center = az, alt
            self.pointerAzAlt2.center = az, alt
            self.pointerAzAlt1.set_visible(True)
            self.pointerAzAlt2.set_visible(True)
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def setDomePointerVisibility(self, stat):
        if self.showStatus:
            self.pointerDome1.set_visible(stat)
            self.pointerDome2.set_visible(stat)
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def setDomePointer(self, az):
        if self.showStatus:
            self.pointerDome1.set_xy((az - 15, 1))
            self.pointerDome2.set_xy((az - 15, 1))
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def setEditModus(self):
        if self.ui.btn_editNone.isChecked():
            self.maskPlotMarker.set_marker('None')
        elif self.ui.btn_editModelPoints.isChecked():
            self.maskPlotMarker.set_marker('None')
        elif self.ui.btn_editHorizonMask.isChecked():
            self.maskPlotMarker.set_marker('o')
        else:
            pass
        self.hemisphereMatplotlib.fig.canvas.draw()

    def onMouse(self, event):
        if event.inaxes is None or self.ui.btn_editNone.isChecked():
            return
        ind = self.get_ind_under_point(event, 2)
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        horizon = self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints

        # first do the model points
        if event.button == 3 and ind is not None and self.ui.btn_editModelPoints.isChecked():
            # delete a point
            if len(points) > 0:
                # print(ind, len(self.annotate), len(points))
                del(points[ind])
                self.annotate[ind].remove()
                del(self.annotate[ind])
            # now redraw plot
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if event.button == 1 and ind is None and self.ui.btn_editModelPoints.isChecked():
            # add a point
            points.append((event.xdata, event.ydata))
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(len(points)), xy=(event.xdata - self.offx, event.ydata - self.offy), color='#E0E0E0'))
            # now redraw plot
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if self.ui.btn_editModelPoints.isChecked():
            for i in range(0, len(points)):
                self.annotate[i].set_text('{0:2d}'.format(i + 1))
            self.app.messageQueue.put('ToModel>{0:02d}'.format(len(points)))

        # now do the horizon mask
        # self.ui.btn_editHorizonMask.isChecked()

        # finally redraw
        self.hemisphereMatplotlib.fig.canvas.draw()

    def get_ind_under_point(self, event, epsilon):
        xy = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        if len(xy) == 0:
            return None
        xt = numpy.asarray([i[0] for i in xy])
        yt = numpy.asarray([i[1] for i in xy])
        d = numpy.sqrt((xt - event.xdata)**2 / 16 + (yt - event.ydata)**2)
        indseq = numpy.nonzero(numpy.equal(d, numpy.amin(d)))[0]
        ind = indseq[0]
        if d[ind] >= epsilon:
            ind = None
        return ind

    def drawHemisphere(self):
        for i in range(0, len(self.annotate)):
            self.annotate[i].remove()
        self.annotate = list()
        self.hemisphereMatplotlib.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.axes.spines['bottom'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['top'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['left'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['right'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.grid(True, color='#404040')
        self.hemisphereMatplotlib.axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        self.hemisphereMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.hemisphereMatplotlib.axes.set_xlim(0, 360)
        self.hemisphereMatplotlib.axes.set_xticks(numpy.arange(0, 361, 30))
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
        horizon.insert(0, (0, 0))
        horizon.append((360, 0))
        self.maskPlotFill,  = self.hemisphereMatplotlib.axes.fill([i[0] for i in horizon], [i[1] for i in horizon], color='#002000', zorder=-20)
        # self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        self.maskPlotMarker,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        # model points
        self.offx = -2
        self.offy = 7 / aspectRatio
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        # draw points in two colors
        self.pointsPlotBig,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=9, color='#00A000')
        self.pointsPlotSmall,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=3, color='#E0E000')
        # add text to points
        for i in range(0, len(points)):
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(i+1), xy=(points[i][0] - self.offx, points[i][1] - self.offy), color='#E0E0E0'))
        # adding the pointer of mount
        self.pointerAzAlt1 = matplotlib.patches.Ellipse((180, 45), 4 * aspectRatio, 4, zorder=10, color='#FF00FF', lw=2, fill=False, visible=False)
        self.pointerAzAlt2 = matplotlib.patches.Ellipse((180, 45), 1.5 * aspectRatio, 1.5, zorder=10, color='#FF00FF', lw=1, fill=False, visible=False)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt2)
        # adding pointer of dome if dome is present
        self.pointerDome1 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#404040', lw=3, fill=True, visible=False)
        self.pointerDome2 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#808080', lw=3, fill=False, visible=False)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome2)
        self.hemisphereMatplotlib.draw()
