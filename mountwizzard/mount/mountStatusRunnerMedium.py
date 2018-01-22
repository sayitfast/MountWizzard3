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
import logging
import PyQt5
import time
from queue import Queue


class MountStatusRunnerMedium(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLE_STATUS_MEDIUM = 3000

    def __init__(self, app, data, signalConnected):
        super().__init__()

        self.app = app
        self.data = data
        self.signalConnected = signalConnected
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.counter = 0
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = self.app.transform

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        while self.isRunning:
            if not self.sendCommandQueue.empty() and self.connected:
                command = self.sendCommandQueue.get()
                self.sendCommand(command)
            time.sleep(0.2)
            self.socket.state()
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                self.sendCommandQueue.queue.clear()
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()
        while self.socket.state() != 0:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def handleHostFound(self):
        pass
        # self.logger.info('Mount RunnerMedium found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Medium': True})
        self.getStatusMedium()
        self.logger.info('Mount RunnerMedium connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerMedium connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount RunnerMedium connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerMedium connection is disconnected from host')
        self.signalConnected.emit({'Medium': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket RunnerMedium not connected')

    def getStatusMedium(self):
        doRefractionUpdate = False
        if self.app.ui.checkAutoRefractionNotTracking.isChecked():
            # if there is no tracking, than updating is good
            if 'Status' in self.data:
                if self.data['Status'] != '0':
                    doRefractionUpdate = True
        if self.app.ui.checkAutoRefractionCamera.isChecked():
            # the same is good if the camera is not in integrating
            if self.app.workerModelingDispatcher.modelingRunner.imagingApps.imagingWorkerCameraAppHandler.data['Camera']['Status'] == 'IDLE':
                doRefractionUpdate = True
        if doRefractionUpdate:
            if 'Temperature' in self.app.workerEnvironment.data and 'Pressure' in self.app.workerEnvironment.data and self.app.workerEnvironment.isRunning:
                pressure = self.app.workerEnvironment.data['Pressure']
                temperature = self.app.workerEnvironment.data['Temperature']
                if (900.0 < pressure < 1100.0) and (-30.0 < temperature < 35.0):
                    self.app.mountCommandQueue.put(':SRPRS{0:04.1f}#'.format(pressure))
                    if temperature > 0:
                        self.app.mountCommandQueue.put(':SRTMP+{0:03.1f}#'.format(temperature))
                    else:
                        self.app.mountCommandQueue.put(':SRTMP-{0:3.1f}#'.format(-temperature))
        self.sendCommandQueue.put(':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#')

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.messageString += tmp
            PyQt5.QtWidgets.QApplication.processEvents()
            # print(self.messageString)
        if len(self.messageString) < 28:
            return
        else:
            messageToProcess = self.messageString[:28]
            self.messageString = self.messageString[28:]
        # Try and parse the message.
        try:
            if 'FW' not in self.data:
                self.data['FW'] = 0
            if len(messageToProcess) == 0:
                return
            valueList = messageToProcess.strip('#').split('#')
            # print(valueList)
            # all parameters are delivered
            if len(valueList) >= 4:
                if len(valueList[0]) > 0:
                    self.data['SlewRate'] = valueList[0]
                if len(valueList[1]) > 0:
                    self.data['TimeToFlip'] = int(float(valueList[1]))
                if len(valueList[2]) > 0:
                    self.data['MeridianLimitTrack'] = int(float(valueList[2]))
                if len(valueList[3]) > 0:
                    self.data['MeridianLimitSlew'] = int(float(valueList[3]))
                self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitTrack'] / 360 * 24 * 60)
                if len(valueList[4]) > 0:
                    self.data['RefractionTemperature'] = valueList[4]
                if len(valueList[5]) > 0:
                    self.data['RefractionPressure'] = valueList[5]
            else:
                self.logger.warning('Parsing Status Medium combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Parsing Status Medium combined command got error:{0}'.format(e))
        finally:
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_MEDIUM, self.getStatusMedium)
