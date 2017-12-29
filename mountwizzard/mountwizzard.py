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
import os
import platform
import sys
import datetime
import json
import logging
import logging.handlers
import time
import math
import numpy
if platform.system() == 'Windows':
    from winreg import *
from queue import Queue
import PyQt5
import matplotlib
matplotlib.use('Qt5Agg')
from baseclasses import widget
from widgets import modelplotWindow
from widgets import imageWindow
from widgets import analyseWindow
from widgets import messageWindow
from gui import wizzard_main_ui
from modeling import modelingDispatcher
from mount import mountDispatcher
from relays import relays
from remote import remoteThread
if platform.system() == 'Windows':
    from dome import ascomDome
    from environment import ascomEnvironment
from indi import indi_client
from astrometry import transform
if platform.system() == 'Windows':
    from automation import upload
from wakeonlan import wol


class MountWizzardApp(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.config = {}
        # defining name of thread
        self.setObjectName("Main")
        # setting up communication queues for inter thread communication
        # commands to the mount
        self.mountCommandQueue = Queue()
        # commands to the dome
        self.domeCommandQueue = Queue()
        # command to the modeling thread
        self.modelCommandQueue = Queue()
        # messages back to main gui (message window)
        self.messageQueue = Queue()
        # commands / images to visualize in images window
        self.imageQueue = Queue()
        # INDI subsystem
        self.INDISendCommandQueue = Queue()
        self.INDIDataQueue = Queue()

        # initializing the gui from file generated from qt creator
        self.ui = wizzard_main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # special setups for gui including box for matplotlib. margins to 0
        self.initUI()
        self.checkPlatformDependableMenus()
        self.setWindowTitle('MountWizzard ' + BUILD_NO)
        # show icon in main gui and add some icons for push buttons
        # Windows opening
        self.widgetIcon(self.ui.btn_openMessageWindow, ':/note_accept.ico')
        self.widgetIcon(self.ui.btn_openAnalyseWindow, ':/chart.ico')
        self.widgetIcon(self.ui.btn_openImageWindow, ':/image.ico')
        self.widgetIcon(self.ui.btn_openModelingPlotWindow, ':/processes.ico')
        self.widgetIcon(self.ui.btn_saveConfigAs, ':/database_down.ico')
        self.widgetIcon(self.ui.btn_loadFrom, ':/database_up.ico')
        self.widgetIcon(self.ui.btn_saveConfig, ':/floppy_disc.ico')
        self.widgetIcon(self.ui.btn_saveConfigQuit, ':/eject.ico')
        self.widgetIcon(self.ui.btn_mountBoot, ':/computer_accept.ico')
        self.widgetIcon(self.ui.btn_mountShutdown, ':/computer_remove.ico')
        self.widgetIcon(self.ui.btn_runBaseModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_cancelModel1, ':/stop.ico')
        self.widgetIcon(self.ui.btn_runRefinementModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_cancelModel2, ':/stop.ico')
        self.widgetIcon(self.ui.btn_loadBasePoints, ':/floppy_disc_add.ico')
        self.widgetIcon(self.ui.btn_generateBasePoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_plateSolveSync, ':/calculator_accept.ico')
        self.widgetIcon(self.ui.btn_loadRefinementPoints, ':/floppy_disc_add.ico')
        self.widgetIcon(self.ui.btn_generateGridPoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_generateMaxPoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_generateNormalPoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_generateMinPoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_generateDSOPoints, ':/favorite_add.ico')
        self.widgetIcon(self.ui.btn_runTimeChangeModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_runHystereseModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_cancelAnalyseModel, ':/stop.ico')

        # the icon picture in gui
        pixmap = PyQt5.QtGui.QPixmap(':/mw.ico')
        pixmap = pixmap.scaled(99, 99)
        self.ui.mainicon.setPixmap(pixmap)
        pixmap = PyQt5.QtGui.QPixmap(':/azimuth1.png')
        self.ui.picAZ.setPixmap(pixmap)
        pixmap = PyQt5.QtGui.QPixmap(':/altitude1.png')
        self.ui.picALT.setPixmap(pixmap)

        # enable a matplotlib figure polar plot in main gui
        self.modelWidget = widget.IntegrateMatplotlib(self.ui.model)
        self.measure1Widget = widget.IntegrateMatplotlib(self.ui.measure1)
        self.measure2Widget = widget.IntegrateMatplotlib(self.ui.measure2)

        # instantiating all subclasses and connecting thread signals
        self.transform = transform.Transform(self)
        self.relays = relays.Relays(self)
        self.INDIworker = indi_client.INDIClient(self)
        self.INDIthread = PyQt5.QtCore.QThread()
        self.INDIthread.setObjectName("INDI")
        self.INDIworker.moveToThread(self.INDIthread)
        self.INDIthread.started.connect(self.INDIworker.run)
        self.INDIworker.status.connect(self.setINDIStatus)
        # threading for ascom environment data
        if platform.system() == 'Windows':
            self.workerAscomEnvironment = ascomEnvironment.AscomEnvironment(self)
            self.threadAscomEnvironment = PyQt5.QtCore.QThread()
            self.threadAscomEnvironment.setObjectName("Environ")
            self.workerAscomEnvironment.moveToThread(self.threadAscomEnvironment)
            # noinspection PyUnresolvedReferences
            self.threadAscomEnvironment.started.connect(self.workerAscomEnvironment.run)
            self.workerAscomEnvironment.finished.connect(self.workerAscomEnvironmentStop)
            self.workerAscomEnvironment.signalAscomEnvironmentConnected.connect(self.setEnvironmentStatus)
        # threading for ascom dome data
        if platform.system() == 'Windows':
            self.workerAscomDome = ascomDome.AscomDome(self)
            self.threadAscomDome = PyQt5.QtCore.QThread()
            self.threadAscomDome.setObjectName("Dome")
            self.workerAscomDome.moveToThread(self.threadAscomDome)
            # noinspection PyUnresolvedReferences
            self.threadAscomDome.started.connect(self.workerAscomDome.run)
            self.workerAscomDome.finished.connect(self.workerAscomDomeStop)
            self.workerAscomDome.signalAscomDomeConnected.connect(self.setDomeStatus)
        # threading for remote shutdown
        self.workerRemote = remoteThread.Remote(self)
        self.threadRemote = PyQt5.QtCore.QThread()
        self.threadRemote.setObjectName("Remote")
        self.workerRemote.moveToThread(self.threadRemote)
        # noinspection PyUnresolvedReferences
        self.threadRemote.started.connect(self.workerRemote.run)
        self.workerRemote.finished.connect(self.workerRemoteStop)
        # thread start will be done when enabled
        # self.threadRemote.start()
        self.workerRemote.signalRemoteShutdown.connect(self.saveConfigQuit)
        # threading for updater automation
        if platform.system() == 'Windows':
            self.workerUpload = upload.UpdaterAuto(self)
            self.threadUpload = PyQt5.QtCore.QThread()
            self.threadUpload.setObjectName("Upload")
            self.workerUpload.moveToThread(self.threadUpload)
            self.threadUpload.started.connect(self.workerUpload.run)
            self.workerUpload.finished.connect(self.workerUploadStop)
            self.threadUpload.start()
        self.workerModelingDispatcher = modelingDispatcher.ModelingDispatcher(self)
        self.threadModelingDispatcher = PyQt5.QtCore.QThread()
        self.threadModelingDispatcher.setObjectName("ModelingDispatcher")
        self.workerModelingDispatcher.moveToThread(self.threadModelingDispatcher)
        self.threadModelingDispatcher.started.connect(self.workerModelingDispatcher.run)
        self.workerModelingDispatcher.finished.connect(self.workerModelingDispatcherStop)
        self.workerModelingDispatcher.signalStatusCamera.connect(self.setStatusCamera)
        self.workerModelingDispatcher.signalStatusSolver.connect(self.setStatusSolver)
        # mount class
        self.workerMountDispatcher = mountDispatcher.MountDispatcher(self)
        self.threadMountDispatcher = PyQt5.QtCore.QThread()
        self.threadMountDispatcher.setObjectName("MountDispatcher")
        self.workerMountDispatcher.moveToThread(self.threadMountDispatcher)
        self.threadMountDispatcher.started.connect(self.workerMountDispatcher.run)
        self.workerMountDispatcher.finished.connect(self.workerMountDispatcherStop)
        self.workerMountDispatcher.signalMountConnectedFast.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedMedium.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedSlow.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedOnce.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedAlign.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedCommand.connect(self.setMountStatus)
        self.setMountStatus({})
        # gui for additional windows
        self.analyseWindow = analyseWindow.AnalyseWindow(self)
        self.modelWindow = modelplotWindow.ModelPlotWindow(self)
        self.imageWindow = imageWindow.ImagesWindow(self)
        self.messageWindow = messageWindow.MessageWindow(self)
        # loading config data - will be config.cfg
        self.loadConfigData()
        # init config starts necessary threads
        self.initConfig()
        # starting the threads
        self.threadModelingDispatcher.start()
        self.threadMountDispatcher.start()
        if platform.system() == 'Windows':
            self.checkASCOM()
        self.enableDisableRemoteAccess()
        self.enableDisableINDI()
        # map all the button to functions for gui
        self.mappingFunctions()
        # print('main app', PyQt5.QtCore.QObject.thread(self), int(PyQt5.QtCore.QThread.currentThreadId()))
        # starting loop for cyclic data to gui from threads
        self.counter = 0
        self.mainLoop()

    def workerAscomEnvironmentStop(self):
        self.threadAscomEnvironment.quit()
        self.threadAscomEnvironment.wait()

    def workerAscomEnvironmentSetup(self):
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerAscomEnvironment.isRunning:
            self.workerAscomEnvironment.stop()
        self.workerAscomEnvironment.setupDriver()
        self.ui.le_ascomEnvironmentDriverName.setText(self.workerAscomEnvironment.driverName)
        self.threadAscomEnvironment.start()

    def workerAscomDomeStop(self):
        self.threadAscomDome.quit()
        self.threadAscomDome.wait()

    def workerAscomDomeSetup(self):
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerAscomDome.isRunning:
            self.workerAscomDome.stop()
        self.workerAscomDome.setupDriver()
        self.ui.le_ascomDomeDriverName.setText(self.workerAscomDome.driverName)
        self.threadAscomDome.start()

    def setDomeStatus(self, status):
        if status == 0:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')
        elif status == 1:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: red;color: black;}')
        elif status == 2:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: yellow;color: black;}')
        elif status == 3:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: green;color: black;}')

    def workerRemoteStop(self):
        self.threadRemote.quit()
        self.threadRemote.wait()

    def workerUploadStop(self):
        self.threadUpload.quit()
        self.threadUpload.wait()

    def workerModelingDispatcherStop(self):
        self.threadModelingDispatcher.quit()
        self.threadModelingDispatcher.wait()

    def workerMountDispatcherStop(self):
        self.threadMountDispatcher.quit()
        self.threadMountDispatcher.wait()

    def enableDisableRemoteAccess(self):
        if self.ui.checkEnableRemoteAccess.isChecked():
            self.messageQueue.put('Remote Access enabled\n')
            self.threadRemote.start()
            # waiting to tcp server to start otherwise no setup for remote
            while not self.workerRemote.tcpServer:
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
        else:
            self.messageQueue.put('Remote Access disabled\n')
            if self.workerRemote.isRunning:
                self.workerRemote.stop()

    def mappingFunctions(self):
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
        self.ui.le_parkPos1Text.textChanged.connect(lambda: self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text()))
        self.ui.le_parkPos2Text.textChanged.connect(lambda: self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text()))
        self.ui.le_parkPos3Text.textChanged.connect(lambda: self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text()))
        self.ui.le_parkPos4Text.textChanged.connect(lambda: self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text()))
        self.ui.le_parkPos5Text.textChanged.connect(lambda: self.ui.btn_mountPos5.setText(self.ui.le_parkPos5Text.text()))
        self.ui.le_parkPos6Text.textChanged.connect(lambda: self.ui.btn_mountPos6.setText(self.ui.le_parkPos6Text.text()))
        self.ui.le_horizonLimitHigh.textChanged.connect(self.setHorizonLimitHigh)
        self.ui.le_horizonLimitLow.textChanged.connect(self.setHorizonLimitLow)
        self.ui.le_slewRate.textChanged.connect(self.setSlewRate)
        self.ui.btn_setDualTracking.clicked.connect(self.setDualTracking)
        self.ui.btn_setUnattendedFlip.clicked.connect(self.setUnattendedFlip)
        if platform.system() == 'Windows':
            self.ui.btn_setupDomeDriver.clicked.connect(self.workerAscomDomeSetup)
            self.ui.btn_setupAscomEnvironmentDriver.clicked.connect(self.workerAscomEnvironmentSetup)
        # setting lambda make the signal / slot a dedicated call. So if you press cancel without lambda, the thread affinity is to modeling,
        # because the signal is passed to the event queue of modeling and handled there. If you press cancel with lambda, the thread
        # affinity is in main, because you don't transfer it to the other event queue, but you leave it to gui event queue.
        self.ui.btn_cancelModel1.clicked.connect(lambda: self.workerModelingDispatcher.cancelModeling())
        self.ui.btn_cancelModel2.clicked.connect(lambda: self.workerModelingDispatcher.cancelModeling())
        self.ui.btn_cancelAnalyseModel.clicked.connect(lambda: self.workerModelingDispatcher.cancelAnalyseModeling())
        self.ui.btn_cancelRunTargetRMSAlignment.clicked.connect(lambda: self.workerMountDispatcher.cancelRunTargetRMSFunction())
        self.ui.btn_loadHorizonMask.clicked.connect(self.selectHorizonPointsFileName)
        self.ui.btn_loadModelPoints.clicked.connect(self.selectModelPointsFileName)
        self.ui.checkUseMinimumHorizonLine.stateChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.checkUseFileHorizonLine.stateChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.altitudeMinimumHorizon.valueChanged.connect(self.modelWindow.selectHorizonPointsMode)
        self.ui.btn_loadAnalyseData.clicked.connect(self.selectAnalyseFileName)
        self.ui.btn_openAnalyseWindow.clicked.connect(self.analyseWindow.showWindow)
        self.ui.btn_openMessageWindow.clicked.connect(self.messageWindow.showWindow)
        self.ui.btn_openModelingPlotWindow.clicked.connect(self.modelWindow.showWindow)
        self.ui.btn_openImageWindow.clicked.connect(self.imageWindow.showWindow)
        self.ui.checkEnableRemoteAccess.stateChanged.connect(self.enableDisableRemoteAccess)
        self.ui.checkEnableINDI.stateChanged.connect(self.enableDisableINDI)
        # self.workerMountDispatcher.signalMountShowAlignmentModel.connect(lambda: self.showModelErrorPolar(self.modelWidget))
        self.workerMountDispatcher.signalMountShowAlignmentModel.connect(lambda: self.test(self.modelWidget))

    def enableDisableINDI(self):
        # todo: enable INDI Subsystem as soon as INDI is tested
        if self.ui.checkEnableINDI.isChecked():
            self.INDIthread.start()
        else:
            self.INDIworker.stop()
            self.INDIthread.quit()
            self.INDIthread.wait()

    def mountBoot(self):
        self.ui.btn_mountBoot.setProperty('running', PyQt5.QtCore.QVariant(True))
        self.ui.btn_mountBoot.style().unpolish(self.ui.btn_mountBoot)
        self.ui.btn_mountBoot.style().polish(self.ui.btn_mountBoot)
        PyQt5.QtWidgets.QApplication.processEvents()
        wol.send_magic_packet(self.ui.le_mountMAC.text().strip())
        time.sleep(1)
        self.messageQueue.put('Send WOL and boot mount\n')
        self.logger.debug('Send WOL packet and boot Mount')
        self.ui.btn_mountBoot.setProperty('running', PyQt5.QtCore.QVariant(False))
        self.ui.btn_mountBoot.style().unpolish(self.ui.btn_mountBoot)
        self.ui.btn_mountBoot.style().polish(self.ui.btn_mountBoot)

    def test(self, widget):
        self.showModelErrorPolar(widget)
        self.showModelErrorPolar(self.measure1Widget)
        self.showModelErrorPolar(self.measure2Widget)

    def showModelErrorPolar(self, widget):
        widget.fig.clf()
        widget.axes = widget.fig.add_subplot(1, 1, 1, polar=True)
        widget.axes.grid(True, color='gray')
        widget.fig.subplots_adjust(left=0.075, right=0.975, bottom=0.075, top=0.925)
        widget.axes.set_facecolor((32/256, 32/256, 32/256))
        widget.axes.tick_params(axis='x', colors='white', labelsize=12)
        widget.axes.tick_params(axis='y', colors='white', labelsize=12)
        widget.axes.set_theta_zero_location('N')
        widget.axes.set_theta_direction(-1)
        widget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        widget.axes.set_yticklabels(yLabel, color='white')
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

    def checkASCOM(self):
        appAvailable, appName, appInstallPath = self.checkRegistrationKeys('ASCOM Platform')
        if appAvailable:
            self.messageQueue.put('Found: {0}\n'.format(appName))
            self.logger.info('Name: {0}, Path: {1}'.format(appName, appInstallPath))
        else:
            self.logger.warning('Application ASCOM not found on computer')

    def checkRegistrationKeys(self, appSearchName):
        if platform.machine().endswith('64'):
            regPath = 'SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'                                # regpath for 64 bit windows
        else:
            regPath = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'                                             # regpath for 32 bit windows
        appInstallPath = ''
        appInstalled = False
        appName = ''
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, regPath)                                                                      # open registry
            for i in range(0, QueryInfoKey(key)[0]):                                                                        # run through all registry application
                name = EnumKey(key, i)                                                                                      # get registry names of applications
                subkey = OpenKey(key, name)                                                                                 # open subkeys of applications
                for j in range(0, QueryInfoKey(subkey)[1]):                                                                 # run through all subkeys
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
                    CloseKey(subkey)                                                                                        # closing the subkey for later usage
            CloseKey(key)                                                                                                   # closing main key for later usage
            if not appInstalled:
                appInstallPath = ''
                appName = ''
        except Exception as e:
            self.logger.debug('Name: {0}, Path: {1}, error: {2}'.format(appName, appInstallPath, e))
        finally:
            return appInstalled, appName, appInstallPath

    def checkPlatformDependableMenus(self):
        if platform.system() != 'Windows':
            # you have to remove the higher number first to keep the ordering number (otherwise everything is already shifted)
            self.ui.settingsTabWidget.removeTab(3)
            self.ui.settingsTabWidget.removeTab(1)

    def initConfig(self):
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
            if 'ModelPointsFileName' in self.config:
                self.ui.le_modelPointsFileName.setText(self.config['ModelPointsFileName'])
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
            if 'CheckUseBlindSolve' in self.config:
                self.ui.checkUseBlindSolve.setChecked(self.config['CheckUseBlindSolve'])
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
            if 'CheckClearModelFirst' in self.config:
                self.ui.checkClearModelFirst.setChecked(self.config['CheckClearModelFirst'])
            if 'AltitudeBase' in self.config:
                self.ui.altitudeBase.setValue(self.config['AltitudeBase'])
            if 'AzimuthBase' in self.config:
                self.ui.azimuthBase.setValue(self.config['AzimuthBase'])
            if 'NumberGridPointsCol' in self.config:
                self.ui.numberGridPointsCol.setValue(self.config['NumberGridPointsCol'])
            if 'NumberGridPointsRow' in self.config:
                self.ui.numberGridPointsRow.setValue(self.config['NumberGridPointsRow'])
            if 'AltitudeMin' in self.config:
                self.ui.altitudeMin.setValue(self.config['AltitudeMin'])
            if 'AltitudeMax' in self.config:
                self.ui.altitudeMax.setValue(self.config['AltitudeMax'])
            if 'NumberPointsDSO' in self.config:
                self.ui.numberPointsDSO.setValue(self.config['NumberPointsDSO'])
            if 'NumberHoursDSO' in self.config:
                self.ui.numberHoursDSO.setValue(self.config['NumberHoursDSO'])
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
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

        # initialize all configs in submodules, if necessary stop thread and restart thread for loading the desired driver
        self.workerMountDispatcher.initConfig()
        self.workerModelingDispatcher.initConfig()
        if platform.system() == 'Windows':
            self.workerAscomEnvironment.initConfig()
            if self.workerAscomEnvironment.isRunning:
                self.workerAscomEnvironment.stop()
            self.threadAscomEnvironment.start()
            self.workerAscomDome.initConfig()
            if self.workerAscomDome.isRunning:
                self.workerAscomDome.stop()
            self.threadAscomDome.start()
            self.workerUpload.initConfig()
        self.modelWindow.initConfig()
        self.imageWindow.initConfig()
        self.analyseWindow.initConfig()
        self.messageWindow.initConfig()
        self.relays.initConfig()
        self.INDIworker.initConfig()

        # make windows visible, if they were on the desktop depending on their show status
        if self.modelWindow.showStatus:
            self.modelWindow.showWindow()
            self.modelWindow.drawHemisphere()
        else:
            self.modelWindow.setVisible(False)
        if self.imageWindow.showStatus:
            self.imageWindow.showWindow()
        else:
            self.imageWindow.setVisible(False)
        if self.analyseWindow.showStatus:
            self.analyseWindow.showWindow()
        else:
            self.analyseWindow.setVisible(False)
        if self.messageWindow.showStatus:
            self.messageWindow.showWindow()
        else:
            self.messageWindow.setVisible(False)

    def storeConfig(self):
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
        self.config['ModelPointsFileName'] = self.ui.le_modelPointsFileName.text()
        self.config['CameraBin'] = self.ui.cameraBin.value()
        self.config['CameraExposure'] = self.ui.cameraExposure.value()
        self.config['CheckFastDownload'] = self.ui.checkFastDownload.isChecked()
        self.config['ISOSetting'] = self.ui.isoSetting.value()
        self.config['SettlingTime'] = self.ui.settlingTime.value()
        self.config['CheckUseBlindSolve'] = self.ui.checkUseBlindSolve.isChecked()
        self.config['TargetRMS'] = self.ui.targetRMS.value()
        self.config['PixelSize'] = self.ui.pixelSize.value()
        self.config['FocalLength'] = self.ui.focalLength.value()
        self.config['ScaleSubframe'] = self.ui.scaleSubframe.value()
        self.config['CheckDoSubframe'] = self.ui.checkDoSubframe.isChecked()
        self.config['CheckKeepImages'] = self.ui.checkKeepImages.isChecked()
        self.config['AltitudeBase'] = self.ui.altitudeBase.value()
        self.config['AzimuthBase'] = self.ui.azimuthBase.value()
        self.config['NumberGridPointsRow'] = self.ui.numberGridPointsRow.value()
        self.config['NumberGridPointsCol'] = self.ui.numberGridPointsCol.value()
        self.config['AltitudeMin'] = self.ui.altitudeMin.value()
        self.config['AltitudeMax'] = self.ui.altitudeMax.value()
        self.config['NumberPointsDSO'] = self.ui.numberPointsDSO.value()
        self.config['NumberHoursDSO'] = self.ui.numberHoursDSO.value()
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
        self.config['CheckClearModelFirst'] = self.ui.checkClearModelFirst.isChecked()
        self.config['ConfigName'] = self.ui.le_configName.text()
        self.config['MainTabPosition'] = self.ui.mainTabWidget.currentIndex()
        self.config['SettingTabPosition'] = self.ui.settingsTabWidget.currentIndex()

        # store config in all submodules
        self.workerMountDispatcher.storeConfig()
        self.workerModelingDispatcher.storeConfig()
        if platform.system() == 'Windows':
            self.workerAscomEnvironment.storeConfig()
            self.workerAscomDome.storeConfig()
            self.workerUpload.storeConfig()
        self.modelWindow.storeConfig()
        self.imageWindow.storeConfig()
        self.analyseWindow.storeConfig()
        self.messageWindow.storeConfig()
        self.relays.storeConfig()
        self.INDIworker.storeConfig()

    def loadConfigData(self):
        try:
            with open('config/config.cfg', 'r') as data_file:
                self.config = json.load(data_file)
        except Exception as e:
            self.messageQueue.put('#BRConfig.cfg could not be loaded !\n')
            self.logger.error('Item in config.cfg not loaded error:{0}'.format(e))
            self.config = {}

    def saveConfig(self):
        filepath = os.getcwd() + '\\config\\' + self.ui.le_configName.text()
        self.saveConfigData(filepath)

    def saveConfigQuit(self):
        filepath = os.getcwd() + '\\config\\' + self.ui.le_configName.text()
        self.saveConfigData(filepath)
        # noinspection PyArgumentList
        PyQt5.QtCore.QCoreApplication.instance().quit()

    def saveConfigData(self, filepath=''):
        self.storeConfig()
        try:
            if not os.path.isdir(os.getcwd() + '/config'):
                os.makedirs(os.getcwd() + '/config')
            with open('config/config.cfg', 'w') as outfile:
                json.dump(self.config, outfile)
            outfile.close()
            with open(filepath, 'w') as outfile:
                json.dump(self.config, outfile)
            outfile.close()
            self.messageQueue.put('Configuration saved.\n')
        except Exception as e:
            self.messageQueue.put('#BRConfig.cfg could not be saved !\n')
            self.logger.error('Item in config.cfg not saved error {0}'.format(e))
            return

    def loadConfigDataFrom(self):
        value, _ = self.selectFile(self, 'Open config file', '/config', 'Config files (*.cfg)', True)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            try:
                with open(value, 'r') as data_file:
                    self.config = json.load(data_file)
                    self.initConfig()
            except Exception as e:
                self.messageQueue.put('#BRConfig.cfg could not be loaded !\n')
                self.logger.error('Item in config.cfg not loaded error:{0}'.format(e))
                self.config = {}
        else:
            self.logger.warning('no config file selected')

    def saveConfigAs(self):
        value, _ = self.selectFile(self, 'Save config file', '/config', 'Config files (*.cfg)', False)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            self.saveConfigData(value)
        else:
            self.logger.warning('No config file selected')

    def selectModelPointsFileName(self):
        value, _ = self.selectFile(self, 'Open model points file', '/config', 'Model points files (*.txt)', True)
        if value != '':
            self.ui.le_modelPointsFileName.setText(os.path.basename(value))
        else:
            self.logger.warning('No file selected')

    def selectAnalyseFileName(self):
        value, _ = self.selectFile(self, 'Open analyse file', '/analyse', 'Analyse files (*.dat)', True)
        if value != '':
            self.ui.le_analyseFileName.setText(os.path.basename(value))
            self.analyseWindow.showWindow()
        else:
            self.logger.warning('no file selected')

    def selectHorizonPointsFileName(self):
        value, _ = self.selectFile(self, 'Open horizon mask file', '/config', 'Horizon mask files (*.txt)', True)
        if value != '':
            self.ui.le_horizonPointsFileName.setText(os.path.basename(value))
            self.modelWindow.selectHorizonPointsMode()
            self.modelWindow.drawHemisphere()

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
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos1.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos1.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def mountPosition2(self):
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos2.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos2.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def mountPosition3(self):
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos3.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos3.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def mountPosition4(self):
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos4.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos4.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def mountPosition5(self):
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos5.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos5.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def mountPosition6(self):
        self.mountCommandQueue.put(':PO#')                                                                                         # unpark first
        self.mountCommandQueue.put(':Sz{0:03d}*00#'.format(int(self.ui.le_azParkPos6.text())))                                     # set az
        self.mountCommandQueue.put(':Sa+{0:02d}*00#'.format(int(self.ui.le_altParkPos6.text())))                                   # set alt
        self.mountCommandQueue.put(':MA#')                                                                                         # start Slewing

    def setEnvironmentStatus(self, status):
        if status == 0:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')
        elif status == 1:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif status == 2:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
        elif status == 3:
            self.ui.btn_environmentConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')

    def fillEnvironmentData(self):
        if platform.system() != 'Windows':
            return
        for valueName in self.workerAscomEnvironment.data:
            if valueName == 'DewPoint':
                self.ui.le_dewPoint.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'Temperature':
                self.ui.le_temperature.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'Humidity':
                self.ui.le_humidity.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'Pressure':
                self.ui.le_pressure.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'CloudCover':
                self.ui.le_cloudCover.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'RainRate':
                self.ui.le_rainRate.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'WindSpeed':
                self.ui.le_windSpeed.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'WindDirection':
                self.ui.le_windDirection.setText('{0:4.1f}'.format(self.workerAscomEnvironment.data[valueName]))
            elif valueName == 'SQR':
                self.ui.le_SQR.setText('{0:4.2f}'.format(self.workerAscomEnvironment.data[valueName]))

    @PyQt5.QtCore.Slot(int)
    def setINDIStatus(self, status):
        if status == 0:
            self.ui.le_INDIStatus.setText('UnconnectedState')
        elif status == 1:
            self.ui.le_INDIStatus.setText('HostLookupState')
        elif status == 2:
            self.ui.le_INDIStatus.setText('ConnectingState')
        elif status == 3:
            self.ui.le_INDIStatus.setText('ConnectedState')
        elif status == 6:
            self.ui.le_INDIStatus.setText('ClosingState')
        else:
            self.ui.le_INDIStatus.setText('Error')

    @PyQt5.QtCore.Slot(dict)
    def fillINDIData(self, data):
        if data['Name'] == 'Telescope':
            self.ui.le_INDITelescope.setText(data['value'])
        elif data['Name'] == 'CCD':
            self.ui.le_INDICCD.setText(data['value'])
        elif data['Name'] == 'WEATHER':
            self.ui.le_INDIWeather.setText(data['value'])
        elif data['Name'] == 'CameraStatus':
            self.imageWindow.ui.le_INDICameraStatus.setText(data['value'])

    @PyQt5.QtCore.Slot(dict)
    def setMountStatus(self, status):
        for key in status:
            self.workerMountDispatcher.mountStatus[key] = status[key]
        stat = 0
        for key in self.workerMountDispatcher.mountStatus:
            if self.workerMountDispatcher.mountStatus[key]:
                stat += 1
        if stat == 0:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif stat == 6:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: green; color:black;}')
        else:
            self.ui.btn_driverMountConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')

    @PyQt5.QtCore.Slot(dict)
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
            if valueName == 'MeridianLimitTrack':
                self.ui.le_meridianLimitTrack.setText(str(self.workerMountDispatcher.data[valueName]))
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

    @PyQt5.QtCore.Slot(int)
    def setStatusCamera(self, status):
        if status == 3:
            self.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')
        elif status == 2:
            self.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
        elif status == 1:
            self.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        else:
            self.ui.btn_cameraConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')

    @PyQt5.QtCore.Slot(int)
    def setStatusSolver(self, status):
        if status == 3:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: green;color: black;}')
        elif status == 2:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: yellow;color: black;}')
        elif status == 1:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: red;color: black;}')
        else:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')

    def mainLoop(self):
        self.counter += 5
        # self.workerAscomDome.signalDomePointer.emit(self.counter)
        # self.workerMountDispatcher.signalMountAzAltPointer.emit(self.counter, 45)
        if self.counter > 370:
            self.counter = -10
        self.fillMountData()
        self.fillEnvironmentData()
        while not self.INDIDataQueue.empty():
            data = self.INDIDataQueue.get()
            self.fillINDIData(data)
        while not self.messageQueue.empty():
            text = self.messageQueue.get()
            if text == 'delete':
                self.messageWindow.ui.messages.clear()
            elif text.startswith('status'):
                self.ui.le_modelingStatus.setText(text[6:])
            elif text.startswith('percent'):
                self.ui.bar_modelingStatusPercent.setValue(int(1000 * float(text[7:])))
            elif text.startswith('timeleft'):
                self.ui.le_modelingStatusTime.setText(text[8:])
            elif text.startswith('#BW'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_WHITE)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(text[3:])
            elif text.startswith('#BG'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_GREEN)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(text[3:])
            elif text.startswith('#BY'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_YELLOW)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(text[3:])
            elif text.startswith('#BR'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ORANGE)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(text[3:])
            elif text.startswith('#BO'):
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ORANGE)
                # self.messageWindow.ui.messages.setFontWeight(QFont.Bold)
                self.messageWindow.ui.messages.insertPlainText(text[3:])
            else:
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ASTRO)
                self.messageWindow.ui.messages.setFontWeight(PyQt5.QtGui.QFont.Normal)
                self.messageWindow.ui.messages.insertPlainText(text)
            self.messageWindow.ui.messages.moveCursor(PyQt5.QtGui.QTextCursor.End)
        while not self.imageQueue.empty():
            filename = self.imageQueue.get()
            if self.imageWindow.showStatus:
                self.imageWindow.showFitsImage(filename)
        PyQt5.QtCore.QTimer.singleShot(100, self.mainLoop)


if __name__ == "__main__":
    import traceback
    import warnings

    # setting except hook to get stack traces into the log files
    def except_hook(typeException, valueException, tbackException):                                                         # manage unhandled exception here
        logging.error(traceback.format_exception(typeException, valueException, tbackException))
        sys.__excepthook__(typeException, valueException, tbackException)                                                   # then call the default handler

    BUILD_NO = '3.0.0 beta'

    warnings.filterwarnings("ignore")
    name = 'mount.{0}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
    handler = logging.handlers.RotatingFileHandler(name, backupCount=3)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s [%(levelname)7s][%(filename)30s][%(lineno)5s][%(funcName)20s][%(threadName)10s] - %(message)s',
                        handlers=[handler], datefmt='%Y-%m-%d %H:%M:%S')

    # population the working directory with necessary subdir
    if not os.path.isdir(os.getcwd() + '/analysedata'):
        os.makedirs(os.getcwd() + '/analysedata')
    if not os.path.isdir(os.getcwd() + '/images'):
        os.makedirs(os.getcwd() + '/images')
    if not os.path.isdir(os.getcwd() + '/config'):
        os.makedirs(os.getcwd() + '/config')

    # start logging with basic system data
    logging.info('-----------------------------------------')
    logging.info('MountWizzard v ' + BUILD_NO + ' started !')
    logging.info('-----------------------------------------')
    logging.info('Platform: ' + platform.system())
    logging.info('Release: ' + platform.release())
    logging.info('Version: ' + platform.version())
    logging.info('Machine: ' + platform.machine())

    # generating the necessary folders
    logging.info('working directory: {0}'.format(os.getcwd()))
    if not os.access(os.getcwd(), os.W_OK):
        logging.error('no write access to workdir')
    if not os.access(os.getcwd() + '/images', os.W_OK):
        logging.error('no write access to /images')
    if not os.access(os.getcwd() + '/config', os.W_OK):
        logging.error('no write access to /config')
    if not os.access(os.getcwd() + '/analysedata', os.W_OK):
        logging.error('no write access to /analysedata')

    # and finally starting the application
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    sys.excepthook = except_hook
    app.setWindowIcon(PyQt5.QtGui.QIcon('mw.ico'))
    mountApp = MountWizzardApp()
    logging.info('Screensize: {0} x {1}'.format(mountApp.screenSizeX, mountApp.screenSizeY))
    mountApp.show()

    sys.exit(app.exec_())
