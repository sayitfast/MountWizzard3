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
import logging
import PyQt5
import time
from queue import Queue
from astrometry import transform


class MountStatusRunnerSlow(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLE_STATUS_SLOW = 1000
    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']

    def __init__(self, app, data):
        super().__init__()

        self.app = app
        self.data = data
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.counter = 0
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.parseQueue = Queue()

        self.transform = transform.Transform(self.app)

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
            if not self.sendCommandQueue.empty():
                command = self.sendCommandQueue.get()
                self.sendCommand(command)
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.finished.emit()

    def handleHostFound(self):
        self.logger.info('Mount found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.connected = True
        self.getStatusSlow()
        self.logger.info('Mount connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.logger.info('Mount connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount connection is disconnected from host')
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
            else:
                self.logger.warning('Socket not connected')

    def getStatusSlow(self):
        if 'FW' in self.data:
            if self.data['FW'] < 21500:
                self.sendCommandQueue.put(':U2#:GRTMP#:GRPRS#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#')
            else:
                self.sendCommandQueue.put(':U2#:GRTMP#:GRPRS#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:GDUTV#')

    def handleReadyRead(self):
        messageToProcess = ''
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.messageString += tmp
            if self.data['FW'] < 21500:
                if len(self.messageString) < 32:
                    return
                else:
                    messageToProcess = self.messageString[:32]
                    self.messageString = self.messageString[32:]
            else:
                if len(self.messageString) < 45:
                    return
                else:
                    messageToProcess = self.messageString[:45]
                    self.messageString = self.messageString[45:]
        # Try and parse the message.
        try:
            if len(messageToProcess) == 0 or 'FW' not in self.data:
                return
            valueList = messageToProcess.strip('#').split('#')
            # +000.0# 0950.0# +029.8# 1 0 1 +90# +00# V,2018-03-24#
            # all parameters are delivered
            if 4 < len(valueList) < 7:
                if len(valueList[0]) > 0:
                    self.data['RefractionTemperature'] = valueList[0].strip('#')
                if len(valueList[1]) > 0:
                    self.data['RefractionPressure'] = valueList[1].strip('#')
                if len(valueList[2]) > 0:
                    self.data['TelescopeTempDEC'] = valueList[2].strip('#')
                if len(valueList[3]) > 0:
                    self.data['RefractionStatus'] = valueList[3].strip('#')[0]
                    self.data['UnattendedFlip'] = valueList[3].strip('#')[1]
                    self.data['DualAxisTracking'] = valueList[3].strip('#')[2]
                    self.data['CurrentHorizonLimitHigh'] = valueList[3].strip('#')[3:]
                if len(valueList[4]) > 0:
                    self.data['CurrentHorizonLimitLow'] = valueList[4].strip('#')
                if self.data['FW'] > 21500 and len(valueList[5]) > 0:
                    valid, expirationDate = valueList[5].split(',')
                    self.data['UTCDataValid'] = valid
                    self.data['UTCDataExpirationDate'] = expirationDate
            else:
                self.logger.warning('Parsing Status Slow combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Parsing Status Slow combined command got error:{0}'.format(e))
        finally:
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_SLOW, self.getStatusSlow)
