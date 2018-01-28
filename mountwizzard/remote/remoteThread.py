############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import logging
import PyQt5
import threading
import socket
import time
from baseclasses import checkParamIP


class Remote(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalRemoteConnected = PyQt5.QtCore.pyqtSignal(bool, name='RemoteConnected')
    signalRemoteShutdown = PyQt5.QtCore.pyqtSignal(bool, name='RemoteShutdown')
    TCP_IP = '127.0.0.1'
    SIZEOF_UINT16 = 2

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.ipChangeLock = threading.Lock()

        self.app = app
        self.thread = thread
        self.checkIP = checkParamIP.CheckIP()
        self.settingsChanged = False
        self.remotePort = 0
        self.tcpServer = None
        self.clientConnection = None

    def initConfig(self):
        try:
            if 'RemotePort' in self.app.config:
                self.app.ui.le_remotePort.setText(self.app.config['RemotePort'])
            if 'CheckRemoteAccess' in self.app.config:
                self.app.ui.checkEnableRemoteAccess.setChecked(self.app.config['CheckRemoteAccess'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.setPort()
        self.app.ui.checkEnableRemoteAccess.stateChanged.connect(lambda: self.enableDisableRemoteAccess())
        # setting changes in gui on false, because the set of the config changed them already
        self.settingsChanged = False
        self.app.ui.le_remotePort.textChanged.connect(self.setPort)
        self.app.ui.le_remotePort.editingFinished.connect(self.enableDisableRemoteAccess)

    def storeConfig(self):
        self.app.config['RemotePort'] = self.app.ui.le_remotePort.text()
        self.app.config['CheckRemoteAccess'] = self.app.ui.checkEnableRemoteAccess.isChecked()

    def changedRemoteConnectionSettings(self):
        print('indi restart')
        if self.settingsChanged:
            print('changed')
            self.settingsChanged = False
            self.app.messageQueue.put('Setting IP address/port for remote access: {0}\n'.format(self.remotePort))
            if self.app.ui.checkEnableRemoteAccess.isChecked():
                self.ipChangeLock.acquire()
                self.stop()
                time.sleep(0.2)
                self.app.threadRemote.start()
                self.ipChangeLock.release()

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_remotePort)
        if valid:
            self.remotePort = value

    def enableDisableRemoteAccess(self):
        if self.app.ui.checkEnableRemoteAccess.isChecked():
            self.app.messageQueue.put('Remote Access enabled\n')
            self.app.threadRemote.start()
            # waiting to tcp server to start otherwise no setup for remote
            while not self.tcpServer:
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
        else:
            self.app.messageQueue.put('Remote Access disabled\n')
            if self.isRunning:
                self.stop()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop
        if not self.isRunning:
            self.isRunning = True
        result = 0
        testPortSocket = None
        try:
            testPortSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = testPortSocket.connect_ex((self.TCP_IP, self.remotePort))
        except Exception as e1:
            self.logger.warning('Error in socket {0}'.format(e1))
        finally:
            if testPortSocket:
                testPortSocket.close()
            if result == 0:
                portFree = False
            else:
                portFree = True
        if portFree:
            # there is no other listening socket
            self.tcpServer = PyQt5.QtNetwork.QTcpServer(self)
            self.tcpServer.listen(PyQt5.QtNetwork.QHostAddress(self.TCP_IP), self.remotePort)
            self.logger.info('MountWizzard started listening on port {0}'.format(self.remotePort))
            self.tcpServer.newConnection.connect(self.addConnection)
        else:
            self.logger.warning('port {0} is already in use'.format(self.remotePort))

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.tcpServer.close()
        self.tcpServer = None
        self.clientConnection = None
        self.logger.info('MountWizzard Remote Server is shut down'.format(self.remotePort))
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.thread.quit()
        self.thread.wait()

    def addConnection(self):
        self.clientConnection = self.tcpServer.nextPendingConnection()
        self.clientConnection.nextBlockSize = 0
        self.clientConnection.readyRead.connect(self.receiveMessage)
        self.clientConnection.disconnected.connect(self.removeConnection)
        self.clientConnection.error.connect(self.socketError)
        self.logger.info('Connection to MountWizzard from {0}'.format(self.clientConnection.peerAddress().toString()))

    def receiveMessage(self):
        if self.clientConnection.bytesAvailable() > 0:
            message = str(self.clientConnection.read(100), "ascii")
            if message == 'shutdown\r\n':
                self.logger.info('Shutdown MountWizzard from {0}'.format(self.clientConnection.peerAddress().toString()))
                self.signalRemoteShutdown.emit(True)

    def removeConnection(self):
        self.logger.info('Connection to MountWizzard from {0} removed'.format(self.clientConnection.peerAddress().toString()))

    def socketError(self):
        self.logger.error('Connection to MountWizzard from {0} failed'.format(self.clientConnection.peerAddress().toString()))
