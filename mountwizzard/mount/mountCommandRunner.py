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


class MountCommandRunner(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    BLIND_COMMANDS = [':AP#', ':hP#', ':PO#', ':RT0#', ':RT1#', ':RT2#', ':RT9#', ':STOP#', ':U2#']

    def __init__(self, app, data, signalMountConnected):
        super().__init__()

        self.app = app
        self.data = data
        self.signalMountConnected = signalMountConnected
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.message_string = ''
        self.sendCommandQueue = Queue()
        self.parseQueue = Queue()

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
        pass

    def handleConnected(self):
        self.connected = True
        self.signalMountConnected.emit(True)
        self.logger.info('Mount connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.logger.info('Mount connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount connection is disconnected from host')
        self.connected = False
        self.signalMountConnected.emit(False)

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        self.message_string = ''

        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.message_string += tmp

        # Try and parse the message.
        values = self.message_string.strip('#').split('#')
        for ret in values:
            (command, target) = self.parseQueue.get()
            print('command ->', command, '   target -> ', target, '   value ->', ret)
        # print(self.message_string)

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.message_string = ''
                if command not in self.BLIND_COMMANDS:
                    if self.socket.waitForReadyRead(3000):
                        # now we got some data
                        while self.socket.bytesAvailable():
                            tmp = str(self.socket.read(1000), "ascii")
                            self.message_string += tmp
                        return self.message_string.strip('#')
            else:
                self.logger.warning('Socket not connected')


