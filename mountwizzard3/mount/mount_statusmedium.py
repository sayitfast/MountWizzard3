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
############################################################
import logging
import PyQt5
import time
from queue import Queue
from astrometry import transform


class MountStatusRunnerMedium(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
    CYCLE_STATUS_MEDIUM = 3000
    CYCLE = 250
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread, data, signalConnected, mountStatus):
        super().__init__()

        self.app = app
        self.thread = thread
        self.data = data
        self.signalConnected = signalConnected
        self.mountStatus = mountStatus
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.dataTimer = None
        self.cycleTimer = None
        self.isRunning = False
        self.connectCounter = 0
        self.socket = None
        self.sendLock = False
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

    def run(self):
        self.logger.info('mount medium started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.KeepAliveOption, 1)
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.error.connect(self.handleError)
        # timer
        self.dataTimer = PyQt5.QtCore.QTimer(self)
        self.dataTimer.setSingleShot(False)
        self.dataTimer.timeout.connect(self.getStatusMedium)
        self.dataTimer.start(self.CYCLE_STATUS_MEDIUM)
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.signalConnected.emit({'Medium': False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount medium stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.disconnectFromHost()
        self.cycleTimer.stop()
        self.dataTimer.stop()
        self.signalDestruct.disconnect(self.destruct)
        self.socket.hostFound.disconnect(self.handleHostFound)
        self.socket.connected.disconnect(self.handleConnected)
        self.socket.stateChanged.disconnect(self.handleStateChanged)
        self.socket.disconnected.disconnect(self.handleDisconnect)
        self.socket.error.disconnect(self.handleError)
        self.socket.readyRead.disconnect(self.handleReadyRead)
        self.socket.abort()

    def doCommand(self):
        self.doReconnect()
        if not self.sendCommandQueue.empty() and (self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState):
            command = self.sendCommandQueue.get()
            if not self.sendLock:
                self.sendCommand(command)

    def doReconnect(self):
        # to get order in connections, we wait for first connecting the once type
        if self.mountStatus['Once'] and self.data['FW'] > 0:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.UnconnectedState:
                if self.connectCounter == 0:
                    self.app.sharedMountDataLock.lockForRead()
                    self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                    self.app.sharedMountDataLock.unlock()
                    self.sendCommandQueue.queue.clear()
                else:
                    # connection build up is ongoing
                    pass
                if self.connectCounter * self.CYCLE > self.CONNECTION_TIMEOUT:
                    self.socket.abort()
                    self.connectCounter = 0
                else:
                    self.connectCounter += 1
            else:
                if self.socket.state() != PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                    if self.connectCounter * self.CYCLE > self.CONNECTION_TIMEOUT:
                        self.socket.abort()
                        self.connectCounter = 0
                    else:
                        self.connectCounter += 1
                else:
                    # connected
                    pass

    @PyQt5.QtCore.pyqtSlot()
    def handleHostFound(self):
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerMedium found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.signalConnected.emit({'Medium': True})
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerMedium connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('Mount RunnerMedium connection fault: {0}'.format(socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount RunnerMedium connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount RunnerMedium connection is disconnected from host')
        self.signalConnected.emit({'Medium': False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.sendLock = True
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket RunnerMedium not connected')

    @PyQt5.QtCore.pyqtSlot()
    def getStatusMedium(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            doRefractionUpdate = False
            pressure = 950
            temperature = 10
            if self.app.ui.checkAutoRefractionNone.isChecked():
                doRefractionUpdate = False
            if self.app.ui.checkAutoRefractionContinous.isChecked():
                doRefractionUpdate = True
                self.app.sharedEnvironmentDataLock.lockForRead()
                if 'MovingAverageTemperature' in self.app.workerEnvironment.data and 'MovingAveragePressure' in self.app.workerEnvironment.data and self.app.workerEnvironment.isRunning:
                    pressure = self.app.workerEnvironment.data['MovingAveragePressure']
                    temperature = self.app.workerEnvironment.data['MovingAverageTemperature']
                self.app.sharedEnvironmentDataLock.unlock()
            if self.app.ui.checkAutoRefractionNotTracking.isChecked():
                # if there is no tracking, than updating is good
                self.app.sharedMountDataLock.lockForRead()
                if 'Status' in self.data:
                    # status 0 means tracking, and in tracking mode we do not want to update
                    if self.data['Status'] != '0':
                        doRefractionUpdate = True
                self.app.sharedMountDataLock.unlock()
                self.app.sharedEnvironmentDataLock.lockForRead()
                if 'Temperature' in self.app.workerEnvironment.data and 'Pressure' in self.app.workerEnvironment.data and self.app.workerEnvironment.isRunning:
                    pressure = self.app.workerEnvironment.data['Pressure']
                    temperature = self.app.workerEnvironment.data['Temperature']
                self.app.sharedEnvironmentDataLock.unlock()
            if doRefractionUpdate:
                if (900.0 < pressure < 1100.0) and (-30.0 < temperature < 35.0):
                    self.app.mountCommandQueue.put(':SRPRS{0:04.1f}#'.format(pressure))
                    if temperature > 0:
                        self.app.mountCommandQueue.put(':SRTMP+{0:03.1f}#'.format(temperature))
                    else:
                        self.app.mountCommandQueue.put(':SRTMP-{0:3.1f}#'.format(-temperature))
            self.sendCommandQueue.put(':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#')

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
            # print(self.messageString)
        if len(self.messageString) < 28:
            return
        else:
            messageToProcess = self.messageString[:28]
            self.messageString = self.messageString[28:]
        # Try and parse the message.
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            valueList = messageToProcess.strip('#').split('#')
            # print(valueList)
            # all parameters are delivered
            if len(valueList) >= 4:
                if len(valueList[0]) > 0:
                    self.data['SlewRate'] = valueList[0]
                if len(valueList[1]) > 0:
                    self.data['TimeToFlip'] = int(valueList[1])
                if len(valueList[2]) > 0:
                    self.data['MeridianLimitGuide'] = int(valueList[2])
                if len(valueList[3]) > 0:
                    self.data['MeridianLimitSlew'] = int(valueList[3])
                self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitGuide'] / 360 * 24 * 60)
                if len(valueList[4]) > 0:
                    self.data['RefractionTemperature'] = valueList[4]
                if len(valueList[5]) > 0:
                    self.data['RefractionPressure'] = valueList[5]
                self.app.workerMountDispatcher.signalMountLimits.emit()
            else:
                self.logger.warning('Parsing Status Medium combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Problem parsing response, error: {0}, message:{1}'.format(e, messageToProcess))
        finally:
            self.app.sharedMountDataLock.unlock()
        self.sendLock = False
