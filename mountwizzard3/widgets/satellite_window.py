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
import logging
import os
import time
import numpy
import copy
import PyQt5
# import pyorbital
import astropy.io.fits as pyfits
from astropy.visualization import MinMaxInterval, ImageNormalize, AsymmetricPercentileInterval, PowerStretch
from matplotlib import use
from base import widget
from astrometry import transform
from gui import satellite_window_ui
use('Qt5Agg')


class WorkerSignals(PyQt5.QtCore.QObject):

    finished = PyQt5.QtCore.pyqtSignal()
    error = PyQt5.QtCore.pyqtSignal(object)
    result = PyQt5.QtCore.pyqtSignal(object)


class Worker(PyQt5.QtCore.QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(e)
            print(e)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class SatelliteWindow(widget.MwWidget):

    logger = logging.getLogger(__name__)

    signalRedrawAll = PyQt5.QtCore.pyqtSignal()

    satelliteData = {
        'Line0': list(),
        'Line1': list(),
        'Line2': list()
    }

    def __init__(self, app):
        super(SatelliteWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.cancel = False
        self.maskPlotFill = None
        self.maskPlotMarker = None
        self.mutexDrawCanvas = PyQt5.QtCore.QMutex()
        self.mutexDrawCanvasMoving = PyQt5.QtCore.QMutex()
        self.transform = transform.Transform(self.app)
        self.ui = satellite_window_ui.Ui_SatelliteDialog()
        self.ui.setupUi(self)
        self.initUI()
        # allow sizing of the window
        self.setFixedSize(PyQt5.QtCore.QSize(16777215, 16777215))
        # set the minimum size
        self.setMinimumSize(791, 400)
        self.threadpool = PyQt5.QtCore.QThreadPool()

        # setup the plot styles
        self.satelliteMatplotlib = widget.IntegrateMatplotlib(self.ui.satellite)
        # making background looking transparent
        self.satelliteMatplotlib.fig.patch.set_facecolor('none')
        background = self.satelliteMatplotlib.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.satelliteMatplotlib.axes = self.satelliteMatplotlib.fig.add_subplot(111)
        # using tight layout because of the axis titles and labels
        self.satelliteMatplotlib.fig.subplots_adjust(left=0.075, right=0.95, bottom=0.1, top=0.975)

        # for the fast moving parts
        self.satelliteMatplotlibMoving = widget.IntegrateMatplotlib(self.ui.satelliteMoving)
        # making background looking transparent
        self.satelliteMatplotlibMoving.fig.patch.set_facecolor('none')
        background = self.satelliteMatplotlibMoving.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.satelliteMatplotlibMoving.axes = self.satelliteMatplotlibMoving.fig.add_subplot(111)

        # slot gui elements
        self.app.ui.btn_loadSatelliteData.clicked.connect(self.selectSatellitesDataFileName)
        self.app.ui.btn_selectSatellite.clicked.connect(self.getListAction)
        self.app.ui.listSatelliteName.itemDoubleClicked.connect(self.getListAction)
        self.app.ui.btn_clearSatellite.clicked.connect(self.clearListAction)

        # slots for functions
        self.signalRedrawAll.connect(self.drawCanvas)

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.satellite.setGeometry(10, 130, self.width() - 20, self.height() - 140)
        self.ui.satelliteMoving.setGeometry(10, 130, self.width() - 20, self.height() - 140)
        # getting position of axis
        axesPos = self.satelliteMatplotlib.axes.get_position()
        # and using it fo the other plot widgets to be identically same size and position
        self.satelliteMatplotlibMoving.axes.set_position(axesPos)
        # size the header window as well
        self.ui.satelliteBackground.setGeometry(0, 0, self.width(), 126)

    def initConfig(self):
        try:
            if 'SatellitePopupWindowPositionX' in self.app.config:
                x = self.app.config['SatellitePopupWindowPositionX']
                y = self.app.config['SatellitePopupWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'SatellitePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['SatellitePopupWindowShowStatus']
            if 'SatelliteWindowHeight' in self.app.config and 'SatelliteWindowWidth' in self.app.config:
                self.resize(self.app.config['SatelliteWindowWidth'], self.app.config['SatelliteWindowHeight'])
            if 'SatelliteDataFileName' in self.app.config:
                self.app.ui.le_satelliteDataFileName.setText(self.app.config['SatelliteDataFileName'])
                if self.app.config['SatelliteDataFileName'] != '':
                    self.loadSatelliteData(os.getcwd() + '/config/' + self.app.config['SatelliteDataFileName'] + '.tle')
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for satellite window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['SatellitePopupWindowPositionX'] = self.pos().x()
        self.app.config['SatellitePopupWindowPositionY'] = self.pos().y()
        self.app.config['SatellitePopupWindowShowStatus'] = self.showStatus
        self.app.config['SatelliteWindowHeight'] = self.height()
        self.app.config['SatelliteWindowWidth'] = self.width()
        self.app.config['SatelliteDataFileName'] = self.app.ui.le_satelliteDataFileName.text()

    def toggleWindow(self):
        self.showStatus = not self.showStatus
        if self.showStatus:
            self.showWindow()
        else:
            self.close()

    def showWindow(self):
        self.showStatus = True
        self.app.signalChangeStylesheet.emit(self.app.ui.btn_openSatelliteWindow, 'running', 'true')
        self.setVisible(True)
        self.drawSatellite()

    def closeEvent(self, closeEvent):
        super().closeEvent(closeEvent)
        self.app.signalChangeStylesheet.emit(self.app.ui.btn_openSatelliteWindow, 'running', 'false')

    def selectSatellitesDataFileName(self):
        value, ext = self.app.selectFile(self.app, 'Open satellite data file', '/config', 'TLE File (*.tle)', True)
        if value != '':
            self.app.ui.le_satelliteDataFileName.setText(os.path.basename(value))
            # next is to load and populate the data dictionary
            self.loadSatelliteData(value + ext)

    def loadSatelliteData(self, filename):
        if not os.path.isfile(filename):
            self.logger.error('Data file {0} is not existent'.format(filename))
        try:
            with open(filename, 'r') as infile:
                lines = infile.read().splitlines()
        except Exception as e:
            self.logger.error('Error loading satellite data: {0}'.format(e))
        finally:
            pass
        # if we don't have a full set of data (3 lines each, we have a problem
        if (len(lines) % 3) != 0:
            self.logger.error('Problem in data file - could not load data')
            return
        else:
            self.logger.info('Data from file : {0} loaded'.format(filename))
        # as we have now loaded a set of data, we could parse it.
        # first delete the data
        self.satelliteData = {
            'Line0': list(),
            'Line1': list(),
            'Line2': list()
        }
        # then make three lists for each line of TLE data
        # Line0 holds the name for the selection list
        # Line1 and Line2 hold the data
        for i in range(0, len(lines), 3):
            self.satelliteData['Line0'].append(lines[i])
            self.satelliteData['Line1'].append(lines[i+1])
            self.satelliteData['Line2'].append(lines[i+2])
        self.setSatelliteNameList()

    def setSatelliteNameList(self):
        self.app.ui.listSatelliteName.clear()
        for name in self.satelliteData['Line0']:
            self.app.ui.listSatelliteName.addItem(name)
        self.app.ui.listSatelliteName.sortItems()
        self.app.ui.listSatelliteName.update()

    def clearData(self):
        self.app.ui.le_satelliteName.setText('')
        self.app.ui.le_satelliteNumber.setText('')
        self.app.ui.le_satelliteLaunchYear.setText('')
        self.app.ui.le_satelliteEpochDay.setText('')
        self.app.ui.le_satelliteEpochYear.setText('')
        self.app.ui.le_satellite1derrMotion.setText('')
        self.app.ui.le_satellite2derrMotion.setText('')
        self.app.ui.le_satelliteBSTAR.setText('')
        self.app.ui.le_satelliteInclination.setText('')
        self.app.ui.le_satelliteRA.setText('')
        self.app.ui.le_satelliteEccentricity.setText('')
        self.app.ui.le_satellitePerigee.setText('')
        self.app.ui.le_satelliteAnomaly.setText('')
        self.app.ui.le_satelliteMotion.setText('')

    def parseData(self, index):
        # parsing of the data is accordingly to https://www.celestrak.com/NORAD/documentation/tle-fmt.php
        # doing that just for information in the gui. The mount computer itself parses the data
        self.app.ui.le_satelliteName.setText(self.satelliteData['Line0'][index].strip())
        self.app.ui.le_satelliteNumber.setText(self.satelliteData['Line1'][index][2:7])
        self.app.ui.le_satelliteLaunchYear.setText(self.satelliteData['Line1'][index][9:11])
        self.app.ui.le_satelliteEpochDay.setText(self.satelliteData['Line1'][index][20:32])
        self.app.ui.le_satelliteEpochYear.setText(self.satelliteData['Line1'][index][18:20])
        self.app.ui.le_satellite1derrMotion.setText(self.satelliteData['Line1'][index][32:43])
        self.app.ui.le_satellite2derrMotion.setText(self.satelliteData['Line1'][index][44:52])
        self.app.ui.le_satelliteBSTAR.setText(self.satelliteData['Line1'][index][53:61])
        self.app.ui.le_satelliteInclination.setText(self.satelliteData['Line2'][index][8:16])
        self.app.ui.le_satelliteRA.setText(self.satelliteData['Line2'][index][17:25])
        self.app.ui.le_satelliteEccentricity.setText(self.satelliteData['Line2'][index][26:33])
        self.app.ui.le_satellitePerigee.setText(self.satelliteData['Line2'][index][34:42])
        self.app.ui.le_satelliteAnomaly.setText(self.satelliteData['Line2'][index][43:51])
        self.app.ui.le_satelliteMotion.setText(self.satelliteData['Line2'][index][52:63])

    def pushDataToMount(self, data, name):
        commandSet = {'command': ':TLEL0{0}#'.format(data), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'][0] == 'V':
            self.app.messageQueue.put('TLE data for {0} loaded\n'.format(name))
            returnValue = True
        else:
            self.app.messageQueue.put('#BRTLE data for {0} could not be loaded\n'.format(name))
            self.logger.warning('TLE data for {0} could not be loaded. Error code: {1}'.format(name, commandSet['reply']))
            returnValue = False
        return returnValue

    def calculateValues(self):
        # if mount not running, we ge not data back
        if not self.app.workerMountDispatcher.mountStatus['Slow']:
            return
        self.app.sharedMountDataLock.lockForRead()
        JD = self.app.workerMountDispatcher.data['JulianDate']
        self.app.sharedMountDataLock.unlock()
        commandSet = {'command': ':TLEGAZ{0}#:TLEP{0},{1}#'.format(JD, 1440), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'][0] == 'E':
            self.app.messageQueue.put('No TLE data loaded for {0}\n'.format(name))
        else:
            altaz = commandSet['reply'][0].split(',')
            self.app.ui.le_satelliteAlt.setText(altaz[0])
            self.app.ui.le_satelliteAz.setText(altaz[1])
        if commandSet['reply'][1] == 'E':
            self.app.messageQueue.put('No TLE data loaded for {0}\n'.format(name))
        else:
            transit = commandSet['reply'][1].split(',')
            passStart = '{0:4.1f}'.format((float(transit[0]) - float(JD)) * 1440)
            passEnd = '{0:4.1f}'.format((float(transit[1]) - float(JD)) * 1440)
            self.app.ui.le_satellitePassStart.setText(passStart)
            self.app.ui.le_satellitePassEnd.setText(passEnd)

    def getListAction(self):
        name = self.app.ui.listSatelliteName.currentItem().text()
        index = self.satelliteData['Line0'].index(name)
        self.parseData(index)

    def clearListAction(self):
        self.clearData()
    '''
        # please think of the escaped characters for mount computer. Hex 0A (CR) goes for $0A
        data = self.satelliteData['Line0'][index] + '$0A' + self.satelliteData['Line1'][index] + '$0A' + self.satelliteData['Line2'][index]
        if self.pushDataToMount(data, name.strip()):
            # now calculation transits etc.
        else:
            return
    '''
    def drawCanvas(self):
        # if window is open, we process the data
        if self.showStatus:
            # make a mutex in case not double execute the routing and detect performance issues
            if not self.mutexDrawCanvas.tryLock():
                self.logger.warning('Performance issue in drawing')
                return
            # i have to redraw the whole story because of the horizon
            self.drawSatellite()
            self.satelliteMatplotlib.fig.canvas.draw()
            self.mutexDrawCanvas.unlock()
            # PyQt5.QtWidgets.QApplication.processEvents()

    def drawSatellite(self):
        # moving widget plane
        self.satelliteMatplotlibMoving.axes.cla()
        # self.hemisphereMatplotlibMoving.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.satelliteMatplotlibMoving.axes.set_facecolor((0, 0, 0, 0))
        self.satelliteMatplotlibMoving.axes.set_xlim(0, 360)
        self.satelliteMatplotlibMoving.axes.set_ylim(0, 90)
        self.satelliteMatplotlibMoving.axes.set_axis_off()

        # fixed points and horizon plane
        self.satelliteMatplotlib.axes.cla()
        # self.hemisphereMatplotlib.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.satelliteMatplotlib.axes.spines['bottom'].set_color('#2090C0')
        self.satelliteMatplotlib.axes.spines['top'].set_color('#2090C0')
        self.satelliteMatplotlib.axes.spines['left'].set_color('#2090C0')
        self.satelliteMatplotlib.axes.spines['right'].set_color('#2090C0')
        self.satelliteMatplotlib.axes.grid(True, color='#404040')
        self.satelliteMatplotlib.axes.set_facecolor((0, 0, 0, 0))
        self.satelliteMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.satelliteMatplotlib.axes.set_xlim(0, 360)
        self.satelliteMatplotlib.axes.set_xticks(numpy.arange(0, 361, 30))
        self.satelliteMatplotlib.axes.set_ylim(0, 90)
        self.satelliteMatplotlib.axes.tick_params(axis='y', colors='#2090C0', which='both', labelleft='on', labelright='on', labelsize=12)
        self.satelliteMatplotlib.axes.set_xlabel('Azimuth in degrees', color='#2090C0', fontweight='bold', fontsize=12)
        self.satelliteMatplotlib.axes.set_ylabel('Altitude in degrees', color='#2090C0', fontweight='bold', fontsize=12)
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
        self.maskPlotFill,  = self.satelliteMatplotlib.axes.fill(x, y, color='#002000', zorder=-20)
        self.maskPlotMarker,  = self.satelliteMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        # drawing the whole stuff
        self.resizeEvent(0)
