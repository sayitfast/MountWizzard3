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


class MountStatusRunnerSlow(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CYCLE_STATUS_SLOW = 10000
    CYCLE_COMMAND = 0.2

    def __init__(self, app, thread, data, signalConnected):
        super().__init__()

        self.app = app
        self.thread = thread
        self.data = data
        self.signalConnected = signalConnected
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.dataTimer = None
        self.isRunning = False
        self.socket = None
        self.sendLock = False
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

    def run(self):
        self.logger.info('mount slow started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.error.connect(self.handleError)
        # timers
        self.dataTimer = PyQt5.QtCore.QTimer(self)
        self.dataTimer.setSingleShot(False)
        self.dataTimer.timeout.connect(self.getStatusSlow)
        self.dataTimer.start(self.CYCLE_STATUS_SLOW)
        while self.isRunning:
            self.doCommand()
            self.doReconnect()
            time.sleep(self.CYCLE_COMMAND)
            PyQt5.QtWidgets.QApplication.processEvents()
        self.dataTimer.stop()
        if self.socket.state() != PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.abort()
        else:
            self.socket.disconnectFromHost()
        self.socket.hostFound.disconnect(self.handleHostFound)
        self.socket.connected.disconnect(self.handleConnected)
        self.socket.stateChanged.disconnect(self.handleStateChanged)
        self.socket.disconnected.disconnect(self.handleDisconnect)
        self.socket.readyRead.disconnect(self.handleReadyRead)
        self.socket.error.disconnect(self.handleError)
        self.socket.close()

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount slow stopped')

    def doCommand(self):
        if not self.sendCommandQueue.empty() and (self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState):
            command = self.sendCommandQueue.get()
            if not self.sendLock:
                self.sendCommand(command)

    def doReconnect(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.UnconnectedState:
            self.app.sharedMountDataLock.lockForRead()
            self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
            self.app.sharedMountDataLock.unlock()
            self.sendCommandQueue.queue.clear()

    @PyQt5.QtCore.pyqtSlot()
    def handleHostFound(self):
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerSlow found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.KeepAliveOption, 1)
        self.signalConnected.emit({'Slow': True})
        self.getStatusSlow()
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerSlow connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleError(self, socketError):
        self.logger.warning('Mount RunnerSlow connection fault: {0}'.format(self.socket.errorString()))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount RunnerSlow connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount RunnerSlow connection is disconnected from host')
        self.signalConnected.emit({'Slow': False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket RunnerSlow not connected')

    @PyQt5.QtCore.pyqtSlot()
    def getStatusSlow(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.app.sharedMountDataLock.lockForRead()
            if 'FW' not in self.data:
                self.data['FW'] = 0
            if self.data['FW'] < 21500:
                self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#')
            else:
                self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:GDUTV#')
            self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            self.messageString += self.socket.read(1024).decode()
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
            if len(messageToProcess) == 0:
                return
            if 'FW' not in self.data:
                self.data['FW'] = 0
            self.app.sharedMountDataLock.lockForWrite()
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
            self.app.sharedMountDataLock.unlock()
        self.sendLock = False
