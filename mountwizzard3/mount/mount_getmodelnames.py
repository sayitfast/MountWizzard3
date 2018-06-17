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
import copy
from queue import Queue
from astrometry import transform


class MountGetModelNames(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
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
        self.isRunning = False
        self.connectCounter = 0
        self.socket = None
        self.sendLock = False
        self.cycleTimer = None
        self.messageString = ''
        self.sendCommandQueue = Queue()

    def run(self):
        self.logger.info('mount get model names started')
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
            self.signalConnected.emit({'GetName': False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount get model names stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.disconnectFromHost()
        self.cycleTimer.stop()
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
        self.logger.debug('Mount GetModelNames found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.signalConnected.emit({'GetName': True})
        self.getModelNames()
        self.logger.info('Mount GetModelNames connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('Mount GetModelNames connection fault: {0}'.format(socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount GetModelNames connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount GetModelNames connection is disconnected from host')
        self.signalConnected.emit({'GetName': False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.sendLock = True
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket GetModelNames not connected')

    def getModelNames(self):
        # asking for 50 model names
        command = ''
        for i in range(1, 51):
            command += (':modelnam{0:d}#'.format(i))
        self.sendCommandQueue.put(command)

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(4000).decode()

        if self.messageString.count('#') != 50:
            if self.messageString.count('#') > 50:
                self.logger.error('Receiving data got error:{0}'.format(self.messageString))
                messageToProcess = self.messageString
                self.messageString = ''
            else:
                # go on receiving data
                return
        else:
            messageToProcess = self.messageString
            self.messageString = ''
        # now we got all information about the model write run
        valueList = messageToProcess.strip('#').split('#')
        # quick check:
        self.app.sharedMountDataLock.lockForWrite()
        self.data['ModelNames'] = copy.copy(valueList)
        self.app.sharedMountDataLock.unlock()
        self.app.workerMountDispatcher.signalMountShowModelNames.emit()
        self.sendLock = False
