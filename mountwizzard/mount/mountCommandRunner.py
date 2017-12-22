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
import threading


class MountCommandRunner(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

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
                      ':MA#': 1,
                      ':shutdown#': 1,
                      ':Sw': 1,
                      ':Sdat': 1,
                      ':Suaf': 1,
                      ':FLIP': 1,
                      ':So': 1,
                      ':Sh': 1,
                      ':SREF': 1
    }

    def __init__(self, app, data, signalConnected):
        super().__init__()

        self.app = app
        self.data = data
        self.signalConnected = signalConnected
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.messageString = ''
        self.sendLock = threading.Lock()

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        # self.socket.readyRead.connect(self.handleReadyRead)
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()
            while not self.app.mountCommandQueue.empty():
                command = self.app.mountCommandQueue.get()
                self.sendCommand(command)
            time.sleep(0.1)
            self.socket.state()
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
        pass

    def handleConnected(self):
        self.connected = True
        self.signalConnected.emit({'Command': True})
        self.logger.info('Mount RunnerCommand connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerCommand connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount connection CommandRunner has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerCommand connection is disconnected from host')
        self.signalConnected.emit({'Command': False})
        self.connected = False

    def handleReadyRead(self):
        pass

    def sendCommand(self, command):
        self.sendLock.acquire()
        messageToProcess = ''
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                numberBytesToReceive = -1
                for key in self.COMMAND_RETURN:
                    if command.startswith(key):
                        numberBytesToReceive = self.COMMAND_RETURN[key]
                if numberBytesToReceive > -1:
                    self.socket.write(bytes(command + '\r', encoding='ascii'))
                    if self.socket.bytesAvailable():
                        # now we got some data
                        while self.socket.bytesAvailable():
                            tmp = str(self.socket.read(1000), "ascii")
                            self.messageString += tmp
                        messageToProcess = self.messageString[:numberBytesToReceive].rstrip('#')
                        self.messageString = self.messageString[numberBytesToReceive:]
                        # print('Command: {0}, return value: {1}'.format(command, messageToProcess))
                    else:
                        self.messageString = ''
                else:
                    print('Command: ->{0}<- not known'.format(command))
            else:
                self.logger.warning('Socket RunnerCommand not connected')
        self.sendLock.release()
        return messageToProcess


