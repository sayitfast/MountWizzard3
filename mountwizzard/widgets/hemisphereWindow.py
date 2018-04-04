############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import copy
import logging
import PyQt5
from PyQt5.QtWidgets import *
from baseclasses import widget
from astrometry import transform
import numpy
import matplotlib
import itertools
import bisect
from gui import hemisphere_window_ui


class HemisphereWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(HemisphereWindow, self).__init__()
        self.app = app
        self.transform = transform.Transform(self.app)
        self.mutexDrawCanvas = PyQt5.QtCore.QMutex()
        self.mutexDrawCanvasMoving = PyQt5.QtCore.QMutex()

        self.pointerAzAlt1 = None
        self.pointerAzAlt2 = None
        self.pointerDome1 = None
        self.pointerDome2 = None
        self.pointerTrack = None
        self.pointsPlotBig = None
        self.pointsPlotSmall = None
        self.pointsPlotCross = None
        self.maskPlotFill = None
        self.maskPlotMarker = None
        self.annotate = list()
        self.offx = 0
        self.offy = 0
        self.ui = hemisphere_window_ui.Ui_HemisphereDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()
        # setup the plot styles
        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        # making background looking transparent
        self.hemisphereMatplotlib.fig.patch.set_facecolor('none')
        background = self.hemisphereMatplotlib.fig.canvas.parentWidget()
        background.setStyleSheet("background-color: transparent;")
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)
        # for the fast moving parts
        self.hemisphereMatplotlibMoving = widget.IntegrateMatplotlib(self.ui.hemisphereMoving)
        # making background looking transparent
        self.hemisphereMatplotlibMoving.fig.patch.set_facecolor('none')
        background = self.hemisphereMatplotlibMoving.fig.canvas.parentWidget()
        background.setStyleSheet("background-color: transparent;")
        self.hemisphereMatplotlibMoving.axes = self.hemisphereMatplotlibMoving.fig.add_subplot(111)
        self.hemisphereMatplotlibMoving.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)
        # signal connections
        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.drawHemisphere)
        self.ui.btn_deletePoints.clicked.connect(lambda: self.app.workerModelingDispatcher.commandDispatcher('DeletePoints'))
        self.app.workerDome.signalDomePointer.connect(self.setDomePointer)
        self.ui.btn_editNone.clicked.connect(self.setEditModus)
        self.ui.btn_editModelPoints.clicked.connect(self.setEditModus)
        self.ui.btn_editHorizonMask.clicked.connect(self.setEditModus)
        self.app.workerModelingDispatcher.modelingRunner.workerSlewpoint.signalPointImaged.connect(self.plotImagedPoint)
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

    def drawCanvas(self):
        if not self.mutexDrawCanvas.tryLock():
            self.logger.warning('Performance issue in drawing')
            return
        self.hemisphereMatplotlib.fig.canvas.draw()
        self.mutexDrawCanvas.unlock()
        PyQt5.QtWidgets.QApplication.processEvents()

    def drawCanvasMoving(self):
        if not self.mutexDrawCanvasMoving.tryLock():
            self.logger.warning('Performance issue in drawing')
            return
        self.hemisphereMatplotlibMoving.fig.canvas.draw()
        self.mutexDrawCanvasMoving.unlock()
        PyQt5.QtWidgets.QApplication.processEvents()

    def setAzAltPointer(self, az, alt):
        if self.showStatus:
            self.pointerAzAlt1.set_data((az, alt))
            self.pointerAzAlt2.set_data((az, alt))
            self.pointerAzAlt1.set_visible(True)
            self.pointerAzAlt2.set_visible(True)
            self.drawCanvasMoving()

    def setDomePointer(self, az, stat):
        print('dome widget, status ', stat)
        if self.showStatus:
            self.pointerDome1.set_visible(stat)
            self.pointerDome2.set_visible(stat)
            self.pointerDome1.set_xy((az - 15, 1))
            self.pointerDome2.set_xy((az - 15, 1))
            self.drawCanvasMoving()

    def plotImagedPoint(self, az, alt):
        self.pointsPlotCross.set_data(numpy.append(az, self.pointsPlotCross.get_xdata()), numpy.append(alt, self.pointsPlotCross.get_ydata()))
        self.drawCanvas()

    def setEditModus(self):
        if self.ui.btn_editNone.isChecked():
            self.maskPlotMarker.set_marker('None')
            self.maskPlotMarker.set_color('#006000')
            self.pointsPlotBig.set_color('#00A000')
            self.ui.hemisphere.stackUnder(self.ui.hemisphereMoving)

        elif self.ui.btn_editModelPoints.isChecked():
            self.maskPlotMarker.set_marker('None')
            self.maskPlotMarker.set_color('#006000')
            self.pointsPlotBig.set_color('#FF00FF')
            self.ui.hemisphereMoving.stackUnder(self.ui.hemisphere)

        elif self.ui.btn_editHorizonMask.isChecked():
            self.maskPlotMarker.set_marker('o')
            self.pointsPlotBig.set_color('#00A000')
            self.maskPlotMarker.set_color('#FF00FF')
            self.ui.hemisphereMoving.stackUnder(self.ui.hemisphere)
        else:
            pass
        self.drawCanvas()

    def onMouse(self, event):
        if event.inaxes is None or self.ui.btn_editNone.isChecked():
            return
        ind = None
        indlow = None
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        horizon = self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints

        # first do the model points
        if self.ui.btn_editModelPoints.isChecked():
            ind = self.get_ind_under_point(event, 2, points)
        if self.ui.btn_editHorizonMask.isChecked():
            ind = self.get_ind_under_point(event, 2, horizon)
            indlow = self.get_two_ind_under_point_in_x(event, horizon)
        if event.button == 3 and ind is not None and self.ui.btn_editModelPoints.isChecked():
            if len(points) > 0:
                del(points[ind])
                self.annotate[ind].remove()
                del(self.annotate[ind])
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if event.button == 1 and ind is None and self.ui.btn_editModelPoints.isChecked():
            points.append((event.xdata, event.ydata))
            if self.app.ui.checkSortPoints.isChecked():
                self.app.workerModelingDispatcher.modelingRunner.modelPoints.sortPoints()
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('', xy=(event.xdata - self.offx, event.ydata - self.offy), color='#E0E0E0'))
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if self.ui.btn_editModelPoints.isChecked():
            for i in range(0, len(points)):
                self.annotate[i].set_text('{0:2d}'.format(i + 1))
            self.app.messageQueue.put('ToModel>{0:02d}'.format(len(points)))

        # now do the horizon mask
        if event.button == 3 and ind is not None and self.ui.btn_editHorizonMask.isChecked():
            # delete a point
            if len(horizon) > 2:
                del(horizon[ind])
            # now redraw plot
            self.maskPlotMarker.set_data([i[0] for i in horizon], [i[1] for i in horizon])
            x = [i[0] for i in horizon]
            x.insert(0, 0)
            x.append(360)
            y = [i[1] for i in horizon]
            y.insert(0, 0)
            y.append(0)
            self.maskPlotFill.set_xy(numpy.column_stack((x, y)))
        if event.button == 1 and ind is None and self.ui.btn_editHorizonMask.isChecked():
            if indlow is not None:
                horizon.insert(indlow + 1, (event.xdata, event.ydata))
            self.maskPlotMarker.set_data([i[0] for i in horizon], [i[1] for i in horizon])
            x = [i[0] for i in horizon]
            x.insert(0, 0)
            x.append(360)
            y = [i[1] for i in horizon]
            y.insert(0, 0)
            y.append(0)
            self.maskPlotFill.set_xy(numpy.column_stack((x, y)))

        # finally redraw
        self.drawCanvas()

    @staticmethod
    def get_ind_under_point(event, epsilon, xy):
        if len(xy) == 0:
            return None
        xt = numpy.asarray([i[0] for i in xy])
        yt = numpy.asarray([i[1] for i in xy])
        d = numpy.sqrt((xt - event.xdata)**2 / 16 + (yt - event.ydata)**2)
        ind = d.argsort()[:1][0]
        if d[ind] >= epsilon:
            ind = None
        return ind

    @staticmethod
    def get_two_ind_under_point_in_x(event, xy):
        if len(xy) < 2:
            return None
        xt = [i[0] for i in xy]
        return bisect.bisect_left(xt, event.xdata) - 1

    def drawHemisphere(self):
        for i in range(0, len(self.annotate)):
            self.annotate[i].remove()
        self.annotate = list()
        self.hemisphereMatplotlibMoving.axes.cla()
        # set face color transparent
        self.hemisphereMatplotlibMoving.axes.set_facecolor((0, 0, 0, 0))
        self.hemisphereMatplotlibMoving.axes.set_xlim(0, 360)
        self.hemisphereMatplotlibMoving.axes.set_ylim(0, 90)
        self.hemisphereMatplotlibMoving.axes.set_axis_off()

        self.hemisphereMatplotlib.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.axes.spines['bottom'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['top'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['left'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['right'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.grid(True, color='#404040')
        self.hemisphereMatplotlib.axes.set_facecolor((0, 0, 0, 0))
        self.hemisphereMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.hemisphereMatplotlib.axes.set_xlim(0, 360)
        self.hemisphereMatplotlib.axes.set_xticks(numpy.arange(0, 361, 30))
        self.hemisphereMatplotlib.axes.set_ylim(0, 90)
        self.hemisphereMatplotlib.axes.tick_params(axis='y', colors='#2090C0', which='both', labelleft='on', labelright='on', labelsize=12)
        self.hemisphereMatplotlib.axes.set_xlabel('Azimuth in degrees', color='#2090C0', fontweight='bold', fontsize=12)
        self.hemisphereMatplotlib.axes.set_ylabel('Altitude in degrees', color='#2090C0', fontweight='bold', fontsize=12)
        # horizon
        horizon = self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints
        if len(horizon) < 2:
            del(horizon[:])
            horizon.append((0, 0))
            horizon.append((360, 0))
        x = [i[0] for i in horizon]
        x.insert(0, 0)
        x.append(360)
        y = [i[1] for i in horizon]
        y.insert(0, 0)
        y.append(0)
        self.maskPlotFill,  = self.hemisphereMatplotlib.axes.fill(x, y, color='#002000', zorder=-20)
        self.maskPlotMarker,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3, picker='None')
        if self.ui.btn_editHorizonMask.isChecked():
            self.maskPlotMarker.set_marker('o')
            self.maskPlotMarker.set_color('#FF00FF')
        # model points
        self.offx = -2
        self.offy = 2
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        # draw points in two colors
        self.pointsPlotBig,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=9, color='#00A000', picker='None')
        self.pointsPlotSmall,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=3, color='#E0E000', picker='None')
        if self.ui.btn_editModelPoints.isChecked():
            self.pointsPlotBig.set_color('#FF00FF')
        # add text to points
        for i in range(0, len(points)):
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(i+1), xy=(points[i][0] - self.offx, points[i][1] - self.offy), color='#E0E0E0', picker='None'))
        # add crosses, if modeling was done to recap when opening the window
        self.pointsPlotCross, = self.hemisphereMatplotlib.axes.plot([], [], 'X', color='#FF00FF', zorder=5, markersize=9)
        # now to the second widget on top of the first one
        # adding the pointer of mount to hemisphereMoving plot
        self.pointerAzAlt1,  = self.hemisphereMatplotlibMoving.axes.plot(180, 45, zorder=10, color='#FF00FF', marker='o', markersize=25, markeredgewidth=3, fillstyle='none', visible=False, picker='None')
        self.pointerAzAlt2,  = self.hemisphereMatplotlibMoving.axes.plot(180, 45, zorder=10, color='#FF00FF', marker='o', markersize=10, markeredgewidth=1, fillstyle='none', visible=False, picker='None')
        # adding pointer of dome if dome is present
        self.pointerDome1 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#40404080', lw=3, fill=True, visible=False, picker='None')
        self.pointerDome2 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#80808080', lw=3, fill=False, visible=False, picker='None')
        self.hemisphereMatplotlibMoving.axes.add_patch(self.pointerDome1)
        self.hemisphereMatplotlibMoving.axes.add_patch(self.pointerDome2)
        self.drawCanvas()
        self.drawCanvasMoving()
