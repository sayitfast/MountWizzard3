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
from widgets import hemisphereWindow
from widgets import imageWindow
from widgets import analyseWindow
from widgets import messageWindow
from gui import wizzard_main_ui
from modeling import modelingDispatcher
from mount import mountDispatcher
from relays import relays
from remote import remoteThread
from dome import dome
from environment import environment
from indi import indi_client
from astrometry import transform
from imaging import imaging
if platform.system() == 'Windows':
    from automation import upload
from wakeonlan import send_magic_packet


class MountWizzardApp(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.config = {}
        self.setObjectName("Main")
        # commands to the mount
        self.mountCommandQueue = Queue()
        self.domeCommandQueue = Queue()
        self.modelCommandQueue = Queue()
        self.messageQueue = Queue()
        self.imageQueue = Queue()
        self.INDICommandQueue = Queue()
        self.INDIStatusQueue = Queue()
        # initializing the gui from file generated from qt creator
        self.ui = wizzard_main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.initUI()
        self.checkPlatformDependableMenus()
        self.setWindowTitle('MountWizzard ' + BUILD_NO)
        self.messageQueue.put('#BWMountWizzard v {0} started \n'.format(BUILD_NO))
        self.messageQueue.put('#BWPlatform : {}\n'.format(platform.system()))
        self.messageQueue.put('#BWRelease  : {}\n'.format(platform.release()))
        self.messageQueue.put('#BWMachine  : {}\n\n'.format(platform.machine()))
        # show icon in main gui and add some icons for push buttons
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
        self.widgetIcon(self.ui.btn_runInitialModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_cancelModel1, ':/stop.ico')
        self.widgetIcon(self.ui.btn_runFullModel, ':/play.ico')
        self.widgetIcon(self.ui.btn_cancelModel2, ':/stop.ico')
        self.widgetIcon(self.ui.btn_generateInitialPoints, ':/process_add.ico')
        self.widgetIcon(self.ui.btn_plateSolveSync, ':/calculator_accept.ico')
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
        # instantiating all subclasses and connecting thread signals
        self.transform = transform.Transform(self)
        self.relays = relays.Relays(self)
        # runtime threads
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
        self.workerRemote = remoteThread.Remote(self, self.threadRemote)
        self.threadRemote.setObjectName("Remote")
        self.workerRemote.moveToThread(self.threadRemote)
        self.threadRemote.started.connect(self.workerRemote.run)
        self.workerRemote.signalRemoteShutdown.connect(self.saveConfigQuit)
        # threading for imaging apps
        self.threadImaging = PyQt5.QtCore.QThread()
        self.workerImaging = imaging.ImagingApps(self, self.threadImaging)
        self.threadImaging.setObjectName("Imaging")
        self.workerImaging.moveToThread(self.threadImaging)
        self.threadImaging.started.connect(self.workerImaging.run)
        self.threadImaging.start()
        # threading for astrometry apps
        #self.threadAstrometry = PyQt5.QtCore.QThread()
        #self.workerAstrometry = remoteThread.Remote(self, self.threadAstrometry)
        #self.threadAstrometry.setObjectName("Astrometry")
        #self.workerAstrometry.moveToThread(self.threadAstrometry)
        #self.threadAstrometry.started.connect(self.workerAstrometry.run)
        # self.threadAstrometry.start()
        # threading for updater automation
        if platform.system() == 'Windows':
            self.threadUpload = PyQt5.QtCore.QThread()
            self.workerUpload = upload.UpdaterAuto(self, self.threadUpload)
            self.threadUpload.setObjectName("Upload")
            self.workerUpload.moveToThread(self.threadUpload)
            self.threadUpload.started.connect(self.workerUpload.run)
            self.threadUpload.start()
        self.threadModelingDispatcher = PyQt5.QtCore.QThread()
        self.workerModelingDispatcher = modelingDispatcher.ModelingDispatcher(self, self.threadModelingDispatcher)
        self.threadModelingDispatcher.setObjectName("ModelingDispatcher")
        self.workerModelingDispatcher.moveToThread(self.threadModelingDispatcher)
        self.threadModelingDispatcher.started.connect(self.workerModelingDispatcher.run)
        # mount class
        self.threadMountDispatcher = PyQt5.QtCore.QThread()
        self.workerMountDispatcher = mountDispatcher.MountDispatcher(self, self.threadMountDispatcher)
        self.threadMountDispatcher.setObjectName("MountDispatcher")
        self.workerMountDispatcher.moveToThread(self.threadMountDispatcher)
        self.threadMountDispatcher.started.connect(self.workerMountDispatcher.run)
        self.workerMountDispatcher.signalMountConnectedFast.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedMedium.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedSlow.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedOnce.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedAlign.connect(self.setMountStatus)
        self.workerMountDispatcher.signalMountConnectedCommand.connect(self.setMountStatus)
        self.setMountStatus({})
        # gui for additional windows
        self.analyseWindow = analyseWindow.AnalyseWindow(self)
        self.hemisphereWindow = hemisphereWindow.HemisphereWindow(self)
        self.imageWindow = imageWindow.ImagesWindow(self)
        self.messageWindow = messageWindow.MessageWindow(self)
        # loading config data - will be config.cfg
        self.loadConfigData()
        # init config starts necessary threads
        self.initConfig()
        # starting the threads
        self.threadModelingDispatcher.start()
        self.threadMountDispatcher.start()
        self.checkASCOM()
        # map all the button to functions for gui
        self.mappingFunctions()
        # starting loop for cyclic data to gui from threads
        self.mainLoop()
        # print('Thread ID:',int(PyQt5.QtCore.QThread.currentThreadId()))

    def workerAscomEnvironmentSetup(self):
        if platform.system() != 'Windows':
            return
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        self.workerEnvironment.setupDriver()
        self.ui.le_ascomEnvironmentDriverName.setText(self.workerEnvironment.ascomDriverName)
        self.threadEnvironment.start()

    def workerAscomDomeSetup(self):
        if platform.system() != 'Windows':
            return
        # first stopping the thread for environment, than setting up, than starting the thread
        if self.workerDome.isRunning:
            self.workerDome.stop()
        self.workerDome.setupDriver()
        self.ui.le_ascomDomeDriverName.setText(self.workerDome.ascomDriverName)
        self.threadDome.start()

    def setDomeStatus(self, status):
        if status == 0:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')
        elif status == 1:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: red;color: black;}')
        elif status == 2:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: yellow;color: black;}')
        elif status == 3:
            self.ui.btn_domeConnected.setStyleSheet('QPushButton {background-color: green;color: black;}')

    def workerModelingDispatcherStop(self):
        self.threadModelingDispatcher.quit()
        self.threadModelingDispatcher.wait()

    def workerMountDispatcherStop(self):
        self.threadMountDispatcher.quit()
        self.threadMountDispatcher.wait()

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
        self.ui.btn_setupDomeDriver.clicked.connect(self.workerAscomDomeSetup)
        self.ui.btn_setupAscomEnvironmentDriver.clicked.connect(self.workerAscomEnvironmentSetup)
        # setting lambda make the signal / slot a dedicated call. So if you press cancel without lambda, the thread affinity is to modeling,
        # because the signal is passed to the event queue of modeling and handled there. If you press cancel with lambda, the thread
        # affinity is in main, because you don't transfer it to the other event queue, but you leave it to gui event queue.
        self.ui.btn_cancelModel1.clicked.connect(lambda: self.workerModelingDispatcher.cancelModeling())
        self.ui.btn_cancelModel2.clicked.connect(lambda: self.workerModelingDispatcher.cancelModeling())
        self.ui.btn_cancelAnalyseModel.clicked.connect(lambda: self.workerModelingDispatcher.cancelAnalyseModeling())
        self.ui.btn_cancelRunTargetRMSAlignment.clicked.connect(lambda: self.workerMountDispatcher.cancelRunTargetRMSFunction())
        self.ui.checkUseMinimumHorizonLine.stateChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.checkUseFileHorizonLine.stateChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.altitudeMinimumHorizon.valueChanged.connect(self.hemisphereWindow.selectHorizonPointsMode)
        self.ui.btn_loadAnalyseData.clicked.connect(self.selectAnalyseFileName)
        self.ui.btn_openAnalyseWindow.clicked.connect(self.analyseWindow.showWindow)
        self.ui.btn_openMessageWindow.clicked.connect(self.messageWindow.showWindow)
        self.ui.btn_openModelingPlotWindow.clicked.connect(self.hemisphereWindow.showWindow)
        self.ui.btn_openImageWindow.clicked.connect(self.imageWindow.showWindow)
        self.workerMountDispatcher.signalMountShowAlignmentModel.connect(lambda: self.showModelErrorPolar(self.modelWidget))
        self.workerINDI.statusCCD.connect(self.setINDIStatusCCD)
        self.workerINDI.statusEnvironment.connect(self.setINDIStatusEnvironment)
        self.workerINDI.statusDome.connect(self.setINDIStatusDome)
        self.workerDome.domeStatusText.connect(self.setDomeStatusText)

    def mountBoot(self):
        import socket
        host = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')][: 1]
        if len(host) > 1:
            self.messageQueue.put('Cannot send WOL because there are multiple computer IP addresses configured\n')
            self.logger.debug('Cannot send WOL because there are multiple computer IP addresses configured')
            return
        addressComputer = host[0].split('.')
        addressMount = self.ui.le_mountIP.text().split('.')
        if addressComputer[0] != addressMount[0] or addressComputer[1] != addressMount[1] or addressComputer[2] != addressMount[2]:
            self.messageQueue.put('Cannot send WOL because computer and mount are not in the same subnet\n')
            self.logger.debug('Cannot send WOL because computer and mount are not in the same subnet')
            return
        self.ui.btn_mountBoot.setProperty('running', PyQt5.QtCore.QVariant(True))
        self.ui.btn_mountBoot.style().unpolish(self.ui.btn_mountBoot)
        self.ui.btn_mountBoot.style().polish(self.ui.btn_mountBoot)
        PyQt5.QtWidgets.QApplication.processEvents()
        send_magic_packet(self.ui.le_mountMAC.text().strip())
        time.sleep(1)
        self.messageQueue.put('Send WOL and boot mount\n')
        self.logger.debug('Send WOL packet and boot Mount')
        self.ui.btn_mountBoot.setProperty('running', PyQt5.QtCore.QVariant(False))
        self.ui.btn_mountBoot.style().unpolish(self.ui.btn_mountBoot)
        self.ui.btn_mountBoot.style().polish(self.ui.btn_mountBoot)

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
        if platform.system() != 'Windows':
            return
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
        if self.workerINDI.isRunning:
            self.workerINDI.stop()
        if self.workerMountDispatcher.isRunning:
            self.workerMountDispatcher.stop()
        if self.workerModelingDispatcher.isRunning:
            self.workerModelingDispatcher.stop()
        if platform.system() == 'Windows':
            if self.workerUpload.isRunning:
                self.workerUpload.stop()
        if self.workerRemote.isRunning:
            self.workerRemote.stop()
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        if self.workerDome.isRunning:
            self.workerDome.stop()
        if self.workerImaging.isRunning:
            self.workerImaging.stop()

        self.workerINDI.initConfig()
        self.workerMountDispatcher.initConfig()
        self.workerModelingDispatcher.initConfig()
        self.workerEnvironment.initConfig()
        self.workerDome.initConfig()
        self.workerRemote.initConfig()
        self.workerImaging.initConfig()
        if platform.system() == 'Windows':
            self.workerUpload.initConfig()
        self.hemisphereWindow.initConfig()
        self.imageWindow.initConfig()
        self.analyseWindow.initConfig()
        self.messageWindow.initConfig()
        self.relays.initConfig()

        if self.ui.checkEnableINDI.isChecked():
            self.threadINDI.start()
        if not self.workerMountDispatcher.isRunning:
            self.threadMountDispatcher.start()
        if not self.workerModelingDispatcher.isRunning:
            self.threadModelingDispatcher.start()
        if not self.workerEnvironment.isRunning:
            self.threadEnvironment.start()
        if not self.workerDome.isRunning:
            self.threadDome.start()
        if not self.workerImaging.isRunning:
            self.threadImaging.start()
        if self.ui.checkEnableRemoteAccess.isChecked():
            self.threadRemote.start()
        if platform.system() == 'Windows':
            self.threadUpload.start()

        # make windows visible, if they were on the desktop depending on their show status
        if self.hemisphereWindow.showStatus:
            self.hemisphereWindow.showWindow()
            self.hemisphereWindow.drawHemisphere()
        else:
            self.hemisphereWindow.setVisible(False)
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

        # store config in all submodules
        self.workerMountDispatcher.storeConfig()
        self.workerModelingDispatcher.storeConfig()
        self.workerEnvironment.storeConfig()
        self.workerDome.storeConfig()
        self.workerImaging.storeConfig()
        if platform.system() == 'Windows':
            self.workerUpload.storeConfig()
        self.hemisphereWindow.storeConfig()
        self.imageWindow.storeConfig()
        self.analyseWindow.storeConfig()
        self.messageWindow.storeConfig()
        self.relays.storeConfig()
        self.workerINDI.storeConfig()

    def loadConfigData(self):
        try:
            with open('config/config.cfg', 'r') as data_file:
                self.config = json.load(data_file)
        except Exception as e:
            self.messageQueue.put('#BRConfig.cfg could not be loaded !\n')
            self.logger.error('Item in config.cfg not loaded error:{0}'.format(e))
            self.config = {}

    def saveConfig(self):
        filepath = os.getcwd() + '/config/' + self.ui.le_configName.text() + '.cfg'
        self.saveConfigData(filepath)

    def saveConfigQuit(self):
        filepath = os.getcwd() + '/config/' + self.ui.le_configName.text() + '.cfg'
        self.saveConfigData(filepath)
        if self.workerMountDispatcher.isRunning:
            self.workerMountDispatcher.stop()
        if self.workerEnvironment.isRunning:
            self.workerEnvironment.stop()
        if self.workerDome.isRunning:
            self.workerDome.stop()
        if platform.system() == 'Windows':
            if self.workerUpload.isRunning:
                self.workerUpload.stop()
        if self.workerModelingDispatcher.isRunning:
            self.workerModelingDispatcher.stop()
        if self.workerRemote.isRunning:
            self.workerRemote.stop()
        if self.workerINDI.isRunning:
            self.workerINDI.stop()
        PyQt5.QtCore.QCoreApplication.quit()

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
        value = self.selectFile(self, 'Open config file', '/config', 'Config files (*.cfg)', '.cfg', True)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            try:
                with open(value + '.cfg', 'r') as data_file:
                    self.config = json.load(data_file)
                    self.initConfig()
            except Exception as e:
                self.messageQueue.put('#BRConfig.cfg could not be loaded !\n')
                self.logger.error('Item in config.cfg not loaded error:{0}'.format(e))
                self.config = {}
        else:
            self.logger.warning('no config file selected')

    def saveConfigAs(self):
        value = self.selectFile(self, 'Save config file', '/config', 'Config files (*.cfg)', '.cfg', False)
        if value != '':
            self.ui.le_configName.setText(os.path.basename(value))
            self.saveConfigData(value + '.cfg')
        else:
            self.logger.warning('No config file selected')

    def selectAnalyseFileName(self):
        value = self.selectFile(self, 'Open analyse file', '/analysedata', 'Analyse files (*.dat)', '.dat', True)
        if value != '':
            self.ui.le_analyseFileName.setText(os.path.basename(value))
            self.analyseWindow.showWindow()
        else:
            self.logger.warning('no file selected')

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

    def setINDIStatus(self, status):
        if status == 0:
            self.ui.le_INDIStatus.setText('UnconnectedState')
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif status == 1:
            self.ui.le_INDIStatus.setText('HostLookupState')
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
        elif status == 2:
            self.ui.le_INDIStatus.setText('ConnectingState')
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
        elif status == 3:
            self.ui.le_INDIStatus.setText('ConnectedState')
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')
        elif status == 6:
            self.ui.le_INDIStatus.setText('ClosingState')
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
        else:
            self.ui.le_INDIStatus.setText('Error')
        if not self.ui.checkEnableINDI.isChecked():
            self.ui.btn_INDIConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')

    def setINDIStatusCCD(self, status):
        if status:
            self.ui.le_INDIStatusCCD.setStyleSheet('background-color: green;')
        else:
            self.ui.le_INDIStatusCCD.setStyleSheet('background-color: red;')

    def setINDIStatusEnvironment(self, status):
        if status:
            self.ui.le_INDIStatusEnvironment.setStyleSheet('background-color: green;')
        else:
            self.ui.le_INDIStatusEnvironment.setStyleSheet('background-color: red;')

    def setINDIStatusDome(self, status):
        if status:
            self.ui.le_INDIStatusDome.setStyleSheet('background-color: green;')
        else:
            self.ui.le_INDIStatusDome.setStyleSheet('background-color: red;')

    def fillINDIData(self, data):
        if data['Name'] == 'CCD':
            self.ui.le_INDICCD.setText(data['value'])
        elif data['Name'] == 'Environment':
            self.ui.le_INDIEnvironment.setText(data['value'])
        elif data['Name'] == 'Dome':
            self.ui.le_INDIDome.setText(data['value'])
        elif data['Name'] == 'CameraStatus':
            self.imageWindow.ui.le_INDICameraStatus.setText(data['value'])

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

    def setStatusSolver(self, status):
        if status == 3:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: green;color: black;}')
        elif status == 2:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: yellow;color: black;}')
        elif status == 1:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: red;color: black;}')
        else:
            self.ui.btn_solverConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')

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

    def setDomeStatusText(self, status):
        self.ui.le_domeStatusText.setText(status)

    @staticmethod
    def timeStamp():
        return time.strftime('%H:%M:%S -> ', time.localtime())

    def mainLoop(self):
        self.fillMountData()
        self.fillEnvironmentData()
        while not self.INDIStatusQueue.empty():
            data = self.INDIStatusQueue.get()
            self.fillINDIData(data)
        while not self.messageQueue.empty():
            text = self.messageQueue.get()
            textadd = self.timeStamp()
            if text == 'delete':
                self.messageWindow.ui.messages.clear()
            elif text.startswith('ToModel>'):
                self.hemisphereWindow.ui.le_numberPointsToModel.setText(text[8:])
            elif text.startswith('Slewed>'):
                self.hemisphereWindow.ui.le_numberPointsSlewed.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToModel.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsSlewed.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToModel.text()))

            elif text.startswith('Imaged>'):
                self.hemisphereWindow.ui.le_numberPointsImaged.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToModel.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsImaged.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToModel.text()))
            elif text.startswith('Solved>'):
                self.hemisphereWindow.ui.le_numberPointsSolved.setText(text[7:])
                if float(self.hemisphereWindow.ui.le_numberPointsToModel.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsSolved.setValue(1000 * float(text[7:]) / float(self.hemisphereWindow.ui.le_numberPointsToModel.text()))
            elif text.startswith('Processed>'):
                self.hemisphereWindow.ui.le_numberPointsProcessed.setText(text[10:])
                if float(self.hemisphereWindow.ui.le_numberPointsToModel.text()) != 0:
                    self.hemisphereWindow.ui.bar_numberPointsProcessed.setValue(1000 * float(text[10:]) / float(self.hemisphereWindow.ui.le_numberPointsToModel.text()))
            elif text.startswith('percent'):
                self.ui.bar_modelingStatusPercent.setValue(int(1000 * float(text[7:])))
            elif text.startswith('timeleft'):
                self.ui.le_modelingStatusTime.setText(text[8:])
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
                self.messageWindow.ui.messages.setTextColor(self.COLOR_ORANGE)
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
        PyQt5.QtCore.QTimer.singleShot(100, self.mainLoop)


class MyApp(PyQt5.QtWidgets.QApplication):
    import traceback

    def notify(self, obj, event):
        isex = False
        try:
            retValue = PyQt5.QtWidgets.QApplication.notify(self, obj, event)
            return retValue
        except Exception as e:
            isex = True
            result = traceback.format_exception(*sys.exc_info())
            logging.error('-----------------------------------------')
            logging.error('Object: {0},  Event:{1}'.format(obj, event))
            logging.error('Exception error in event loop: {0}'.format(e))
            for i in range(0, len(result)):
                logging.error(result[i].replace('\n', ''))
            logging.error('-----------------------------------------')
            return False
        finally:
            pass
            # if isex:
            #    self.quit()


if __name__ == "__main__":
    import traceback
    import warnings
    import socket

    # setting except hook to get stack traces into the log files
    def except_hook(typeException, valueException, tbackException):
        result = traceback.format_exception(typeException, valueException, tbackException)
        logging.error('-----------------------------------------')
        logging.error('Logging an uncatched Exception')
        for i in range(0, len(result)):
            logging.error(result[i].replace('\n', ''))
        logging.error('-----------------------------------------')
        sys.__excepthook__(typeException, valueException, tbackException)

    # app = PyQt5.QtWidgets.QApplication(sys.argv)
    # implement notify different to catch exception from event handler
    app = MyApp(sys.argv)
    splash_pix = PyQt5.QtGui.QPixmap(':/mw3_splash.ico')
    splash = PyQt5.QtWidgets.QSplashScreen(splash_pix, PyQt5.QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()

    BUILD_NO = '3.0 alpha 10'

    warnings.filterwarnings("ignore")
    name = 'mount.{0}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
    handler = logging.handlers.RotatingFileHandler(name, backupCount=3)
    logging.basicConfig(level=logging.INFO,
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
    logging.info('Platform : ' + platform.system())
    logging.info('Release  : ' + platform.release())
    logging.info('Version  : ' + platform.version())
    logging.info('Machine  : ' + platform.machine())
    host = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')][: 1]
    for i in range(0, len(host)):
        logging.info('Computer IP address: ' + host[i])
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
    sys.excepthook = except_hook
    app.setWindowIcon(PyQt5.QtGui.QIcon('mw.ico'))
    mountApp = MountWizzardApp()
    logging.info('Screensize: {0} x {1}'.format(mountApp.screenSizeX, mountApp.screenSizeY))
    mountApp.show()
    # end of splash screen
    splash.finish(mountApp)
    sys.exit(app.exec_())
