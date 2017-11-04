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
import socket


class Remote(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    signalRemoteConnected = PyQt5.QtCore.pyqtSignal(bool, name='RemoteConnected')
    signalRemoteShutdown = PyQt5.QtCore.pyqtSignal(bool, name='RemoteShutdown')
    TCP_IP = '127.0.0.1'
    BUFFER_SIZE = 20                                                                                                        # Normally 1024, but we want fast response

    def __init__(self, app):
        super().__init__()
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()

        self.app = app
        self.remotePort = 0
        self.tcpServer = None
        self.clientConnection = None
        self.initConfig()
        self.app.ui.le_remotePort.textChanged.connect(self.setRemotePort)

    def initConfig(self):
        try:
            if 'RemotePort' in self.app.config:
                self.app.ui.le_remotePort.setText(self.app.config['RemotePort'])
            if 'CheckRemoteAccess' in self.config:
                self.app.ui.checkRemoteAccess.setChecked(self.app.config['CheckRemoteAccess'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            self.setRemotePort()

    def storeConfig(self):
        self.app.config['RemotePort'] = self.app.ui.le_remotePort.Text()
        self.app.config['CheckRemoteAccess'] = self.app.ui.checkRemoteAccess.isChecked()

    def setRemotePort(self):
        if self.app.ui.le_remotePort.text().strip() != '':
            self.remotePort = int(self.app.ui.le_remotePort.text())
        else:
            self.logger.warning('empty input value for remote port')
            self.app.messageQueue.put('No remote port configured')

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop
        print('start remote')
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
        while self.isRunning:
            PyQt5.QtWidgets.QApplication.processEvents()  # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        print('stop remote')
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def addConnection(self):
        self.clientConnection = self.tcpServer.nextPendingConnection()
        self.clientConnection.nextBlockSize = 0
        self.clientConnection.readyRead.connect(self.receiveMessage)
        self.clientConnection.disconnected.connect(self.removeConnection)
        self.clientConnection.error.connect(self.socketError)
        self.logger.info('Connection to MountWizzard from {0}'.format(self.clientConnection))

    def receiveMessage(self):
        if self.clientConnection.bytesAvailable() > 0:
            stream = PyQt5.QtNetwork.QDataStream(self.clientConnection)
            stream.setVersion(PyQt5.QtNetwork.QDataStream.Qt_4_2)
            if self.clientConnection.nextBlockSize == 0:
                if self.clientConnection.bytesAvailable() < PyQt5.QtNetwork.SIZEOF_UINT32:
                    return
                self.clientConnection.nextBlockSize = stream.readUInt32()
            if self.clientConnection.bytesAvailable() < self.clientConnection.nextBlockSize:
                return
            textFromClient = stream.readQString()
            if textFromClient == 'shutdown':
                self.logger.info('Shutdown MountWizzard from {0}'.format(self.clientConnection))
                self.signalRemoteShutdown.emit(True)
            self.clientConnection.nextBlockSize = 0
            self.sendMessage(textFromClient, self.clientConnection.socketDescriptor())
            self.clientConnection.nextBlockSize = 0

    def removeConnection(self):
        pass

    def socketError(self):
        pass
