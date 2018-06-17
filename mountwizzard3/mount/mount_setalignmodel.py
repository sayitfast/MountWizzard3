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
import time
from queue import Queue
from astrometry import transform


class MountSetAlignmentModel(PyQt5.QtCore.QObject):
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
        self.connected = False
        self.socket = None
        self.sendLock = False
        self.cycleTimer = None
        self.result = None
        self.messageString = ''
        self.numberAlignmentPoints = 0
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

    def run(self):
        self.logger.info('mount set align started')
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
            self.signalConnected.emit({'SetAlign': False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount set align stopped')

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
        self.logger.debug('Mount SetAlignmentModel found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.connected = True
        self.signalConnected.emit({'SetAlign': True})
        self.logger.info('Mount SetAlignmentModel connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('Mount SetAlignmentModel connection fault: {0}'.format(socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount SetAlignmentModel connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount SetAlignmentModel connection is disconnected from host')
        self.signalConnected.emit({'SetAlign': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket SetAlignmentModel not connected')

    def setAlignmentModel(self, data):
        if self.data['FW'] < 20815:
            return
        # writing new model
        self.numberAlignmentPoints = len(data['Index'])
        command = ':newalig#'
        for i in range(0, self.numberAlignmentPoints):
            command += ':newalpt{0},{1},{2},{3},{4},{5}#'.format(self.transform.decimalToDegree(data['RaJNow'][i], False, True),
                                                                 self.transform.decimalToDegree(data['DecJNow'][i], True, False),
                                                                 data['Pierside'][i],
                                                                 self.transform.decimalToDegree(data['RaJNowSolved'][i], False, True),
                                                                 self.transform.decimalToDegree(data['DecJNowSolved'][i], True, False),
                                                                 self.transform.decimalToDegree(data['LocalSiderealTimeFloat'][i], False, True))
        command += ':endalig#'
        self.sendCommandQueue.put(command)

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(4000).decode()

        if self.messageString.count('#') != (self.numberAlignmentPoints + 1):
            if self.messageString.count('#') > (self.numberAlignmentPoints + 1):
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
        if len(valueList) != self.numberAlignmentPoints + 1:
            # error happened
            self.logger.error('Parsing SetAlignmentModel wrong numbers: value:{0}, points:{1}, values:{2}'.format(len(valueList), self.numberAlignmentPoints, valueList))
        # now parsing the result
        try:
            self.result = (valueList[0] == 'V')
            if valueList[0] != 'V':
                self.logger.error('Programming alignment model failed')
        except Exception as e:
            self.logger.error('Parsing SetAlignmentModel got error:{0}, values:{1}'.format(e, valueList))
        finally:
            pass
        self.sendLock = False
