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
import threading
import PyQt5
from baseclasses import checkParamIP


class MountIpDirect(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    BLIND_COMMANDS = [':AP#', ':hP#', ':PO#', ':RT0#', ':RT1#', ':RT2#', ':RT9#', ':STOP#', ':U2#']

    def __init__(self, app):
        super().__init__()

        self.app = app
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.checkIP = checkParamIP.CheckIP()
        self.socket = None
        self.message_string = ''
        self.mountIP = ''
        self.mountMAC = ''
        self.mountPort = 0
        self.value_azimuth = 0
        self.value_altitude = 0
        self.sendCommandLock = threading.Lock()
        self.initConfig()
        self.app.ui.le_mountIP.textChanged.connect(self.setIP)
        self.app.ui.le_mountPort.textChanged.connect(self.setPort)
        self.app.ui.le_mountMAC.textChanged.connect(self.setMAC)

    def initConfig(self):
        try:
            if 'MountIP' in self.app.config:
                self.app.ui.le_mountIP.setText(self.app.config['MountIP'])
            if 'MountPort' in self.app.config:
                self.app.ui.le_mountPort.setText(self.app.config['MountPort'])
            if 'MountMAC' in self.app.config:
                self.app.ui.le_mountMAC.setText(self.app.config['MountMAC'])

        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            self.setIP()
            self.setPort()
            self.setMAC()

    def storeConfig(self):
        self.app.config['MountIP'] = self.app.ui.le_mountIP.text()
        self.app.config['MountPort'] = self.app.ui.le_mountPort.text()
        self.app.config['MountMAC'] = self.app.ui.le_mountMAC.text()

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_mountPort)
        if valid:
            self.mountPort = value

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_mountIP)
        if valid:
            self.mountIP = value

    def setMAC(self):
        valid, value = self.checkIP.checkMAC(self.app.ui.le_mountMAC)
        if valid:
            self.mountMAC = value

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.connectToHost(self.mountIP, self.mountPort)
        while self.isRunning:
            if not self.app.INDISendCommandQueue.empty():
                indi_command = self.app.INDISendCommandQueue.get()
                self.sendMessage(indi_command)
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.INDIServerIP, self.INDIServerPort)
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
        self.logger.info('Mount connected at {}:{}'.format(self.mountIP, self.mountPort))

    def handleError(self, socketError):
        self.logger.error('Mount connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.logger.info('Mount connection has state: {0}'.format(self.socket.state()))
        self.status.emit(self.socket.state())

    def handleDisconnect(self):
        self.logger.info('Mount connection is disconnected from host')
        self.connected = False

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        self.message_string = ''

        # Get message from socket.
        while self.socket.bytesAvailable():
            # print(self.socket.bytesAvailable())
            tmp = str(self.socket.read(1000), "ascii")
            self.message_string += tmp

        # Try and parse the message.
        return self.message_string

    def sendCommand(self, command):
        if self.connected:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(command)
            else:
                self.logger.warning('Socket not connected')

