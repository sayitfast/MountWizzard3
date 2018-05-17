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
from baseclasses import checkIP


class Remote(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalRemoteConnected = PyQt5.QtCore.pyqtSignal(bool, name='RemoteConnected')
    signalRemoteShutdown = PyQt5.QtCore.pyqtSignal(bool, name='RemoteShutdown')
    TCP_IP = '127.0.0.1'
    SIZEOF_UINT16 = 2

    CYCLE = 500
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexIPChanged = PyQt5.QtCore.QMutex()

        self.app = app
        self.thread = thread
        self.checkIP = checkIP.CheckIP()
        self.settingsChanged = False
        self.cycleTimer = None
        self.data = dict()
        self.data['RemotePort'] = 0
        self.data['RemoteIP'] = '127.0.0.1'
        self.tcpServer = None
        self.clientConnection = None
        # signal slot
        self.app.ui.le_remotePort.textChanged.connect(self.setPort)
        self.app.ui.le_remotePort.editingFinished.connect(self.enableDisableRemoteAccess)
        self.app.ui.checkEnableRemoteAccess.stateChanged.connect(self.enableDisableRemoteAccess)

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
        # setting changes in gui on false, because the set of the config changed them already
        self.settingsChanged = True
        self.changedRemoteConnectionSettings()

    def storeConfig(self):
        self.app.config['RemotePort'] = self.app.ui.le_remotePort.text()
        self.app.config['CheckRemoteAccess'] = self.app.ui.checkEnableRemoteAccess.isChecked()

    def changedRemoteConnectionSettings(self):
        if self.settingsChanged:
            self.settingsChanged = False
            if self.app.ui.checkEnableRemoteAccess.isChecked():
                # stopping thread
                self.mutexIPChanged.lock()
                self.stop()
                # change to new values
                valid, value = self.checkIP.checkPort(self.app.ui.le_remotePort)
                if valid:
                    self.data['RemotePort'] = value
                self.app.threadRemote.start()
                self.mutexIPChanged.unlock()
                self.app.messageQueue.put('Setting IP address/port for remote access: {0}\n'.format(self.data['RemotePort']))

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_remotePort)
        self.settingsChanged = (self.data['RemotePort'] != value)

    def enableDisableRemoteAccess(self):
        if self.app.ui.checkEnableRemoteAccess.isChecked():
            self.app.messageQueue.put('Remote Access enabled\n')
            if not self.isRunning:
                self.app.threadRemote.start()
            # waiting to tcp server to start otherwise no setup for remote
            while not self.tcpServer:
                time.sleep(0.2)
        else:
            self.app.messageQueue.put('Remote Access disabled\n')
            if self.isRunning:
                while not self.tcpServer.isListening():
                    time.sleep(0.2)
                self.stop()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop
        self.logger.info('remote started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.tcpServer = PyQt5.QtNetwork.QTcpServer(self)
        if not self.tcpServer.listen(PyQt5.QtNetwork.QHostAddress(self.data['RemoteIP']), self.data['RemotePort']):
            self.logger.warning('port {0} is already in use'.format(self.data['RemotePort']))
            self.mutexIsRunning.lock()
            self.isRunning = False
            self.mutexIsRunning.unlock()
        else:
            self.logger.info('MountWizzard started listening on port {0}'.format(self.data['RemotePort']))
            self.tcpServer.newConnection.connect(self.addConnection)

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
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('MountWizzard Remote Server is shut down'.format(self.data['RemotePort']))
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.logger.info('remote stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)
        self.tcpServer.newConnection.disconnect(self.addConnection)
        self.tcpServer.close()
        if self.clientConnection:
            self.clientConnection.close()
        self.tcpServer = None
        self.clientConnection = None

    def doCommand(self):
        pass

    @PyQt5.QtCore.pyqtSlot()
    def addConnection(self):
        self.clientConnection = self.tcpServer.nextPendingConnection()
        self.clientConnection.nextBlockSize = 0
        self.clientConnection.readyRead.connect(self.receiveMessage)
        self.clientConnection.disconnected.connect(self.removeConnection)
        self.clientConnection.error.connect(self.socketError)
        self.logger.info('Connection to MountWizzard from {0}'.format(self.clientConnection.peerAddress().toString()))

    @PyQt5.QtCore.pyqtSlot()
    def receiveMessage(self):
        if self.clientConnection.bytesAvailable() > 0:
            message = str(self.clientConnection.read(100), "ascii")
            if message == 'shutdown\r\n':
                self.logger.info('Shutdown MountWizzard from {0}'.format(self.clientConnection.peerAddress().toString()))
                self.signalRemoteShutdown.emit(True)

    @PyQt5.QtCore.pyqtSlot()
    def removeConnection(self):
        self.clientConnection.close()
        self.logger.info('Connection to MountWizzard from {0} removed'.format(self.clientConnection.peerAddress().toString()))

    def socketError(self, socketError):
        self.logger.error('Connection to MountWizzard from {0} failed'.format(self.clientConnection.peerAddress().toString()))
