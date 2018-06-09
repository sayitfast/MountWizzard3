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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import PyQt5
from baseclasses import widget
from astrometry import transform
import astropy
import copy
import numpy
import matplotlib
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
        self.pointerAzAlt3 = None
        self.pointerDome1 = None
        self.pointerDome2 = None
        self.pointerTrack = None
        self.pointsPlotBig = None
        self.pointsPlotSmall = None
        self.pointsPlotCross = None
        self.starsAlignment = None
        self.starsAnnotate = list()
        self.maskPlotFill = None
        self.maskPlotMarker = None
        self.deltaGuide = None
        self.deltaSlew = None
        self.celestial = None
        self.annotate = list()
        self.offx = 1
        self.offy = 1
        self.ui = hemisphere_window_ui.Ui_HemisphereDialog()
        self.ui.setupUi(self)
        self.initUI()
        # allow sizing of the window
        self.setFixedSize(PyQt5.QtCore.QSize(16777215, 16777215))
        # set the minimum size
        self.setMinimumSize(791, 400)

        # setup the plot styles
        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        # making background looking transparent
        self.hemisphereMatplotlib.fig.patch.set_facecolor('none')
        background = self.hemisphereMatplotlib.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        # using tight layout because of the axis titles and labels
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.95, bottom=0.1, top=0.975)
        #self.hemisphereMatplotlib.fig.set_tight_layout((0.075, 0.075, 0.925, 0.925))

        # for the fast moving parts
        self.hemisphereMatplotlibMoving = widget.IntegrateMatplotlib(self.ui.hemisphereMoving)
        # making background looking transparent
        self.hemisphereMatplotlibMoving.fig.patch.set_facecolor('none')
        background = self.hemisphereMatplotlibMoving.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.hemisphereMatplotlibMoving.axes = self.hemisphereMatplotlibMoving.fig.add_subplot(111)

        # for the stars in background
        self.hemisphereMatplotlibStar = widget.IntegrateMatplotlib(self.ui.hemisphereStar)
        self.ui.hemisphereStar.setVisible(False)
        # making background looking transparent
        self.hemisphereMatplotlibStar.fig.patch.set_facecolor('none')
        background = self.hemisphereMatplotlibStar.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.hemisphereMatplotlibStar.axes = self.hemisphereMatplotlibStar.fig.add_subplot(111)

        # signal connections
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.updateModelPoints)

        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerMountDispatcher.signalMountLimits.connect(self.updateMeridianLimits)
        self.ui.checkShowMeridian.clicked.connect(self.updateMeridianLimits)
        self.app.workerMountDispatcher.signalAlignmentStars.connect(self.updateAlignmentStars)
        self.ui.checkShowAlignmentStars.clicked.connect(self.setShowAlignmentStars)
        self.app.workerMountDispatcher.signalAlignmentStars.connect(self.updateCelestial)
        self.ui.checkShowCelestial.clicked.connect(self.updateCelestial)
        self.app.workerDome.signalDomePointer.connect(self.setDomePointer)
        self.ui.checkEditNone.clicked.connect(self.setOperationModus)
        self.ui.checkEditModelPoints.clicked.connect(self.setOperationModus)
        self.ui.checkEditHorizonMask.clicked.connect(self.setOperationModus)
        self.ui.checkPolarAlignment.clicked.connect(self.setOperationModus)

        self.ui.btn_deletePoints.clicked.connect(lambda: self.app.workerModelingDispatcher.commandDispatcher('DeletePoints'))
        self.app.workerModelingDispatcher.modelingRunner.workerSlewpoint.signalPointImaged.connect(self.plotImagedPoint)

        # from start on invisible
        self.showStatus = False
        self.setVisible(False)

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.hemisphere.setGeometry(10, 130, self.width() - 20, self.height() - 140)
        self.ui.hemisphereStar.setGeometry(10, 130, self.width() - 20, self.height() - 140)
        self.ui.hemisphereMoving.setGeometry(10, 130, self.width() - 20, self.height() - 140)
        # getting position of axis
        axesPos = self.hemisphereMatplotlib.axes.get_position()
        # and using it fo the other plot widgets to be identically same size and position
        self.hemisphereMatplotlibStar.axes.set_position(axesPos)
        self.hemisphereMatplotlibMoving.axes.set_position(axesPos)
        # size the header window as well
        self.ui.hemisphereBackground.setGeometry(0, 0, self.width(), 126)

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
                self.ui.checkEditNone.setChecked(self.app.config['CheckEditNone'])
            if 'CheckEditModelPoints' in self.app.config:
                self.ui.checkEditModelPoints.setChecked(self.app.config['CheckEditModelPoints'])
            if 'CheckEditHorizonMask' in self.app.config:
                self.ui.checkEditHorizonMask.setChecked(self.app.config['CheckEditHorizonMask'])
            if 'CheckShowAlignmentStars' in self.app.config:
                self.ui.checkShowAlignmentStars.setChecked(self.app.config['CheckShowAlignmentStars'])
                self.ui.checkPolarAlignment.setDisabled(not self.app.config['CheckShowAlignmentStars'])
            if 'CheckShowCelestial' in self.app.config:
                self.ui.checkShowCelestial.setChecked(self.app.config['CheckShowCelestial'])
            if 'CheckShowMeridian' in self.app.config:
                self.ui.checkShowMeridian.setChecked(self.app.config['CheckShowMeridian'])
            if 'CheckPolarAlignment' in self.app.config:
                self.ui.checkPolarAlignment.setChecked(self.app.config['CheckPolarAlignment'])
            if 'HemisphereWindowHeight' in self.app.config and 'HemisphereWindowWidth' in self.app.config:
                self.resize(self.app.config['HemisphereWindowWidth'], self.app.config['HemisphereWindowHeight'])

        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['HemisphereWindowPositionX'] = self.pos().x()
        self.app.config['HemisphereWindowPositionY'] = self.pos().y()
        self.app.config['HemisphereWindowShowStatus'] = self.showStatus
        self.app.config['CheckEditNone'] = self.ui.checkEditNone.isChecked()
        self.app.config['CheckEditModelPoints'] = self.ui.checkEditModelPoints.isChecked()
        self.app.config['CheckEditHorizonMask'] = self.ui.checkEditHorizonMask.isChecked()
        self.app.config['CheckShowAlignmentStars'] = self.ui.checkShowAlignmentStars.isChecked()
        self.app.config['CheckShowCelestial'] = self.ui.checkShowCelestial.isChecked()
        self.app.config['CheckShowMeridian'] = self.ui.checkShowMeridian.isChecked()
        self.app.config['CheckPolarAlignment'] = self.ui.checkPolarAlignment.isChecked()
        self.app.config['HemisphereWindowHeight'] = self.height()
        self.app.config['HemisphereWindowWidth'] = self.width()

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
        if self.ui.checkShowAlignmentStars.isChecked():
            self.hemisphereMatplotlibStar.fig.canvas.draw()
        self.mutexDrawCanvas.unlock()
        PyQt5.QtWidgets.QApplication.processEvents()

    def drawCanvasMoving(self):
        if not self.mutexDrawCanvasMoving.tryLock():
            self.logger.warning('Performance issue in drawing')
            return
        self.hemisphereMatplotlibMoving.fig.canvas.draw()
        self.mutexDrawCanvasMoving.unlock()
        PyQt5.QtWidgets.QApplication.processEvents()

    def updateModelPoints(self):
        if self.showStatus:
            self.drawHemisphere()
            self.updateCelestial()
            self.updateAlignmentStars()

    def updateMeridianLimits(self):
        if self.showStatus:
            self.app.sharedMountDataLock.lockForRead()
            if 'MeridianLimitSlew' in self.app.workerMountDispatcher.data:
                slew = copy.copy(self.app.workerMountDispatcher.data['MeridianLimitSlew'])
                guide = copy.copy(self.app.workerMountDispatcher.data['MeridianLimitGuide'])
            else:
                slew = 0
                guide = 0
            self.app.sharedMountDataLock.unlock()
            self.deltaGuide.set_visible(self.ui.checkShowMeridian.isChecked())
            self.deltaSlew.set_visible(self.ui.checkShowMeridian.isChecked())
            self.deltaGuide.set_xy((180 - guide, 0))
            self.deltaSlew.set_xy((180 - slew, 0))
            self.deltaGuide.set_width(2 * guide)
            self.deltaSlew.set_width(2 * slew)
            self.drawCanvas()

    def updateCelestial(self):
        if self.showStatus:
            if self.celestial is not None:
                self.celestial.set_visible(self.ui.checkShowCelestial.isChecked())
                celestial = self.app.workerModelingDispatcher.modelingRunner.modelPoints.celestialEquator
                self.celestial.set_data([i[0] for i in celestial], [i[1] for i in celestial])
                self.drawCanvas()

    def updateAlignmentStars(self):
        if self.showStatus:
            self.ui.hemisphereStar.setVisible(self.ui.checkShowAlignmentStars.isChecked())
            starsTopo = copy.copy(self.app.workerMountDispatcher.data['starsTopo'])
            starsNames = copy.copy(self.app.workerMountDispatcher.data['starsNames'])
            if len(starsNames) > 0:
                self.starsAlignment.set_data([i[0] for i in starsTopo], [i[1] for i in starsTopo])
                for i in range(0, len(starsNames)):
                    self.starsAnnotate[i].set_position((starsTopo[i][0] + self.offx, starsTopo[i][1] + self.offy))
                self.hemisphereMatplotlibStar.fig.canvas.draw()

    def setAzAltPointer(self, az, alt):
        if self.showStatus:
            self.pointerAzAlt1.set_data((az, alt))
            self.pointerAzAlt2.set_data((az, alt))
            self.pointerAzAlt3.set_data((az, alt))
            self.pointerAzAlt1.set_visible(True)
            self.pointerAzAlt2.set_visible(True)
            self.pointerAzAlt3.set_visible(True)
            self.drawCanvasMoving()

    def setDomePointer(self, az, stat):
        if self.showStatus:
            self.pointerDome1.set_visible(stat)
            self.pointerDome2.set_visible(stat)
            self.pointerDome1.set_xy((az - 15, 1))
            self.pointerDome2.set_xy((az - 15, 1))
            self.drawCanvasMoving()

    def setShowAlignmentStars(self):
        self.ui.hemisphereStar.setVisible(self.ui.checkShowAlignmentStars.isChecked())
        if self.ui.checkShowAlignmentStars.isChecked():
            self.ui.checkPolarAlignment.setDisabled(False)
        else:
            self.ui.checkPolarAlignment.setDisabled(True)
            if self.ui.checkPolarAlignment.isChecked():
                self.ui.checkPolarAlignment.setChecked(False)
                self.ui.checkEditNone.setChecked(True)
        self.setOperationModus()

    def plotImagedPoint(self, az, alt):
        self.pointsPlotCross.set_data(numpy.append(az, self.pointsPlotCross.get_xdata()), numpy.append(alt, self.pointsPlotCross.get_ydata()))
        self.drawCanvas()

    def setOperationModus(self):
        # reset the settings
        self.maskPlotMarker.set_marker('None')
        self.maskPlotMarker.set_color('#006000')
        self.pointsPlotBig.set_color('#00A000')
        self.starsAlignment.set_color('#C0C000')
        self.starsAlignment.set_markersize(6)
        for i in range(0, len(self.starsAnnotate)):
            self.starsAnnotate[i].set_color('#808080')
        self.ui.hemisphere.stackUnder(self.ui.hemisphereMoving)
        if self.ui.checkEditNone.isChecked():
            pass
        elif self.ui.checkEditModelPoints.isChecked():
            self.pointsPlotBig.set_color('#FF00FF')
            self.ui.hemisphereMoving.stackUnder(self.ui.hemisphere)
        elif self.ui.checkEditHorizonMask.isChecked():
            self.maskPlotMarker.set_marker('o')
            self.maskPlotMarker.set_color('#FF00FF')
            self.ui.hemisphereMoving.stackUnder(self.ui.hemisphere)
        elif self.ui.checkPolarAlignment.isChecked():
            self.starsAlignment.set_color('#FFFF00')
            self.starsAlignment.set_markersize(12)
            for i in range(0, len(self.starsAnnotate)):
                self.starsAnnotate[i].set_color('#F0F0F0')
            self.ui.hemisphere.stackUnder(self.ui.hemisphereMoving)
        else:
            pass
        self.drawCanvas()

    def onMouse(self, event):
        if event.inaxes is None:
            return
        ind = None
        indlow = None
        self.app.sharedMountDataLock.lockForRead()
        stars = self.app.workerMountDispatcher.data['starsTopo']
        self.app.sharedMountDataLock.unlock()
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        horizon = self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints
        if self.ui.checkEditNone.isChecked():
            # double click makes slew to target
            if event.button == 1 and event.dblclick:
                azimuth = int(event.xdata)
                altitude = int(event.ydata)
                question = 'Do you want to slew the mount to:\n\nAzimuth:\t{0}°\nAltitude:\t{1}°'.format(azimuth, altitude)
                value = self.dialogMessage(self, 'Hemisphere direct slew', question)
                if value == PyQt5.QtWidgets.QMessageBox.Ok:
                    # get tracking status of mount:
                    self.app.sharedMountDataLock.lockForRead()
                    isTracking = (self.app.workerMountDispatcher.data['Status'] == '0')
                    self.app.sharedMountDataLock.unlock()
                    # sending the commands for slewing
                    self.app.mountCommandQueue.put(':PO#')
                    self.app.mountCommandQueue.put(':Sz{0:03d}*00#'.format(azimuth))
                    self.app.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(altitude))
                    self.app.mountCommandQueue.put(':MA#')
                    # and start tracking again, if mount was in tracking mode, because :MA# command stops tracking
                    if isTracking:
                        self.app.mountCommandQueue.put(':AP#')

        if self.ui.checkPolarAlignment.isChecked():
            if event.button == 1 and event.dblclick:
                print('got event')
                ind = self.get_ind_under_point(event, 2, stars)
                if ind:
                    self.app.sharedMountDataLock.lockForRead()
                    name = self.app.workerMountDispatcher.data['starsNames'][ind]
                    # RA in degrees ICRS
                    RaJ2000 = self.transform.degStringToDecimal(self.app.workerMountDispatcher.data['starsICRS'][ind][0], ' ')
                    DecJ2000 = self.transform.degStringToDecimal(self.app.workerMountDispatcher.data['starsICRS'][ind][1], ' ')
                    # correct for proper motion
                    jd_2000 = 2451544.5
                    jd_delta = float(self.app.workerMountDispatcher.data['JulianDate']) - jd_2000
                    jd_year_delta = jd_delta / 365.25
                    RaJ2000 += jd_year_delta * self.app.workerMountDispatcher.data['starsICRS'][ind][2] / 3600000
                    DecJ2000 += jd_year_delta * self.app.workerMountDispatcher.data['starsICRS'][ind][3] / 3600000
                    question = 'Do you want to slew to\npolar align star:\n\n{0}'.format(name)
                    value = self.dialogMessage(self, 'Polar Align Routine', question)
                    self.app.sharedMountDataLock.unlock()
                    if value == PyQt5.QtWidgets.QMessageBox.Ok:
                        # transform to JNOW, RAJ2000 comes in degrees, need to be hours
                        RaJNow, DecJNow = self.transform.transformERFA(RaJ2000, DecJ2000, 3)
                        RA = self.transform.decimalToDegreeMountSr(RaJNow)
                        DEC = self.transform.decimalToDegreeMountSd(DecJNow)
                        self.app.mountCommandQueue.put(':PO#')
                        self.app.mountCommandQueue.put(RA)
                        self.app.mountCommandQueue.put(DEC)
                        self.app.mountCommandQueue.put(':MS#')
                    # todo: open automatically the image window and start continuously taking pictures

        # first do the model points
        if self.ui.checkEditModelPoints.isChecked():
            ind = self.get_ind_under_point(event, 2, points)
        if self.ui.checkEditHorizonMask.isChecked():
            ind = self.get_ind_under_point(event, 2, horizon)
            indlow = self.get_two_ind_under_point_in_x(event, horizon)
        if event.button == 3 and ind is not None and self.ui.checkEditModelPoints.isChecked():
            if len(points) > 0:
                del(points[ind])
                self.annotate[ind].remove()
                del(self.annotate[ind])
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if event.button == 1 and ind is None and self.ui.checkEditModelPoints.isChecked():
            points.append((event.xdata, event.ydata))
            if self.app.ui.checkSortPoints.isChecked():
                self.app.workerModelingDispatcher.modelingRunner.modelPoints.sortPoints()
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('', xy=(event.xdata + self.offx, event.ydata + self.offy), color='#E0E0E0'))
            self.pointsPlotBig.set_data([i[0] for i in points], [i[1] for i in points])
            self.pointsPlotSmall.set_data([i[0] for i in points], [i[1] for i in points])
        if self.ui.checkEditModelPoints.isChecked():
            for i in range(0, len(points)):
                self.annotate[i].set_text('{0:2d}'.format(i + 1))
            self.app.messageQueue.put('ToModel>{0:02d}'.format(len(points)))

        # now do the horizon mask
        if event.button == 3 and ind is not None and self.ui.checkEditHorizonMask.isChecked():
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
        if event.button == 1 and ind is None and self.ui.checkEditHorizonMask.isChecked():
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
        self.starsAnnotate = list()
        # star plane
        self.hemisphereMatplotlibStar.axes.cla()
        self.hemisphereMatplotlibStar.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.hemisphereMatplotlibStar.axes.set_facecolor((0, 0, 0, 0))
        self.hemisphereMatplotlibStar.axes.set_xlim(0, 360)
        self.hemisphereMatplotlibStar.axes.set_ylim(0, 90)
        self.hemisphereMatplotlibStar.axes.set_axis_off()
        starsTopo = self.app.workerMountDispatcher.data['starsTopo']
        starsNames = self.app.workerMountDispatcher.data['starsNames']
        self.starsAlignment,  = self.hemisphereMatplotlibStar.axes.plot([i[0] for i in starsTopo], [i[1] for i in starsTopo], '*', markersize=6, color='#C0C000')
        for i in range(0, len(starsTopo)):
            self.starsAnnotate.append(self.hemisphereMatplotlibStar.axes.annotate(starsNames[i],
                                                                                  xy=(starsTopo[i][0] + self.offx,
                                                                                      starsTopo[i][1] + self.offy),
                                                                                  xycoords=('data', 'data'),
                                                                                  color='#808080', fontsize=12, clip_on=True))

        # moving widget plane
        self.hemisphereMatplotlibMoving.axes.cla()
        self.hemisphereMatplotlibMoving.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.hemisphereMatplotlibMoving.axes.set_facecolor((0, 0, 0, 0))
        self.hemisphereMatplotlibMoving.axes.set_xlim(0, 360)
        self.hemisphereMatplotlibMoving.axes.set_ylim(0, 90)
        self.hemisphereMatplotlibMoving.axes.set_axis_off()

        # fixed points and horizon plane
        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.fig.canvas.mpl_connect('button_press_event', self.onMouse)
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
        self.maskPlotMarker,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        if self.ui.checkEditHorizonMask.isChecked():
            self.maskPlotMarker.set_marker('o')
            self.maskPlotMarker.set_color('#FF00FF')
        # model points
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        # draw points in two colors
        self.pointsPlotBig,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=9, fillstyle='none', color='#00A000')
        self.pointsPlotSmall,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=3, color='#E0E000', picker='None')
        if self.ui.checkEditModelPoints.isChecked():
            self.pointsPlotBig.set_color('#FF00FF')
        # add text to points
        for i in range(0, len(points)):
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(i+1), xy=(points[i][0] + self.offx, points[i][1] + self.offy), color='#E0E0E0'))
        # add crosses, if modeling was done to recap when opening the window
        self.pointsPlotCross, = self.hemisphereMatplotlib.axes.plot([], [], 'x', color='#FF0000', zorder=5, markersize=9, lw=2)
        # draw celestial equator
        celestial = self.app.workerModelingDispatcher.modelingRunner.modelPoints.celestialEquator
        self.celestial,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in celestial], [i[1] for i in celestial], '.', markersize=1, fillstyle='none', color='#808080', visible=False)
        # draw meridian limits
        self.deltaGuide = matplotlib.patches.Rectangle((180, 0), 1, 90, zorder=-10, color='#FFFF0040', lw=1, fill=True, visible=False)
        self.deltaSlew = matplotlib.patches.Rectangle((180, 0), 1, 90, zorder=-10, color='#FF000040', lw=1, fill=True, visible=False)
        self.hemisphereMatplotlib.axes.add_patch(self.deltaGuide)
        self.hemisphereMatplotlib.axes.add_patch(self.deltaSlew)

        # now to the third widget on top of the other ones
        # adding the pointer of mount to hemisphereMoving plot
        self.pointerAzAlt1,  = self.hemisphereMatplotlibMoving.axes.plot(180, 45, zorder=10, color='#FF00FF', marker='o', markersize=25, markeredgewidth=3, fillstyle='none', visible=False)
        self.pointerAzAlt2,  = self.hemisphereMatplotlibMoving.axes.plot(180, 45, zorder=10, color='#FF00FF', marker='o', markersize=10, markeredgewidth=1, fillstyle='none', visible=False)
        self.pointerAzAlt3,  = self.hemisphereMatplotlibMoving.axes.plot(180, 45, zorder=10, color='#FF00FF', marker='.', markersize=2, markeredgewidth=1, fillstyle='none', visible=False)
        # adding pointer of dome if dome is present
        self.pointerDome1 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#40404080', lw=3, fill=True, visible=False)
        self.pointerDome2 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#80808080', lw=3, fill=False, visible=False)
        self.hemisphereMatplotlibMoving.axes.add_patch(self.pointerDome1)
        self.hemisphereMatplotlibMoving.axes.add_patch(self.pointerDome2)

        # drawing the whole stuff
        self.setOperationModus()
        self.resizeEvent(0)
