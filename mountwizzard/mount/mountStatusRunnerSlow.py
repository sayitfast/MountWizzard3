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


class MountStatusRunnerSlow(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLE_STATUS_SLOW = 10000

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
        # self.logger.info('Mount RunnerSlow found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Slow': True})
        self.getStatusSlow()
        self.logger.info('Mount RunnerSlow connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerSlow connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount RunnerSlow connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerSlow connection is disconnected from host')
        self.signalConnected.emit({'Slow': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket RunnerSlow not connected')

    def getStatusSlow(self):
        if 'FW' not in self.data:
            self.data['FW'] = 0
        if self.data['FW'] < 21500:
            self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#')
        else:
            self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:GDUTV#')

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.messageString += tmp
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.data['FW'] < 21500:
            if len(self.messageString) < 18:
                return
            else:
                messageToProcess = self.messageString[:18]
                self.messageString = self.messageString[18:]
        else:
            if len(self.messageString) < 31:
                return
            else:
                messageToProcess = self.messageString[:31]
                self.messageString = self.messageString[31:]
        # Try and parse the message.
        try:
            if 'FW' not in self.data:
                self.data['FW'] = 0
            if len(messageToProcess) == 0:
                return
            valueList = messageToProcess.strip('#').split('#')
            #  +029.8# 1 0 1 +90# +00# V,2018-03-24#
            # all parameters are delivered
            if 2 < len(valueList) < 5:
                if len(valueList[0]) > 0:
                    self.data['TelescopeTempDEC'] = valueList[0]
                if len(valueList[1]) > 0:
                    self.data['RefractionStatus'] = valueList[1][0]
                    self.data['UnattendedFlip'] = valueList[1][1]
                    self.data['DualAxisTracking'] = valueList[1][2]
                    self.data['CurrentHorizonLimitHigh'] = valueList[1][3:]
                if len(valueList[2]) > 0:
                    self.data['CurrentHorizonLimitLow'] = valueList[2]
                if self.data['FW'] > 21500 and len(valueList[3]) > 0:
                    valid, expirationDate = valueList[3].split(',')
                    self.data['UTCDataValid'] = valid
                    self.data['UTCDataExpirationDate'] = expirationDate
            else:
                self.logger.warning('Parsing Status Slow combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Parsing Status Slow combined command got error:{0}'.format(e))
        finally:
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_SLOW, self.getStatusSlow)
