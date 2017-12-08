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


class MountStatusRunnerMedium(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLE_STATUS_MEDIUM = 3000

    def __init__(self, app, data, signalMountTrackPreview):
        super().__init__()

        self.app = app
        self.data = data
        self.signalMountTrackPreview = signalMountTrackPreview
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

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.finished.emit()

    def handleHostFound(self):
        pass
        # self.logger.info('Mount RunnerMedium found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.connected = True
        self.getStatusMedium()
        self.logger.info('Mount RunnerMedium connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerMedium connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount RunnerMedium connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerMedium connection is disconnected from host')
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
            else:
                self.logger.warning('Socket RunnerMedium not connected')

    def getStatusMedium(self):
        self.sendCommandQueue.put(':GMs#:Gmte#:Glmt#:Glms#')

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.messageString += tmp
        if len(self.messageString) < 14:
            return
        else:
            messageToProcess = self.messageString[:14]
            self.messageString = self.messageString[14:]
        # Try and parse the message.
        try:
            if len(messageToProcess) == 0 or 'FW' not in self.data:
                return
            valueList = messageToProcess.strip('#').split('#')
            # all parameters are delivered
            if len(valueList) == 4:
                if len(valueList[0]) > 0:
                    self.data['SlewRate'] = valueList[0]
                if len(valueList[1]) > 0:
                    self.data['TimeToFlip'] = int(float(valueList[1]))
                if len(valueList[2]) > 0:
                    self.data['MeridianLimitTrack'] = int(float(valueList[2]))
                if len(valueList[3]) > 0:
                    self.data['MeridianLimitSlew'] = int(float(valueList[3]))
                self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitTrack'] / 360 * 24 * 60)
                self.signalMountTrackPreview.emit()
            else:
                self.logger.warning('Parsing Status Medium combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Parsing Status Medium combined command got error:{0}'.format(e))
        finally:
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_MEDIUM, self.getStatusMedium)
