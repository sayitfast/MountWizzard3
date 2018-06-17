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
###########################################################
import logging
import PyQt5
import time


class MountCommandRunner(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
    CYCLE = 250
    signalDestruct = PyQt5.QtCore.pyqtSignal()
    # define the number of bytes for the return bytes in case of not having them in bulk mode
    # this is needed, because the mount computer  doesn't support a transaction base like number of
    # bytes to be expected. it's just plain data and i have to find out myself how much it is.
    # due to the fact i'm doing multi threading with multi connections some of the commands run in parallel
    COMMAND_RETURN = {':AP#': 0,
                      ':hP#': 0,
                      ':PO#': 0,
                      ':RT0#': 0,
                      ':RT1#': 0,
                      ':RT2#': 0,
                      ':RT9#': 0,
                      ':STOP#': 0,
                      ':U2#': 0,
                      ':modelld0': 2,
                      ':modelsv0': 2,
                      ':modeldel0': 2,
                      ':delalst': 2,
                      ':delalig': 1,
                      ':SRPRS': 1,
                      ':SRTMP': 1,
                      ':Sz': 1,
                      ':Sa': 1,
                      ':Sr': 1,
                      ':Sd': 1,
                      ':MA#': 1,
                      ':MS#': 1,
                      ':shutdown': 1,
                      ':Sw': 1,
                      ':Sdat': 1,
                      ':Suaf': 1,
                      ':FLIP': 1,
                      ':So': 1,
                      ':Sh': 1,
                      ':SREF': 1,
                      ':CM#': 27,
                      ':CMS#': 1,
                      ':Gr#': 12,
                      ':Gd#': 12,
                      ':newalig#': 1,
                      ':endalig#': 1,
                      ':newalpt': 1,
                      ':CMCFG': 1}

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
        self.numberBytesToReceive = -1
        self.commandSet = dict()

    def run(self):
        self.logger.info('mount command started')
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
        self.socket.error.connect(self.handleError)
        self.socket.readyRead.connect(self.handleReadyRead)

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
            self.signalConnected.emit({'Command': False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount command stopped')

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
        if not self.app.mountCommandQueue.empty() and (self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState) and not self.sendLock:
            rawCommand = self.app.mountCommandQueue.get()
            if isinstance(rawCommand, str):
                # only a single command without return needed
                command = rawCommand
            elif isinstance(rawCommand, dict):
                self.commandSet = rawCommand
                command = rawCommand['command']
            else:
                command = ''
                self.logger.error('Mount RunnerCommand received command {0} wrong type: {1}'.format(rawCommand, type(rawCommand)))
            if len(command) > 0:
                # determine how many bytes to receive
                self.numberBytesToReceive = -1
                for key in self.COMMAND_RETURN:
                    if command.startswith(key):
                        self.numberBytesToReceive = self.COMMAND_RETURN[key]
                        break
                if self.numberBytesToReceive == -1:
                    self.logger.error('Command >(0)< not known'.format(command))
                elif self.numberBytesToReceive > 0:
                    self.sendLock = True
                    self.sendCommand(command)
                else:
                    self.sendLock = False
                    self.sendCommand(command)

    def doReconnect(self):
        # to get order in connections, we wait for first connecting the once type
        if self.mountStatus['Once'] and self.data['FW'] > 0:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.UnconnectedState:
                if self.connectCounter == 0:
                    self.app.sharedMountDataLock.lockForRead()
                    self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                    self.app.sharedMountDataLock.unlock()
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
        self.logger.debug('Mount RunnerCommand found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.signalConnected.emit({'Command': True})
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerCommand connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('Mount RunnerCommand connection fault: {0}'.format(socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount RunnerCommand connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount RunnerCommand connection is disconnected from host')
        self.signalConnected.emit({'Command': False})

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        while (len(self.messageString) < self.numberBytesToReceive) and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
        messageToProcess = self.messageString
        self.messageString = ''
        self.commandSet['reply'] = messageToProcess.rstrip('#')
        self.sendLock = False

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket CommandRunner not connected')
