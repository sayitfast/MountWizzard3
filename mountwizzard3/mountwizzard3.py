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
import os
import shutil
import platform
import sys
import datetime
import json
import logging
import logging.handlers
import time
import math
import numpy
import socket
if platform.system() == 'Windows':
    from winreg import *
from queue import Queue
import PyQt5
import PyQt5.QtMultimedia
import numpy
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot
from baseclasses import widget
from widgets import hemisphere_window
from widgets import image_window
from widgets import analyse_window
from widgets import message_window
from gui import main_window_ui
from modeling import model_dispatcher
from mount import mount_dispatcher
from relays import relays
from remote import remote
from dome import dome
from environment import environment
from indi import indi_client
from astrometry import transform
from imaging import imaging
from astrometry import astrometry
from analyse import analysedata
from audio import audio
if platform.system() == 'Windows':
    from automation import automation
from wakeonlan import send_magic_packet
from icons import resources


class MountWizzardApp(widget.MwWidget):
    logger = logging.getLogger(__name__)

    # general signals
    signalMountSiteData = PyQt5.QtCore.pyqtSignal([str, str, str])
    signalJulianDate = PyQt5.QtCore.pyqtSignal(float)
    signalSetAnalyseFilename = PyQt5.QtCore.pyqtSignal(str)
    signalChangeStylesheet = PyQt5.QtCore.pyqtSignal(object, str, object)
    signalSetMountStatus = PyQt5.QtCore.pyqtSignal(int)

    # Locks for accessing shared  data
    sharedAstrometryDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedImagingDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedMountDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedModelingDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedEnvironmentDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedDomeDataLock = PyQt5.QtCore.QReadWriteLock()
    sharedINDIDataLock = PyQt5.QtCore.QReadWriteLock()

    CYCLE_MAIN_LOOP = 250

    def __init__(self):
        super().__init__()

        self.config = {}
        self.setObjectName("Main")

        # setting up the queues for communication between the threads
        self.mountCommandQueue = Queue()
        self.domeCommandQueue = Queue()
        self.modelCommandQueue = Queue()
        self.audioCommandQueue = Queue()
        self.messageQueue = Queue()
        self.imageQueue = Queue()
        self.INDICommandQueue = Queue()
        self.INDIStatusQueue = Queue()

        # initializing the gui from file generated from qt creator
        self.ui = main_window_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.initUI()
        self.checkPlatformDependableMenus()
        self.setWindowTitle('MountWizzard3   (Build: ' + BUILD_NO + ')')
        # enable a matplotlib figure polar plot in main gui
        self.modelWidget = widget.IntegrateMatplotlib(self.ui.model)
        # finalize gui with icons
        self.setupIcons()

        # putting header to message window
        self.messageQueue.put('#BWMountWizzard3  Build:{0} started \n'.format(BUILD_NO))
        self.messageQueue.put('#BWPlatform : {}\n'.format(platform.system()))
        self.messageQueue.put('#BWRelease  : {}\n'.format(platform.release()))
        self.messageQueue.put('#BWMachine  : {}\n'.format(platform.machine()))
        self.messageQueue.put('#BWWorkDir  : {}\n\n'.format(os.getcwd()))

        # get ascom state
        self.checkASCOM()

        # access methods for saving model
        self.analyse = analysedata.Analyse(self)

        # instantiating all subclasses and connecting thread signals
        # mount class
        self.threadMountDispatcher = PyQt5.QtCore.QThread()
        self.workerMountDispatcher = mount_dispatcher.MountDispatcher(self, self.threadMountDispatcher)
        self.threadMountDispatcher.setObjectName("MountDispatcher")
        self.workerMountDispatcher.moveToThread(self.threadMountDispatcher)
        self.threadMountDispatcher.started.connect(self.workerMountDispatcher.run)
        # INDI client framework
        self.threadINDI = PyQt5.QtCore.QThread()
        self.workerINDI = indi_client.INDIClient(self, self.threadINDI)
        self.threadINDI.setObjectName("INDI")
        self.workerINDI.moveToThread(self.threadINDI)
        self.threadINDI.started.connect(self.workerINDI.run)
        self.workerINDI.status.connect(self.setINDIStatus)
        # threading for environment data
        self.threadEnvironment = PyQt5.QtCore.QThread()
        self.workerEnvironment = environment.Environment(self, self.threadEnvironment)
        self.threadEnvironment.setObjectName("Environment")
        self.workerEnvironment.moveToThread(self.threadEnvironment)
        self.threadEnvironment.started.connect(self.workerEnvironment.run)
        self.workerEnvironment.signalEnvironmentConnected.connect(self.setEnvironmentStatus)
        # threading for ascom dome data
        self.threadDome = PyQt5.QtCore.QThread()
        self.workerDome = dome.Dome(self, self.threadDome)
        self.threadDome.setObjectName("Dome")
        self.workerDome.moveToThread(self.threadDome)
        self.threadDome.started.connect(self.workerDome.run)
        self.workerDome.signalDomeConnected.connect(self.setDomeStatus)
        # threading for remote shutdown
        self.threadRemote = PyQt5.QtCore.QThread()
        self.workerRemote = remote.Remote(self, self.threadRemote)
        self.threadRemote.setObjectName("Remote")
        self.workerRemote.moveToThread(self.threadRemote)
        self.threadRemote.started.connect(self.workerRemote.run)
        self.workerRemote.signalRemoteShutdown.connect(self.saveConfigQuit)
        # threading for audio playing
        self.threadAudio = PyQt5.QtCore.QThread()
        self.workerAudio = audio.Audio(self, self.threadAudio)
        self.threadAudio.setObjectName("Audio")
        self.workerAudio.moveToThread(self.threadAudio)
        self.threadAudio.started.connect(self.workerAudio.run)
        # threading for relay handling shutdown
        self.threadRelay = PyQt5.QtCore.QThread()
        self.workerRelay = relays.Relays(self, self.threadRelay)
        self.threadRelay.setObjectName("Relay")
        self.workerRelay.moveToThread(self.threadRelay)
        self.threadRelay.started.connect(self.workerRelay.run)
        # threading for imaging apps
        self.threadImaging = PyQt5.QtCore.QThread()
        self.workerImaging = imaging.Imaging(self, self.threadImaging)
        self.threadImaging.setObjectName("Imaging")
        self.workerImaging.moveToThread(self.threadImaging)
        self.threadImaging.started.connect(self.workerImaging.run)
        # threading for astrometry apps
        self.threadAstrometry = PyQt5.QtCore.QThread()
        self.workerAstrometry = astrometry.Astrometry(self, self.threadAstrometry)
        self.threadAstrometry.setObjectName("Astrometry")
        self.workerAstrometry.moveToThread(self.threadAstrometry)
        self.threadAstrometry.started.connect(self.workerAstrometry.run)
        # threading for updater automation
        if platform.system() == 'Windows':
            self.threadAutomation = PyQt5.QtCore.QThread()
            self.workerAutomation = automation.Automation(self, self.threadAutomation)
            self.threadAutomation.setObjectName("Automation")
            self.workerAutomation.moveToThread(self.threadAutomation)
            self.threadAutomation.started.connect(self.workerAutomation.run)
        # modeling
        self.threadModelingDispatcher = PyQt5.QtCore.QThread()
        self.workerModelingDispatcher = model_dispatcher.ModelingDispatcher(self, self.threadModelingDispatcher)
        self.threadModelingDispatcher.setObjectName("ModelingDispatcher")
        self.workerModelingDispatcher.moveToThread(self.threadModelingDispatcher)
        self.threadModelingDispatcher.started.connect(self.workerModelingDispatcher.run)

        # gui for additional windows
        self.imageWindow = image_window.ImagesWindow(self)
        self.messageWindow = message_window.MessageWindow(self)
        self.analyseWindow = analyse_window.AnalyseWindow(self)
        self.hemisphereWindow = hemisphere_window.HemisphereWindow(self)

        # map all the button to functions for gui
        self.mappingFunctions()

        # loading config data - will be config.cfg
        self.loadConfigData()

        # setting loglevel
        self.setLoggingLevel()
        # starting loop for cyclic data queues to gui from threads
        self.mainLoopTimer = PyQt5.QtCore.QTimer(self)
        self.mainLoopTimer.setSingleShot(False)
        self.mainLoopTimer.timeout.connect(self.mainLoop)
        self.mainLoopTimer.start(self.CYCLE_MAIN_LOOP)

    def mappingFunctions(self):
        self.workerMountDispatcher.signalMountShowAlignmentModel.connect(lambda: self.showModelErrorPolar(self.modelWidget))
        self.ui.btn_saveConfigQuit.clicked.connect(self.saveConfigQuit)
        self.ui.btn_saveConfig.clicked.connect(self.saveConfig)
        self.ui.btn_saveConfigAs.clicked.connect(self.saveConfigAs)
        self.ui.btn_loadFrom.clicked.connect(self.loadConfigDataFrom)
        self.ui.btn_mountBoot.clicked.connect(self.mountBoot)
        self.ui.btn_mountPark.clicked.connect(lambda: self.mountCommandQueue.put(':PO#:hP#'))
        self.ui.btn_mountUnpark.clicked.connect(lambda: self.mountCommandQueue.put(':PO#'))
        self.ui.btn_startTracking.clicked.connect(lambda: self.mountCommandQueue.put(':PO#:AP#'))
        self.ui.btn_stopTracking.clicked.connect(lambda: self.mountCommandQueue.put(':RT9#'))
        self.ui.btn_setTrackingLunar.clicked.connect(lambda: self.mountCommandQueue.put(':RT0#'))
        self.ui.btn_setTrackingSolar.clicked.connect(lambda: self.mountCommandQueue.put(':RT1#'))
        self.ui.btn_setTrackingSideral.clicked.connect(lambda: self.mountCommandQueue.put(':RT2#'))
        self.ui.btn_setRefractionCorrection.clicked.connect(self.setRefractionCorrection)
        self.ui.btn_stop.clicked.connect(lambda: self.mountCommandQueue.put(':STOP#'))
        self.ui.btn_mountPos1.clicked.connect(self.mountPosition1)
        self.ui.btn_mountPos2.clicked.connect(self.mountPosition2)
        self.ui.btn_mountPos3.clicked.connect(self.mountPosition3)
        self.ui.btn_mountPos4.clicked.connect(self.mountPosition4)
        self.ui.btn_mountPos5.clicked.connect(self.mountPosition5)
        self.ui.btn_mountPos6.clicked.connect(self.mountPosition6)
        self.ui.le_parkPos1Text.textEdited.connect(lambda: self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text()))
        self.ui.le_parkPos2Text.textEdited.connect(lambda: self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text()))
        self.ui.le_parkPos3Text.textEdited.connect(lambda: self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text()))
        self.ui.le_parkPos4Text.textEdited.connect(lambda: self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text()))
        self.ui.le_parkPos5Text.textEdited.connect(lambda: self.ui.btn_mountPos5.setText(self.ui.le_parkPos5Text.text()))
        self.ui.le_parkPos6Text.textEdited.connect(lambda: self.ui.btn_mountPos6.setText(self.ui.le_parkPos6Text.text()))
        self.ui.le_horizonLimitHigh.textEdited.connect(self.setHorizonLimitHigh)
        self.ui.le_horizonLimitLow.textEdited.connect(self.setHorizonLimitLow)
        self.ui.le_slewRate.textEdited.connect(self.setSlewRate)
        self.ui.btn_setDualTracking.clicked.connect(self.setDualTracking)
        self.ui.btn_setUnattendedFlip.clicked.connect(self.setUnattendedFlip)
        self.ui.btn_setupAscomDomeDriver.clicked.connect(self.workerAscomDomeSetup)
        self.ui.btn_setupAscomEnvironmentDriver.clicked.connect(self.workerAscomEnvironmentSetup)
        self.ui.btn_cancelFullModel.clicked.connect(self.cancelFullModel)
        self.ui.btn_cancelInitialModel.clicked.connect(self.cancelInitialModel)
        self.ui.btn_cancelAnalyseModel.clicked.connect(self.cancelAnalyseModeling)
        self.ui.btn_cancelRunTargetRMSAlignment.clicked.connect(self.cancelRunTargetRMSFunction)
        self.ui.checkUseMinimumHorizonLine.stateChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.checkUseFileHorizonLine.stateChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.altitudeMinimumHorizon.valueChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.btn_loadAnalyseData.clicked.connect(self.selectAnalyseFileName)
        self.ui.btn_openAnalyseWindow.clicked.connect(self.analyseWindow.showWindow)
        self.ui.btn_openMessageWindow.clicked.connect(self.messageWindow.showWindow)
        self.ui.btn_openHemisphereWindow.clicked.connect(self.hemisphereWindow.showWindow)
        self.ui.btn_openImageWindow.clicked.connect(self.imageWindow.showWindow)
        self.workerDome.domeStatusText.connect(self.setDomeStatusText)
        self.workerImaging.cameraStatusText.connect(self.setCameraStatusText)
        self.workerImaging.cameraExposureTime.connect(self.setCameraExposureTime)
        self.workerAstrometry.astrometryStatusText.connect(self.setAstrometryStatusText)
        self.workerAstrometry.astrometrySolvingTime.connect(self.setAstrometrySolvingTime)
        self.ui.loglevelDebug.clicked.connect(self.setLoggingLevel)
        self.ui.loglevelInfo.clicked.connect(self.setLoggingLevel)
        self.ui.loglevelWarning.clicked.connect(self.setLoggingLevel)
        self.ui.loglevelError.clicked.connect(self.setLoggingLevel)
        self.signalSetAnalyseFilename.connect(self.setAnalyseFilename)
        self.ui.btn_runBatchModel.clicked.connect(self.runBatchModel)
        # setting up stylesheet change for buttons
        self.signalChangeStylesheet.connect(self.changeStylesheet)
        self.signalSetMountStatus.connect(self.setMountStatus)

    @staticmethod
    def timeStamp():
        return time.strftime('%H:%M:%S - ', time.localtime())

    @staticmethod
    def changeStylesheet(ui, item, value):
        ui.setProperty(item, value)
        ui.style().unpolish(ui)
        ui.style().polish(ui)

    def setupIcons(self):
        # show icon in main gui and add some icons for push buttons
        self.widgetIcon(self.ui.btn_openMessageWindow, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DesktopIcon))
        self.widgetIcon(self.ui.btn_openAnalyseWindow, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DesktopIcon))
        self.widgetIcon(self.ui.btn_openImageWindow, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DesktopIcon))
        self.widgetIcon(self.ui.btn_openHemisphereWindow, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DesktopIcon))
        self.widgetIcon(self.ui.btn_saveConfigAs, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogSaveButton))
        self.widgetIcon(self.ui.btn_loadFrom, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DirOpenIcon))
        self.widgetIcon(self.ui.btn_saveConfig, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogSaveButton))
        self.widgetIcon(self.ui.btn_saveConfigQuit, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogSaveButton))
        self.widgetIcon(self.ui.btn_mountBoot, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogApplyButton))
        self.widgetIcon(self.ui.btn_mountShutdown, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_MessageBoxCritical))
        self.widgetIcon(self.ui.btn_runInitialModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_cancelFullModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogCancelButton))
        self.widgetIcon(self.ui.btn_runFullModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_cancelInitialModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogCancelButton))
        self.widgetIcon(self.ui.btn_generateInitialPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_plateSolveSync, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_generateGridPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_generateMaxPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_generateNormalPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_generateMinPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_generateDSOPoints, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_runTimeChangeModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_runHystereseModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward))
        self.widgetIcon(self.ui.btn_cancelAnalyseModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogCancelButton))
        self.widgetIcon(self.ui.btn_stop, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_MessageBoxWarning))
        self.widgetIcon(self.ui.btn_startTracking, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogYesButton))
        self.widgetIcon(self.ui.btn_stopTracking, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogNoButton))
        self.widgetIcon(self.ui.btn_loadModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DirOpenIcon))
        self.widgetIcon(self.ui.btn_saveModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_DialogSaveButton))
        self.widgetIcon(self.ui.btn_deleteModel, PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_TrashIcon))

        # PyQt5.QtWidgets.qApp.style().standardIcon(PyQt5.QtWidgets.QStyle.SP_ArrowForward)
        # the icon picture in gui
        pixmap = PyQt5.QtGui.QPixmap(':/mw.ico')
        pixmap = pixmap.scaled(90, 90)
        self.ui.mainicon.setPixmap(pixmap)
        pixmap = PyQt5.QtGui.QPixmap(':/azimuth1.png')
        self.ui.picAZ.setPixmap(pixmap)
        pixmap = PyQt5.QtGui.QPixmap(':/altitude1.png')
        self.ui.picALT.setPixmap(pixmap)

    def showModelErrorPolar(self, widget):
        widget.fig.clf()
        widget.axes = widget.fig.add_subplot(1, 1, 1, polar=True)
        widget.axes.grid(True, color='#404040')
        widget.axes.set_title('Actual Mount Model', color='white', fontweight='bold', y=1.15)
        widget.fig.subplots_adjust(left=0.075, right=0.975, bottom=0.075, top=0.925)
        widget.axes.set_facecolor((32/256, 32/256, 32/256))
        widget.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        widget.axes.tick_params(axis='y', colors='#2090C0', labelsize=12)
        widget.axes.set_theta_zero_location('N')
        widget.axes.set_theta_direction(-1)
        widget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        widget.axes.set_yticklabels(yLabel, color='white')
        if 'ModelIndex' in self.workerMountDispatcher.data:
            if len(self.workerMountDispatcher.data['ModelIndex']) != 0:
                azimuth = numpy.asarray(self.workerMountDispatcher.data['ModelAzimuth'])
                altitude = numpy.asarray(self.workerMountDispatcher.data['ModelAltitude'])
                cm = matplotlib.pyplot.cm.get_cmap('RdYlGn_r')
                colors = numpy.asarray(self.workerMountDispatcher.data['ModelError'])
                scaleErrorMax = max(colors)
                scaleErrorMin = min(colors)
                area = [150 if x >= max(colors) else 40 for x in self.workerMountDispatcher.data['ModelError']]
                theta = azimuth / 180.0 * math.pi
                r = 90 - altitude
                scatter = widget.axes.scatter(theta, r, c=colors, vmin=scaleErrorMin, vmax=scaleErrorMax, s=area, cmap=cm)
                scatter.set_alpha(0.75)
                colorbar = widget.fig.colorbar(scatter, pad=0.1)
                colorbar.set_label('Error [arcsec]', color='white')
                matplotlib.pyplot.setp(matplotlib.pyplot.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        widget.axes.set_rmax(90)
        widget.axes.set_rmin(0)
        widget.draw()

    def checkPlatformDependableMenus(self):
        # get index of analyse data:
        index = self.ui.mainTabWidget.indexOf(self.ui.mainTabWidget.findChild(PyQt5.QtWidgets.QWidget, 'Analyse'))
        self.ui.mainTabWidget.removeTab(index)
        if platform.system() != 'Windows':
            # get index of ASCOM data:
            index = self.ui.settingsTabWidget.indexOf(self.ui.settingsTabWidget.findChild(PyQt5.QtWidgets.QWidget, 'ASCOM'))
            self.ui.settingsTabWidget.removeTab(index)
            index = self.ui.settingsTabWidget.indexOf(self.ui.settingsTabWidget.findChild(PyQt5.QtWidgets.QWidget, 'Uploads'))
            self.ui.settingsTabWidget.removeTab(index)

    def setLoggingLevel(self):
        if self.ui.loglevelDebug.isChecked():
            logging.getLogger().setLevel(logging.DEBUG)
        elif self.ui.loglevelInfo.isChecked():
            logging.getLogger().setLevel(logging.INFO)
        elif self.ui.loglevelWarning.isChecked():
            logging.getLogger().setLevel(logging.WARNING)
        elif self.ui.loglevelError.isChecked():
            logging.getLogger().setLevel(logging.ERROR)

    def initConfigMain(self):
        # initialize all configs in submodules, if necessary stop thread and restart thread for loading the desired driver
        if platform.system() == 'Windows':
            if self.workerAutomation.isRunning:
                self.workerAutomation.stop()
        if self.workerRemote.isRunning:
            self.workerRemote.stop()
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        if self.workerDome.isRunning:
            self.workerDome.stop()
        if self.workerAstrometry.isRunning:
            self.workerAstrometry.stop()
        if self.workerImaging.isRunning:
            self.workerImaging.stop()
        if self.workerMountDispatcher.isRunning:
            self.workerMountDispatcher.stop()
        if self.workerModelingDispatcher.isRunning:
            self.workerModelingDispatcher.stop()
        if self.workerINDI.isRunning:
            self.workerINDI.stop()
        if self.workerRelay.isRunning:
            self.workerRelay.stop()
        if self.workerAudio.isRunning:
            self.workerAudio.stop()
        # update the configuration
        if 'ConfigName' in self.config:
            self.logger.info('Setting up new configuration with name: [{0}]'.format(self.config['ConfigName']))
            self.messageQueue.put('Setting up new configuration with name: [{0}]\n'.format(self.config['ConfigName']))
        self.initConfig()
        self.workerINDI.initConfig()
        self.workerMountDispatcher.initConfig()
        self.workerModelingDispatcher.initConfig()
        self.workerEnvironment.initConfig()
        self.workerDome.initConfig()
        self.workerRemote.initConfig()
        self.workerImaging.initConfig()
        self.workerAstrometry.initConfig()
        if platform.system() == 'Windows':
            self.workerAutomation.initConfig()
        # now the window config
        self.hemisphereWindow.initConfig()
        self.imageWindow.initConfig()
        self.analyseWindow.initConfig()
        self.messageWindow.initConfig()
        self.workerRelay.initConfig()
        self.workerAudio.initConfig()

        if not self.workerAudio.isRunning:
            self.threadAudio.start()
        if self.ui.checkEnableRelay.isChecked():
            self.threadRelay.start()
        if self.ui.checkEnableINDI.isChecked():
            self.threadINDI.start()
        if self.ui.checkEnableRemoteAccess.isChecked():
            self.threadRemote.start()
        if platform.system() == 'Windows':
            self.threadAutomation.start()
        if not self.workerMountDispatcher.isRunning:
            self.threadMountDispatcher.start()
        if not self.workerEnvironment.isRunning:
            self.threadEnvironment.start()
        if not self.workerDome.isRunning:
            self.threadDome.start()
        if not self.workerAstrometry.isRunning:
            self.threadAstrometry.start()
        if not self.workerImaging.isRunning:
            self.threadImaging.start()
        if not self.workerModelingDispatcher.isRunning:
            self.threadModelingDispatcher.start()

        # make windows visible, if they were on the desktop depending on their show status
        if self.imageWindow.showStatus:
            self.imageWindow.showWindow()
        else:
            self.imageWindow.close()
        if self.messageWindow.showStatus:
            self.messageWindow.showWindow()
        else:
            self.messageWindow.close()
        if self.hemisphereWindow.showStatus:
            self.hemisphereWindow.showWindow()
        else:
            self.hemisphereWindow.close()
        if self.analyseWindow.showStatus:
            self.analyseWindow.showWindow()
        else:
            self.analyseWindow.close()

    def initConfig(self):
        # now try to set the right values in class
        try:
            if 'ParkPosText1' in self.config:
                self.ui.le_parkPos1Text.setText(self.config['ParkPosText1'])
                self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text())
            if 'ParkPosAlt1' in self.config:
                self.ui.le_altParkPos1.setText(self.config['ParkPosAlt1'])
            if 'ParkPosAz1' in self.config:
                self.ui.le_azParkPos1.setText(self.config['ParkPosAz1'])
            if 'ParkPosText2' in self.config:
                self.ui.le_parkPos2Text.setText(self.config['ParkPosText2'])
                self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text())
            if 'ParkPosAlt2' in self.config:
                self.ui.le_altParkPos2.setText(self.config['ParkPosAlt2'])
            if 'ParkPosAz2' in self.config:
                self.ui.le_azParkPos2.setText(self.config['ParkPosAz2'])
            if 'ParkPosText3' in self.config:
                self.ui.le_parkPos3Text.setText(self.config['ParkPosText3'])
                self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text())
            if 'ParkPosAlt3' in self.config:
                self.ui.le_altParkPos3.setText(self.config['ParkPosAlt3'])
            if 'ParkPosAz3' in self.config:
                self.ui.le_azParkPos3.setText(self.config['ParkPosAz3'])
            if 'ParkPosText4' in self.config:
                self.ui.le_parkPos4Text.setText(self.config['ParkPosText4'])
                self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text())
            if 'ParkPosAlt4' in self.config:
                self.ui.le_altParkPos4.setText(self.config['ParkPosAlt4'])
            if 'ParkPosAz4' in self.config:
                self.ui.le_azParkPos4.setText(self.config['ParkPosAz4'])
            if 'ParkPosText5' in self.config:
                self.ui.le_parkPos5Text.setText(self.config['ParkPosText5'])
                self.ui.btn_mountPos5.setText(self.ui.le_parkPos5Text.text())
            if 'ParkPosAlt5' in self.config:
                self.ui.le_altParkPos5.setText(self.config['ParkPosAlt5'])
            if 'ParkPosAz5' in self.config:
                self.ui.le_azParkPos5.setText(self.config['ParkPosAz5'])
            if 'ParkPosText6' in self.config:
                self.ui.le_parkPos6Text.setText(self.config['ParkPosText6'])
                self.ui.btn_mountPos6.setText(self.ui.le_parkPos6Text.text())
            if 'ParkPosAlt6' in self.config:
                self.ui.le_altParkPos6.setText(self.config['ParkPosAlt6'])
            if 'ParkPosAz6' in self.config:
                self.ui.le_azParkPos6.setText(self.config['ParkPosAz6'])
            if 'CameraBin' in self.config:
                self.ui.cameraBin.setValue(self.config['CameraBin'])
            if 'CameraExposure' in self.config:
                self.ui.cameraExposure.setValue(self.config['CameraExposure'])
            if 'ISOSetting' in self.config:
                self.ui.isoSetting.setValue(self.config['ISOSetting'])
            if 'CheckFastDownload' in self.config:
                self.ui.checkFastDownload.setChecked(self.config['CheckFastDownload'])
            if 'SettlingTime' in self.config:
                self.ui.settlingTime.setValue(self.config['SettlingTime'])
            if 'TargetRMS' in self.config:
                self.ui.targetRMS.setValue(self.config['TargetRMS'])
            if 'PixelSize' in self.config:
                self.ui.pixelSize.setValue(self.config['PixelSize'])
            if 'FocalLength' in self.config:
                self.ui.focalLength.setValue(self.config['FocalLength'])
            if 'ScaleSubframe' in self.config:
                self.ui.scaleSubframe.setValue(self.config['ScaleSubframe'])
            if 'CheckDoSubframe' in self.config:
                self.ui.checkDoSubframe.setChecked(self.config['CheckDoSubframe'])
            if 'CheckKeepImages' in self.config:
                self.ui.checkKeepImages.setChecked(self.config['CheckKeepImages'])
            if 'AnalyseFileName' in self.config:
                self.ui.le_analyseFileName.setText(self.config['AnalyseFileName'])
            if 'AltitudeTimeChange' in self.config:
                self.ui.altitudeTimeChange.setValue(self.config['AltitudeTimeChange'])
            if 'AzimuthTimeChange' in self.config:
                self.ui.azimuthTimeChange.setValue(self.config['AzimuthTimeChange'])
            if 'NumberRunsTimeChange' in self.config:
                self.ui.numberRunsTimeChange.setValue(self.config['NumberRunsTimeChange'])
            if 'DelayTimeTimeChange' in self.config:
                self.ui.delayTimeTimeChange.setValue(self.config['DelayTimeTimeChange'])
            if 'AltitudeHysterese1' in self.config:
                self.ui.altitudeHysterese1.setValue(self.config['AltitudeHysterese1'])
            if 'AltitudeHysterese2' in self.config:
                self.ui.altitudeHysterese2.setValue(self.config['AltitudeHysterese2'])
            if 'AzimuthHysterese1' in self.config:
                self.ui.azimuthHysterese1.setValue(self.config['AzimuthHysterese1'])
            if 'AzimuthHysterese2' in self.config:
                self.ui.azimuthHysterese2.setValue(self.config['AzimuthHysterese2'])
            if 'NumberRunsHysterese' in self.config:
                self.ui.numberRunsHysterese.setValue(self.config['NumberRunsHysterese'])
            if 'DelayTimeHysterese' in self.config:
                self.ui.delayTimeHysterese.setValue(self.config['DelayTimeHysterese'])
            if 'WindowPositionX' in self.config:
                x = self.config['WindowPositionX']
                y = self.config['WindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'ConfigName' in self.config:
                self.ui.le_configName.setText(self.config['ConfigName'])
            if 'MainTabPosition' in self.config:
                self.ui.mainTabWidget.setCurrentIndex(self.config['MainTabPosition'])
            if 'SettingTabPosition' in self.config:
                self.ui.settingsTabWidget.setCurrentIndex(self.config['SettingTabPosition'])
            if 'CheckLoglevelDebug' in self.config:
                self.ui.loglevelDebug.setChecked(self.config['CheckLoglevelDebug'])
            if 'CheckLoglevelInfo' in self.config:
                self.ui.loglevelInfo.setChecked(self.config['CheckLoglevelInfo'])
            if 'CheckLoglevelWarning' in self.config:
                self.ui.loglevelWarning.setChecked(self.config['CheckLoglevelWarning'])
            if 'CheckLoglevelError' in self.config:
                self.ui.loglevelError.setChecked(self.config['CheckLoglevelError'])

        except Exception as e:
            self.logger.error('Item in config.cfg for main window could not be initialized, error:{0}'.format(e))
        finally:
            pass

    def quit(self):
        self.mainLoopTimer.stop()
        self.workerAstrometry.astrometryCancel.emit()
        self.workerImaging.imagingCancel.emit()
        if platform.system() == 'Windows':
            if self.workerAutomation.isRunning:
                self.workerAutomation.stop()
        if self.workerRemote.isRunning:
            self.workerRemote.stop()
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        if self.workerDome.isRunning:
            self.workerDome.stop()
        if self.workerAstrometry.isRunning:
            self.workerAstrometry.stop()
        if self.workerImaging.isRunning:
            self.workerImaging.stop()
        if self.workerMountDispatcher.isRunning:
            self.workerMountDispatcher.stop()
        if self.workerModelingDispatcher.isRunning:
            self.workerModelingDispatcher.stop()
        if self.workerINDI.isRunning:
            self.workerINDI.stop()
        PyQt5.QtCore.QCoreApplication.quit()

    def storeConfig(self):
        # counting versions : 30 equals v3.0
        self.config['version'] = 30
        self.config['ParkPosText1'] = self.ui.le_parkPos1Text.text()
        self.config['ParkPosAlt1'] = self.ui.le_altParkPos1.text()
        self.config['ParkPosAz1'] = self.ui.le_azParkPos1.text()
        self.config['ParkPosText2'] = self.ui.le_parkPos2Text.text()
        self.config['ParkPosAlt2'] = self.ui.le_altParkPos2.text()
        self.config['ParkPosAz2'] = self.ui.le_azParkPos2.text()
        self.config['ParkPosText3'] = self.ui.le_parkPos3Text.text()
        self.config['ParkPosAlt3'] = self.ui.le_altParkPos3.text()
        self.config['ParkPosAz3'] = self.ui.le_azParkPos3.text()
        self.config['ParkPosText4'] = self.ui.le_parkPos4Text.text()
        self.config['ParkPosAlt4'] = self.ui.le_altParkPos4.text()
        self.config['ParkPosAz4'] = self.ui.le_azParkPos4.text()
        self.config['ParkPosText5'] = self.ui.le_parkPos5Text.text()
        self.config['ParkPosAlt5'] = self.ui.le_altParkPos5.text()
        self.config['ParkPosAz5'] = self.ui.le_azParkPos5.text()
        self.config['ParkPosText6'] = self.ui.le_parkPos6Text.text()
        self.config['ParkPosAlt6'] = self.ui.le_altParkPos6.text()
        self.config['ParkPosAz6'] = self.ui.le_azParkPos6.text()
        self.config['CameraBin'] = self.ui.cameraBin.value()
        self.config['CameraExposure'] = self.ui.cameraExposure.value()
        self.config['CheckFastDownload'] = self.ui.checkFastDownload.isChecked()
        self.config['ISOSetting'] = self.ui.isoSetting.value()
        self.config['SettlingTime'] = self.ui.settlingTime.value()
        self.config['TargetRMS'] = self.ui.targetRMS.value()
        self.config['PixelSize'] = self.ui.pixelSize.value()
        self.config['FocalLength'] = self.ui.focalLength.value()
        self.config['ScaleSubframe'] = self.ui.scaleSubframe.value()
        self.config['CheckDoSubframe'] = self.ui.checkDoSubframe.isChecked()
        self.config['CheckKeepImages'] = self.ui.checkKeepImages.isChecked()
        self.config['WindowPositionX'] = self.pos().x()
        self.config['WindowPositionY'] = self.pos().y()
        self.config['AnalyseFileName'] = self.ui.le_analyseFileName.text()
        self.config['AltitudeTimeChange'] = self.ui.altitudeTimeChange.value()
        self.config['AzimuthTimeChange'] = self.ui.azimuthTimeChange.value()
        self.config['NumberRunsTimeChange'] = self.ui.numberRunsTimeChange.value()
        self.config['DelayTimeTimeChange'] = self.ui.delayTimeTimeChange.value()
        self.config['AltitudeHysterese1'] = self.ui.altitudeHysterese1.value()
        self.config['AltitudeHysterese2'] = self.ui.altitudeHysterese2.value()
        self.config['AzimuthHysterese1'] = self.ui.azimuthHysterese1.value()
        self.config['AzimuthHysterese2'] = self.ui.azimuthHysterese2.value()
        self.config['NumberRunsHysterese'] = self.ui.numberRunsHysterese.value()
        self.config['DelayTimeHysterese'] = self.ui.delayTimeHysterese.value()
        self.config['ConfigName'] = self.ui.le_configName.text()
        self.config['MainTabPosition'] = self.ui.mainTabWidget.currentIndex()
        self.config['SettingTabPosition'] = self.ui.settingsTabWidget.currentIndex()
        self.config['CheckLoglevelDebug'] = self.ui.loglevelDebug.isChecked()
        self.config['CheckLoglevelInfo'] = self.ui.loglevelInfo.isChecked()
        self.config['CheckLoglevelWarning'] = self.ui.loglevelWarning.isChecked()
        self.config['CheckLoglevelError'] = self.ui.loglevelError.isChecked()

        # store config in all submodules
        self.workerMountDispatcher.storeConfig()
        self.workerModelingDispatcher.storeConfig()
        self.workerEnvironment.storeConfig()
        self.workerDome.storeConfig()
        self.workerRemote.storeConfig()
        self.workerImaging.storeConfig()
        self.workerAstrometry.storeConfig()
        if platform.system() == 'Windows':
            self.workerAutomation.storeConfig()
        self.hemisphereWindow.storeConfig()
        self.imageWindow.storeConfig()
        self.analyseWindow.storeConfig()
        self.messageWindow.storeConfig()
        self.workerRelay.storeConfig()
        self.workerINDI.storeConfig()
        self.workerAudio.storeConfig()

    def loadConfigData(self, filepath='config/config.cfg'):
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r') as data_file:
                    self.config = json.load(data_file)
                    # test version
                    if 'version' in self.config:
                        if self.config['version'] >= 30:
                            pass
                            # all ok
                        else:
                            shutil.copyfile(filepath, filepath + '.old')
                            self.messageQueue.put('Old version of config file found, try to convert, old version copied to {0}.old\n'.format(filepath))
                            self.logger.error('Old version of config file found, try to convert, old version copied to {0}.old'.format(filepath))
                    else:
                        shutil.copyfile(filepath, filepath + '.old')
                        self.messageQueue.put('Old version of config file found, try to convert, old version copied to {0}.old\n'.format(filepath))
                        self.logger.error('Old version of config file found, try to convert, old version copied to {0}.old'.format(filepath))
            except Exception as e:
                self.messageQueue.put('#BRConfig.cfg could not be loaded !\n')
                self.logger.error('config.cfg could not be loaded, error:{0}'.format(e))
                self.config = dict()
        else:
            self.messageQueue.put('Generating a new config file!\n')
            self.logger.info('Configuration config.cfg not preset, starting new.')
            self.config = dict()
        # finally start initialisation
        self.initConfigMain()

    def loadConfigDataFrom(self):
        value, ext = self.selectFile(self, 'Open config file', '/config', 'Config files (*.cfg)', True)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            self.loadConfigData(value + '.cfg')
        else:
            self.logger.warning('No config file selected')

    def saveConfigData(self, filepath=''):
        self.storeConfig()
        try:
            if not os.path.isdir(os.getcwd() + '/config'):
                os.makedirs(os.getcwd() + '/config')
            with open('config/config.cfg', 'w') as outfile:
                json.dump(self.config, outfile)
            with open(filepath, 'w') as outfile:
                json.dump(self.config, outfile)
            self.messageQueue.put('Configuration saved.\n')
        except Exception as e:
            self.messageQueue.put('#BRConfig.cfg could not be saved !\n')
            self.logger.error('Item in config.cfg not saved error {0}'.format(e))
            return

    def saveConfigQuit(self):
        filepath = os.getcwd() + '/config/' + self.ui.le_configName.text() + '.cfg'
        self.saveConfigData(filepath)
        self.quit()

    def saveConfig(self):
        filepath = os.getcwd() + '/config/' + self.ui.le_configName.text() + '.cfg'
        self.saveConfigData(filepath)

    def saveConfigAs(self):
        value, ext = self.selectFile(self, 'Save config file', '/config', 'Config files (*.cfg)', False)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            self.saveConfigData(value + '.cfg')
        else:
            self.logger.warning('No config file selected')

    def checkASCOM(self):
        if platform.system() != 'Windows':
            return
        appAvailable, appName, appInstallPath = self.checkRegistrationKeys('ASCOM Platform')
        if appAvailable:
            self.messageQueue.put('Found: {0}\n'.format(appName))
            self.logger.info('Name: {0}, Path: {1}'.format(appName, appInstallPath))
        else:
            self.logger.info('Application ASCOM not found on computer')

    def checkRegistrationKeys(self, appSearchName):
        if platform.machine().endswith('64'):
            regPath = 'SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
        else:
            regPath = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
        appInstallPath = ''
        appInstalled = False
        appName = ''
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, regPath)
            for i in range(0, QueryInfoKey(key)[0]):
                nameKey = EnumKey(key, i)
                subkey = OpenKey(key, nameKey)
                for j in range(0, QueryInfoKey(subkey)[1]):
                    values = EnumValue(subkey, j)
                    if values[0] == 'DisplayName':
                        appName = values[1]
                    if values[0] == 'InstallLocation':
                        appInstallPath = values[1]
                if appSearchName in appName:
                    appInstalled = True
                    CloseKey(subkey)
                    break
                else:
                    CloseKey(subkey)
            CloseKey(key)
            if not appInstalled:
                appInstallPath = ''
                appName = ''
        except Exception as e:
            self.logger.debug('Name: {0}, Path: {1}, error: {2}'.format(appName, appInstallPath, e))
        finally:
            return appInstalled, appName, appInstallPath

    def selectAnalyseFileName(self):
        value, ext = self.selectFile(self, 'Open analyse file', '/analysedata', 'Analyse files (*.dat)', True)
        if value != '':
            self.ui.le_analyseFileName.setText(os.path.basename(value))
            self.analyseWindow.showWindow()
        else:
            self.logger.warning('no file selected')

    def mountBoot(self):
        hostSummary = socket.gethostbyname_ex(socket.gethostname())
        canWOL = False
        self.logger.info('Got following hosts: {0}'.format(hostSummary[2]))
        host = [ip for ip in hostSummary[2] if not ip.startswith('127.')]
        if len(host) == 0:
            self.messageQueue.put('Probably cannot send WOL because check subnet configuration\n')
        else:
            addressMount = socket.gethostbyname(self.ui.le_mountIP.text()).split('.')
            for hostAddress in host:
                addressComputer = hostAddress.split('.')
                if addressComputer[0] == addressMount[0] and addressComputer[1] == addressMount[1] and addressComputer[2] == addressMount[2]:
                    canWOL = True
        if not canWOL:
            self.messageQueue.put('Probably cannot send WOL because computer and mount are not in the same subnet\n')
            self.logger.debug('Cannot send WOL because computer and mount are not in the same subnet')

        self.changeStylesheet(self.ui.btn_mountBoot, 'running', True)
        PyQt5.QtWidgets.QApplication.processEvents()
        send_magic_packet(self.ui.le_mountMAC.text().strip())
        self.messageQueue.put('Send WOL and boot mount\n')
        self.logger.debug('Send WOL packet and boot Mount')
        time.sleep(1)
        self.changeStylesheet(self.ui.btn_mountBoot, 'running', False)

    def setHorizonLimitHigh(self):
        _text = self.ui.le_horizonLimitHigh.text()
        if len(_text) > 0:
            _value = int(_text)
            if _value < 0:
                _value = 0
            elif _value > 90:
                _value = 90
            self.mountCommandQueue.put(':Sh+{0:02d}#'.format(_value))
            self.workerMountDispatcher.data['CurrentHorizonLimitHigh'] = _value

    def setHorizonLimitLow(self):
        _text = self.ui.le_horizonLimitLow.text()
        if len(_text) > 0:
            _value = int(_text)
            if _value < 0:
                _value = 0
            elif _value > 90:
                _value = 90
            self.mountCommandQueue.put(':So+{0:02d}#'.format(_value))
            self.workerMountDispatcher.data['CurrentHorizonLimitLow'] = _value

    def setSlewRate(self):
        _text = self.ui.le_slewRate.text()
        if len(_text) > 0:
            _value = int(_text)
            if _value < 1:
                _value = 1
            elif _value > 15:
                _value = 15
            self.mountCommandQueue.put(':Sw{0:02d}#'.format(_value))
            self.workerMountDispatcher.data['SlewRate'] = _value

    def setDualTracking(self):
        _value = self.ui.le_telescopeDualTrack.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeDualTrack.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeDualTrack.setText('ON')
        self.mountCommandQueue.put(':Sdat{0:1d}#'.format(_value))
        self.workerMountDispatcher.data['DualAxisTracking'] = _value

    def setUnattendedFlip(self):
        _value = self.ui.le_telescopeUnattendedFlip.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeUnattendedFlip.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeUnattendedFlip.setText('ON')
        self.mountCommandQueue.put(':Suaf{0:1d}#'.format(_value))
        self.workerMountDispatcher.data['UnattendedFlip'] = _value

    def setRefractionCorrection(self):
        _value = self.ui.le_refractionStatus.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_refractionStatus.setText('OFF')
        else:
            _value = 1
            self.ui.le_refractionStatus.setText('ON')
        self.mountCommandQueue.put(':SREF{0:1d}#'.format(_value))
        self.workerMountDispatcher.data['RefractionStatus'] = _value

    def mountPosition1(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos1.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos1.text())))
        self.mountCommandQueue.put(':MA#')

    def mountPosition2(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos2.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos2.text())))
        self.mountCommandQueue.put(':MA#')

    def mountPosition3(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos3.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos3.text())))
        self.mountCommandQueue.put(':MA#')

    def mountPosition4(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos4.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos4.text())))
        self.mountCommandQueue.put(':MA#')

    def mountPosition5(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos5.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos5.text())))
        self.mountCommandQueue.put(':MA#')

    def mountPosition6(self):
        self.mountCommandQueue.put(':PO#')
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos6.text())))
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos6.text())))
        self.mountCommandQueue.put(':MA#')

    def workerAscomEnvironmentSetup(self):
        if platform.system() != 'Windows':
            return
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        self.workerEnvironment.ascom.setupDriver()
        self.ui.le_ascomEnvironmentDriverName.setText(self.workerEnvironment.ascom.driverName)
        self.threadEnvironment.start()

    def workerAscomDomeSetup(self):
        if platform.system() != 'Windows':
            return
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerDome.isRunning:
            self.workerDome.stop()
        self.workerDome.ascom.setupDriver()
        self.ui.le_ascomDomeDriverName.setText(self.workerDome.ascom.driverName)
        self.threadDome.start()

    def runBatchModel(self):
        value, ext = self.selectFile(self, 'Open analyse file for model programming', '/analysedata', 'Analyse files (*.dat)', True)
        if value == '':
            self.logger.warning('No file selected')
            return
        nameDataFile = os.path.basename(value)
        self.logger.info('Modeling from {0}'.format(nameDataFile))
        data = self.analyse.loadData(nameDataFile)
        self.workerMountDispatcher.programBatchData(data)

    def cancelFullModel(self):
        # cancel only works if modeling gis running. otherwise recoloring button after stop won't happen
        if self.workerModelingDispatcher.modelingRunner.modelRun:
            # color button
            self.changeStylesheet(self.ui.btn_cancelFullModel, 'cancel', True)
            self.logger.info('User canceled modeling')
            # send signal to cancel model run
            self.workerModelingDispatcher.signalCancel.emit()

    def cancelInitialModel(self):
        if self.workerModelingDispatcher.modelingRunner.modelRun:
            self.changeStylesheet(self.ui.btn_cancelInitialModel, 'cancel', True)
            self.logger.info('User canceled modeling')
            self.workerModelingDispatcher.signalCancel.emit()

    def cancelAnalyseModeling(self):
        if self.workerModelingDispatcher.modelingRunner.modelRun:
            self.changeStylesheet(self.ui.btn_cancelAnalyseModel, 'cancel', True)
            self.logger.info('User canceled analyse modeling')
            self.workerModelingDispatcher.signalCancel.emit()

    def cancelRunTargetRMSFunction(self):
        if self.workerMountDispatcher.runTargetRMS:
            self.ui.btn_cancelRunTargetRMSAlignment.setProperty('cancel', True)
            self.ui.btn_cancelRunTargetRMSAlignment.style().unpolish(self.ui.btn_cancelRunTargetRMSAlignment)
            self.ui.btn_cancelRunTargetRMSAlignment.style().polish(self.ui.btn_cancelRunTargetRMSAlignment)
            self.workerMountDispatcher.signalCancelRunTargetRMS.emit()

    def setAnalyseFilename(self, filename):
        self.ui.le_analyseFileName.setText(filename)

    def setEnvironmentStatus(self, status):
        if status == 0:
            self.signalChangeStylesheet.emit(self.ui.btn_environmentConnected, 'color', 'gray')
        elif status == 1:
            self.signalChangeStylesheet.emit(self.ui.btn_environmentConnected, 'color', 'red')
        elif status == 2:
            self.signalChangeStylesheet.emit(self.ui.btn_environmentConnected, 'color', 'yellow')
        elif status == 3:
            self.signalChangeStylesheet.emit(self.ui.btn_environmentConnected, 'color', 'green')

    def fillEnvironmentData(self):
        for valueName in self.workerEnvironment.data:
            if valueName == 'DewPoint':
                self.ui.le_dewPoint.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'Temperature':
                self.ui.le_temperature.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'Humidity':
                self.ui.le_humidity.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'Pressure':
                self.ui.le_pressure.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'CloudCover':
                self.ui.le_cloudCover.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'RainRate':
                self.ui.le_rainRate.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'WindSpeed':
                self.ui.le_windSpeed.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'WindDirection':
                self.ui.le_windDirection.setText('{0:4.1f}'.format(self.workerEnvironment.data[valueName]))
            elif valueName == 'SQR':
                self.ui.le_SQR.setText('{0:4.2f}'.format(self.workerEnvironment.data[valueName]))

    def fillINDIData(self, data):
        if data['Name'] == 'CCD':
            self.ui.le_INDICCD.setText(data['value'])
        elif data['Name'] == 'Environment':
            self.ui.le_INDIEnvironment.setText(data['value'])
        elif data['Name'] == 'Dome':
            self.ui.le_INDIDome.setText(data['value'])
        elif data['Name'] == 'Telescope':
            self.ui.le_INDITelescope.setText(data['value'])
        elif data['Name'] == 'CameraStatus':
            self.imageWindow.ui.le_INDICameraStatus.setText(data['value'])

    def setMountStatus(self, status):
        if status == 0:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif status == 1:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: yellow; color:black;}')
        elif status == 2:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')

    def fillMountData(self):
        for valueName in self.workerMountDispatcher.data:
            if valueName == 'Reply':
                pass
            if valueName == 'DualAxisTracking':
                if self.workerMountDispatcher.data[valueName] == '1':
                    self.ui.le_telescopeDualTrack.setText('ON')
                else:
                    self.ui.le_telescopeDualTrack.setText('OFF')
            if valueName == 'NumberAlignmentStars':
                self.ui.le_alignNumberStars.setText(str(self.workerMountDispatcher.data[valueName]))
                self.ui.le_alignNumberStars2.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelRMSError':
                self.ui.le_alignErrorRMS.setText(str(self.workerMountDispatcher.data[valueName]))
                self.ui.le_alignErrorRMS2.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelErrorPosAngle':
                self.ui.le_alignErrorPosAngle.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelPolarError':
                self.ui.le_alignErrorPolar.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelOrthoError':
                self.ui.le_alignErrorOrtho.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelTerms':
                self.ui.le_alignNumberTerms.setText(str(self.workerMountDispatcher.data[valueName]))
                self.ui.le_alignNumberTerms2.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelKnobTurnAz':
                self.ui.le_alignKnobTurnAz.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelKnobTurnAlt':
                self.ui.le_alignKnobTurnAlt.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelErrorAz':
                self.ui.le_alignErrorAz.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'ModelErrorAlt':
                self.ui.le_alignErrorAlt.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'CurrentHorizonLimitLow':
                if not self.ui.le_horizonLimitLow.hasFocus():
                    self.ui.le_horizonLimitLow.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'CurrentHorizonLimitHigh':
                if not self.ui.le_horizonLimitLow.hasFocus():
                    self.ui.le_horizonLimitHigh.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'SiteLongitude':
                self.ui.le_siteLongitude.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'SiteLatitude':
                self.ui.le_siteLatitude.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'SiteHeight':
                self.ui.le_siteElevation.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'JulianDate':
                self.ui.le_JulianDate.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'LocalSiderealTime':
                self.ui.le_localSiderealTime.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'TelescopeTempDEC':
                self.ui.le_telescopeTempDECMotor.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'RefractionTemperature':
                self.ui.le_refractionTemperature.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'RefractionPressure':
                self.ui.le_refractionPressure.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'RefractionStatus':
                if self.workerMountDispatcher.data[valueName] == '1':
                    self.ui.le_refractionStatus.setText('ON')
                else:
                    self.ui.le_refractionStatus.setText('OFF')
            if valueName == 'MountStatus':
                self.ui.le_mountStatus.setText(str(self.workerMountDispatcher.statusReference[self.workerMountDispatcher.data[valueName]]))
            if valueName == 'TelescopeDEC':
                self.ui.le_telescopeDEC.setText(self.workerMountDispatcher.data[valueName])
            if valueName == 'TelescopeRA':
                self.ui.le_telescopeRA.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'TelescopeAltitude':
                self.ui.le_telescopeAltitude.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'TelescopeAzimuth':
                self.ui.le_telescopeAzimut.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'SlewRate':
                if not self.ui.le_horizonLimitLow.hasFocus():
                    self.ui.le_slewRate.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'MeridianLimitGuide':
                self.ui.le_meridianLimitGuide.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'MeridianLimitSlew':
                self.ui.le_meridianLimitSlew.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'UnattendedFlip':
                if self.workerMountDispatcher.data[valueName] == '1':
                    self.ui.le_telescopeUnattendedFlip.setText('ON')
                else:
                    self.ui.le_telescopeUnattendedFlip.setText('OFF')
            if valueName == 'TimeToFlip':
                self.ui.le_timeToFlip.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'TimeToMeridian':
                self.ui.le_timeToMeridian.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'FirmwareProductName':
                self.ui.le_firmwareProductName.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'FirmwareNumber':
                self.ui.le_firmwareNumber.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'FirmwareDate':
                self.ui.le_firmwareDate.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'FirmwareTime':
                self.ui.le_firmwareTime.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'HardwareVersion':
                self.ui.le_hardwareVersion.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'TelescopePierSide':
                self.ui.le_telescopePierSide.setText(str(self.workerMountDispatcher.data[valueName]))
            if valueName == 'UTCDataValid':
                if self.workerMountDispatcher.data[valueName] == 'V':
                    self.ui.le_UTCDataValid.setText('VALID')
                elif self.workerMountDispatcher.data[valueName] == 'E':
                    self.ui.le_UTCDataValid.setText('EXPIRED')
                else:
                    self.ui.le_UTCDataValid.setText('INVALID')
            if valueName == 'UTCDataExpirationDate':
                self.ui.le_UTCDataExpirationDate.setText(str(self.workerMountDispatcher.data[valueName]))

    def setDomeStatus(self, status):
        if status == 0:
            self.signalChangeStylesheet.emit(self.ui.btn_domeConnected, 'color', 'gray')
        elif status == 1:
            self.signalChangeStylesheet.emit(self.ui.btn_domeConnected, 'color', 'red')
        elif status == 2:
            self.signalChangeStylesheet.emit(self.ui.btn_domeConnected, 'color', 'yellow')
        elif status == 3:
            self.signalChangeStylesheet.emit(self.ui.btn_domeConnected, 'color', 'green')

    def setINDIStatus(self, status):
        if status == 0:
            self.ui.le_INDIStatus.setText('UnconnectedState')
            self.signalChangeStylesheet.emit(self.ui.btn_INDIConnected, 'color', 'red')
        elif status == 3:
            self.ui.le_INDIStatus.setText('ConnectedState')
            self.signalChangeStylesheet.emit(self.ui.btn_INDIConnected, 'color', 'green')
        elif status == 1:
            self.ui.le_INDIStatus.setText('Host lookup')
        elif status == 2:
            self.ui.le_INDIStatus.setText('Host found')
        else:
            self.ui.le_INDIStatus.setText('Error')
        if not self.ui.checkEnableINDI.isChecked():
            self.signalChangeStylesheet.emit(self.ui.btn_INDIConnected, 'color', 'gray')

    def setDomeStatusText(self, status):
        self.ui.le_domeStatusText.setText(status)

    def setCameraStatusText(self, status):
        self.imageWindow.ui.le_cameraStatusText.setText(status)
        self.ui.le_cameraStatusText.setText(status)

    def setCameraExposureTime(self, status):
        self.imageWindow.ui.le_cameraExposureTime.setText(status)

    def setAstrometryStatusText(self, status):
        self.ui.le_astrometryStatusText.setText(status)
        self.imageWindow.ui.le_astrometryStatusText.setText(status)

    def setAstrometrySolvingTime(self, status):
        self.imageWindow.ui.le_astrometrySolvingTime.setText(status)

    @PyQt5.QtCore.pyqtSlot()
    def mainLoop(self):
        self.fillMountData()
        self.fillEnvironmentData()
        self.ui.le_modelingTimeActual.setText(datetime.datetime.now().strftime('%H:%M:%S'))
        while not self.INDIStatusQueue.empty():
            data = self.INDIStatusQueue.get()
            self.fillINDIData(data)
        while not self.messageQueue.empty():
            text = self.messageQueue.get()
            textadd = self.timeStamp()
            if text == 'delete':
                self.messageWindow.ui.messages.clear()
            elif text.startswith('ToModel>'):
                self.hemisphereWindow.ui.le_numberPointsToProcess.setText(text[8:])
            elif text.startswith('Slewed>'):
                self.hemisphereWindow.ui.le_numberPointsSlewed.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsSlewed.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()))
            elif text.startswith('Imaged>'):
                self.hemisphereWindow.ui.le_numberPointsImaged.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsImaged.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()))
            elif text.startswith('Solved>'):
                self.hemisphereWindow.ui.le_numberPointsSolved.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsSolved.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToProcess.text()))
            elif text.startswith('percent'):
                self.ui.bar_modelingStatusPercent.setValue(int(1000 * float(text[7:])))
            elif text.startswith('timeEst'):
                self.ui.le_modelingTimeEstimated.setText(text[7:])
            elif text.startswith('timeEla'):
                self.ui.le_modelingTimeElapsed.setText(text[7:])
            elif text.startswith('timeFin'):
                self.ui.le_modelingTimeFinished.setText(text[7:])
            elif text.startswith('#BW'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_WHITE)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(textadd + text[3:])
            elif text.startswith('#BG'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_GREEN)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(textadd + text[3:])
            elif text.startswith('#BY'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_YELLOW)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(textadd + text[3:])
            elif text.startswith('#BR'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_RED)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(textadd + text[3:])
            elif text.startswith('#BO'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ORANGE)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(textadd + text[3:])
            else:
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ASTRO)
                self.messageWindow.ui.messages.setFontWeight(PyQt5.QtGui.QFont.Normal)
                self.messageWindow.ui.messages.insertPlainText(textadd + text)
            self.messageWindow.ui.messages.moveCursor(PyQt5.QtGui.QTextCursor.End)
        # update application name in pull-down menu
        self.workerImaging.updateApplicationName()
        self.workerAstrometry.updateApplicationName()


class SplashScreen(PyQt5.QtCore.QObject):

    # Part from Maurizio D'Addona <mauritiusdadd@gmail.com> under license APL2.0
    # Ported from PYQT4 to PYQT5
    # Agreement for License (email from 04.07.2018):
    # Hi Michel,
    # sure, there is no problem for me. I'm glad you have found it useful.
    # Best regards,
    # Maurizio

    def __init__(self, pix, qapp=None):
        super().__init__()
        self._qapp = qapp
        self._pxm = pix
        self._qss = PyQt5.QtWidgets.QSplashScreen(self._pxm, (PyQt5.QtCore.Qt.WindowStaysOnTopHint | PyQt5.QtCore.Qt.X11BypassWindowManagerHint))

        self._msg = ''
        self._maxv = 100.0
        self._minv = 0.0
        self._cval = 0.0

        self._qss.__drawContents__ = self._qss.drawContents
        self._qss.drawContents = self._drawContents

        self._qss.show()

        self.processEvents()

    def close(self):
        self.update()
        self._qss.close()

    def setMaximum(self, val):
        self._maxv = val
        self.update()

    def setMinimum(self, val):
        self._minv = val
        self.update()

    def setValue(self, val):
        for i in numpy.arange(self._cval, val, self._maxv / 1000.0):
            self._cval = i
            self.update()

    def maximum(self):
        return self._maxv

    def minimum(self):
        return self._minv

    def value(self):
        return self._cval

    def message(self):
        return self._msg

    def showMessage(self, msg):
        self._msg = msg
        # self._qss.showMessage(msg,QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeft,QtCore.Qt.white)
        self.update()

    def update(self):
        self._qss.update()
        self.processEvents()

    def _drawContents(self, painter):
        # self._qss.__drawContents__(painter)

        view_port = painter.viewport()

        w = view_port.right()
        h = view_port.bottom()

        painter.setPen(PyQt5.QtGui.QColor(55, 55, 55, 255))
        painter.setBrush(PyQt5.QtGui.QColor(0, 0, 0, 255))
        painter.drawRect(10, h - 65, w - 20, 17)

        redlg = PyQt5.QtGui.QLinearGradient(0, h - 65, 0, h)
        redlg.setColorAt(0.5, PyQt5.QtGui.QColor(32, 144, 192))
        redlg.setColorAt(0, PyQt5.QtGui.QColor(8, 36, 48))

        painter.setPen(PyQt5.QtCore.Qt.NoPen)
        painter.setBrush(redlg)
        painter.drawRect(11, h - 63, (w - 21) * self._cval / self._maxv, 14)

        painter.setPen(PyQt5.QtCore.Qt.white)

        rect = PyQt5.QtCore.QRectF(10, h - 63, w - 20, 15)
        painter.drawText(rect, PyQt5.QtCore.Qt.AlignCenter, str(self._msg))

    def finish(self, qwid):
        self._qss.finish(qwid)

    def processEvents(self):
        if self._qapp is not None:
            self._qapp.processEvents()


class MyApp(PyQt5.QtWidgets.QApplication):

    PyQt5.QtWidgets.QApplication.setAttribute(PyQt5.QtCore.Qt.AA_EnableHighDpiScaling, True)

    def notify(self, obj, event):
        try:
            returnValue = PyQt5.QtWidgets.QApplication.notify(self, obj, event)
        except Exception as e:
            logging.error('-----------------------------------------')
            logging.error('Event: {0}'.format(event))
            logging.error('EventType: {0}'.format(event.type()))
            logging.error('Exception error in event loop: {0}'.format(e))
            logging.error('-----------------------------------------')
            returnValue = False
        finally:
            pass
        return returnValue


if __name__ == "__main__":
    import traceback
    import warnings
    import socket
    import PyQt5
    import build.build
    from PyQt5.QtCore import PYQT_VERSION_STR
    from PyQt5.QtCore import QT_VERSION_STR

    BUILD_NO = build.build.BUILD().BUILD_NO_WINDOW

    # setting except hook to get stack traces into the log files
    def except_hook(typeException, valueException, tbackException):
        result = traceback.format_exception(typeException, valueException, tbackException)
        logging.error('----------------------------------------------------------------------------------')
        logging.error('Logging an uncatched Exception')
        logging.error('----------------------------------------------------------------------------------')
        for i in range(0, len(result)):
            logging.error(result[i].replace('\n', ''))
        logging.error('----------------------------------------------------------------------------------')
        sys.__excepthook__(typeException, valueException, tbackException)

    # implement notify different to catch exception from event handler
    app = MyApp(sys.argv)
    splash_pix = PyQt5.QtGui.QPixmap(':/mw.ico')
    splash = SplashScreen(splash_pix, app)
    splash.showMessage('Start initialising')
    splash.setValue(20)

    warnings.filterwarnings("ignore")
    name = 'mount.{0}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
    handler = logging.handlers.RotatingFileHandler(name, backupCount=3)
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s.%(msecs)03d][%(levelname)7s][%(filename)22s][%(lineno)5s][%(funcName)20s][%(threadName)10s] - %(message)s',
                        handlers=[handler], datefmt='%Y-%m-%d %H:%M:%S')

    splash.showMessage('Checking work directories')
    splash.setValue(30)

    # population the working directory with necessary subdir
    if not os.path.isdir(os.getcwd() + '/analysedata'):
        os.makedirs(os.getcwd() + '/analysedata')
    if not os.path.isdir(os.getcwd() + '/images'):
        os.makedirs(os.getcwd() + '/images')
    if not os.path.isdir(os.getcwd() + '/config'):
        os.makedirs(os.getcwd() + '/config')

    splash.showMessage('Starting logging')
    splash.setValue(40)

    # start logging with basic system data for information
    hostSummary = socket.gethostbyname_ex(socket.gethostname())
    logging.info('----------------------------------------------------------------------------------')
    logging.info('')
    logging.info('MountWizzard ' + BUILD_NO + ' started !')
    logging.info('')
    logging.info('----------------------------------------------------------------------------------')
    logging.info('Platform : ' + platform.system())
    logging.info('Release  : ' + platform.release())
    logging.info('Version  : ' + platform.version())
    logging.info('Machine  : ' + platform.machine())
    logging.info('CPU      : ' + platform.processor())
    logging.info('Python   : ' + platform.python_version())
    logging.info('PyQt5    : ' + PYQT_VERSION_STR)
    logging.info('Qt       : ' + QT_VERSION_STR)
    host = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')][: 1]
    for i in range(0, len(host)):
        logging.info('IP addr. : ' + host[i])
    logging.info('Node     : ' + platform.node())
    logging.info('Hosts....: {0}'.format(hostSummary))
    logging.info('Workdir. : ' + os.getcwd())
    logging.info('----------------------------------------------------------------------------------')
    logging.info('')

    splash.showMessage('Checking work directories')
    splash.setValue(50)

    # checking if writable
    if not os.access(os.getcwd(), os.W_OK):
        logging.error('no write access to workdir')
    if not os.access(os.getcwd() + '/images', os.W_OK):
        logging.error('no write access to /images')
    if not os.access(os.getcwd() + '/config', os.W_OK):
        logging.error('no write access to /config')
    if not os.access(os.getcwd() + '/analysedata', os.W_OK):
        logging.error('no write access to /analysedata')

    splash.showMessage('Preparing application')
    splash.setValue(60)

    # and finally starting the application
    sys.excepthook = except_hook
    app.setWindowIcon(PyQt5.QtGui.QIcon('mw.ico'))
    mountApp = MountWizzardApp()

    splash.showMessage('Launching GUI')
    splash.setValue(80)

    mountApp.show()

    # end of splash screen
    splash.showMessage('Finishing loading')
    splash.setValue(100)

    splash.close()
    sys.exit(app.exec_())
