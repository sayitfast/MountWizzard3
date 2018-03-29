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
import copy
import threading


class MountCommandRunner(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

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
        self.numberBytesToReceive = -1
        self.commandSet = dict()
        self.sendLock = False

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
        self.socket.error.connect(self.handleError)
        self.socket.readyRead.connect(self.handleReadyRead)
        while self.isRunning:
            while not self.app.mountCommandQueue.empty() and self.connected and not self.sendLock:
                rawCommand = self.app.mountCommandQueue.get()
                if isinstance(rawCommand, str):
                    # only a single command without return needed
                    command = rawCommand
                elif isinstance(rawCommand, dict):
                    self.commandSet = rawCommand
                    command = rawCommand['command']
                else:
                    command = ''
                    self.logger.error('Mount RunnerCommand received command {0} wrong type: {1}'.format(commandSet, type(commandSet)))
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
            if not self.connected and self.socket.state() == 0:
                self.app.sharedMountDataLock.lockForRead()
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                self.app.sharedMountDataLock.unlock()
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
        self.socket.error.disconnect(self.handleError)
        self.socket.readyRead.disconnect(self.handleReadyRead)

        self.socket.close()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def handleHostFound(self):
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerCommand found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Command': True})
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerCommand connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleError(self):
        self.logger.warning('Mount RunnerCommand connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        self.logger.debug('Mount RunnerCommand connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerCommand connection is disconnected from host')
        self.signalConnected.emit({'Command': False})
        self.connected = False

    def handleReadyRead(self):
        while len(self.messageString) < self.numberBytesToReceive:
            tmp = self.socket.read(1024).decode()
            self.messageString += tmp
            # print(len(self.messageString), self.messageString)
        messageToProcess = self.messageString
        self.messageString = ''
        self.commandSet['reply'] = messageToProcess.rstrip('#')
        self.sendLock = False
        # print('To Receive: {0}, received: >{1}<'.format(self.numberBytesToReceive, self.messageString))

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket CommandRunner not connected')
