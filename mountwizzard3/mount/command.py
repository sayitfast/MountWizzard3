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
    CYCLE_QUEUE = 250
    signalDestruct = PyQt5.QtCore.pyqtSignal()
    # define the number of bytes for the return bytes in case of not having them in bulk mode
    # this is needed, because the mount computer  doesn't support a transaction base like number of
    # bytes to be expected. it's just plain data and i have to find out myself how much it is.
    # due to the fact i'm doing multi threading with multi connections some of the commands run in parallel
    # there are three types of commands:
    #       a) no reply                     this is ok
    #       b) reply without '#'            this is the bad part, don't like it
    #       c) reply ended with '#'         this is normal feedback -> no special treatment
    COMMAND_RETURN_A = [':AP', ':AL', ':hP', ':PO', ':RT0', ':RT1', ':RT2', ':RT9', ':STOP', ':U2', ':hS', ':hF', ':hP',
                        ':KA', ':Me', ':Mn', ':Ms', ':Mw', ':EW', ':NS', ':Q', 'Suaf', ':TSOLAR', ':TQ']
    COMMAND_RETURN_B = [':FLIP', ':shutdown', ':GREF', ':GSC', ':Guaf', ':GTMPLT', ':GTRK', ':GTTRK', ':GTsid', ':MA', ':MS',
                        ':Sa', ':Sev', ':Sr', ':SREF', ':SRPRS', ':SRTMP', ':Slmt', ':Slms', ':St', ':Sw', ':Sz', ':Sdat', ':Gdat']

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
        self.numberReplyToReceive = 0
        self.flagBadReply = False
        self.commandSet = dict()

    def run(self):
        self.logger.info('{0} started'.format(__name__))
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
        # timers
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE_QUEUE)
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.signalConnected.emit({__name__: False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('{0} stopped'.format(__name__))

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
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
                self.commandSet = dict()
            elif isinstance(rawCommand, dict):
                self.commandSet = rawCommand
                command = rawCommand['command']
            else:
                command = ''
                self.logger.error('Mount RunnerCommand received command {0} wrong type: {1}'.format(rawCommand, type(rawCommand)))
            if len(command) > 0:
                # determine how many messages to receive
                # first we have to count how many commands are sent and split them
                commandList = command.split('#')
                # the last item is empty due to split command
                commandList = commandList[:-1]
                # now we have to parse how many of them will give a reply
                self.numberReplyToReceive = 0
                self.flagBadReply = False
                foundReplyTypeA = False
                # iterate through all commands in commandList
                for commandKey in commandList:
                    # if it's in type A, no response expected
                    for key in self.COMMAND_RETURN_A:
                        if commandKey.startswith(key):
                            foundReplyTypeA = True
                            break
                    if not foundReplyTypeA:
                        self.numberReplyToReceive += 1
                        for keyBad in self.COMMAND_RETURN_B:
                            if commandKey.startswith(keyBad):
                                self.flagBadReply = True
                                break
                if self.numberReplyToReceive > 0:
                    self.sendLock = True
                    self.sendCommand(command)
                else:
                    self.sendLock = False
                    self.sendCommand(command)
                self.logger.info('Sending command {0}, with number of replies : {1} and flagBadReply set : {2}'.format(command, self.numberReplyToReceive, self.flagBadReply))

    def doReconnect(self):
        # to get order in connections, we wait for first connecting the Slow type
        if self.mountStatus['Slow'] and self.data['FW'] > 0:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.UnconnectedState:
                if self.connectCounter == 0:
                    self.app.sharedMountDataLock.lockForRead()
                    self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                    self.app.sharedMountDataLock.unlock()
                else:
                    # connection build up is ongoing
                    pass
                if self.connectCounter * self.CYCLE_QUEUE > self.CONNECTION_TIMEOUT:
                    self.socket.abort()
                    self.connectCounter = 0
                else:
                    self.connectCounter += 1
            else:
                if self.socket.state() != PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                    if self.connectCounter * self.CYCLE_QUEUE > self.CONNECTION_TIMEOUT:
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
        self.signalConnected.emit({__name__: True})
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
        self.signalConnected.emit({__name__: False})

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
        # test weather is good feedback (with delimiting '#')
        if self.flagBadReply:
            # if not, we are go for length of string
            if len(self.messageString) < self.numberReplyToReceive:
                return
        else:
            # if so we are counting '#'
            if self.messageString.count('#') < self.numberReplyToReceive:
                return

        if self.flagBadReply:
            if len(self.messageString) != self.numberReplyToReceive:
                self.logger.error('Receiving data with flagBadReply set got error: {0}'.format(self.messageString))
                self.messageString = ''
                messageToProcess = ''
            else:
                messageToProcess = self.messageString
                self.messageString = ''
        else:
            if self.messageString.count('#') != self.numberReplyToReceive:
                self.logger.error('Receiving data with flagBadReply set got error: {0}'.format(self.messageString))
                self.messageString = ''
                messageToProcess = ''
            else:
                messageToProcess = self.messageString
                self.messageString = ''

        if self.flagBadReply:
            self.commandSet['reply'] = messageToProcess
        else:
            self.commandSet['reply'] = messageToProcess.split('#')
            # the last item is empty due to split command
            self.commandSet['reply'] = self.commandSet['reply'][:-1]

        self.logger.info('Receiving reply of command {0}'.format(self.commandSet['reply']))
        self.sendLock = False

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket CommandRunner not connected')
