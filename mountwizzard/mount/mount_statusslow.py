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
    CYCLE_COMMAND = 200

    def __init__(self, app, thread, data, signalConnected):
        super().__init__()

        self.app = app
        self.thread = thread
        self.data = data
        self.signalConnected = signalConnected
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.isRunning = False
        self.connected = False
        self.socket = None
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

    def run(self):
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
        self.doCommandQueue()
        while self.isRunning:
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.socket.state() != 3:
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
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def doCommandQueue(self):
        if not self.sendCommandQueue.empty() and self.connected:
            command = self.sendCommandQueue.get()
            self.sendCommand(command)
        if not self.connected and self.socket.state() == 0:
            self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
            self.sendCommandQueue.queue.clear()
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_COMMAND, self.doCommandQueue)

    def handleHostFound(self):
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerSlow found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Slow': True})
        self.getStatusSlow()
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerSlow connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleError(self, socketError):
        self.logger.warning('Mount RunnerSlow connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        self.logger.debug('Mount RunnerSlow connection has state: {0}'.format(self.socket.state()))

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
        self.app.sharedMountDataLock.lockForRead()
        if 'FW' not in self.data:
            self.data['FW'] = 0
        if self.data['FW'] < 21500:
            self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#')
        else:
            self.sendCommandQueue.put(':U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:GDUTV#')
        self.app.sharedMountDataLock.unlock()

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = self.socket.read(1024).decode()
            self.messageString += tmp
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
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_SLOW, self.getStatusSlow)
