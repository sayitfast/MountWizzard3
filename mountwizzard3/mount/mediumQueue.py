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
############################################################
import logging
import PyQt5
import time
from queue import Queue
from astrometry import transform


class MountStatusRunnerMedium(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
    CYCLE_COMMAND = 3000
    CYCLE_QUEUE = 250
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread, data, signalConnected, mountStatus):
        super().__init__()

        self.app = app
        self.thread = thread
        self.data = data
        self.signalConnected = signalConnected
        self.mountStatus = mountStatus
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.dataTimer = None
        self.cycleTimer = None
        self.isRunning = False
        self.connectCounter = 0
        self.socket = None
        self.sendLock = False
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

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
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.error.connect(self.handleError)
        # timer
        self.dataTimer = PyQt5.QtCore.QTimer(self)
        self.dataTimer.setSingleShot(False)
        self.dataTimer.timeout.connect(self.startCommand)
        self.dataTimer.start(self.CYCLE_COMMAND)
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
        self.dataTimer.stop()
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
        # to get order in connections, we wait for first connecting the Slow type
        # todo: how to make it general for all classes ?
        if self.data['FW'] > 0:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.UnconnectedState:
                if self.connectCounter == 0:
                    self.app.sharedMountDataLock.lockForRead()
                    self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                    self.app.sharedMountDataLock.unlock()
                    self.sendCommandQueue.queue.clear()
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
        self.logger.info('{0} found at {1}:{2}'.format(__name__, self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.signalConnected.emit({__name__: True})
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('{0} connected at {1}:{2}'.format(__name__, self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('{0} connection fault: {1}'.format(__name__, socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('{0} has state: {1}'.format(__name__, self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('{0} is disconnected from host'.format(__name__))
        self.signalConnected.emit({__name__: False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.sendLock = True
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket RunnerMedium not connected')

    @PyQt5.QtCore.pyqtSlot()
    def startCommand(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.app.sharedMountDataLock.lockForRead()
            if self.data['FW'] < 21500:
                self.sendCommandQueue.put(':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:modelcnt#:getalst#')
            else:
                self.sendCommandQueue.put(':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:modelcnt#:getalst#:GDUTV#')
            self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # we have a firmware dependency
        self.app.sharedMountDataLock.lockForRead()
        if self.data['FW'] < 21500:
            numberResults = 12
        else:
            numberResults = 13
        self.app.sharedMountDataLock.unlock()
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
        if self.messageString.count('#') < numberResults:
            return
        if self.messageString.count('#') != numberResults:
            self.logger.error('Receiving data got error:{0}'.format(self.messageString))
            self.messageString = ''
            messageToProcess = ''
        else:
            messageToProcess = self.messageString
            self.messageString = ''
        # Try and parse the message. In medium we expect 10 or 11
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            valueList = messageToProcess.strip('#').split('#')
            # print(valueList)
            # all parameters are delivered
            if len(valueList) >= 4:
                if len(valueList[0]) > 0:
                    self.data['SlewRate'] = valueList[0]
                if len(valueList[1]) > 0:
                    self.data['TimeToFlip'] = int(valueList[1])
                if len(valueList[2]) > 0:
                    self.data['MeridianLimitGuide'] = int(valueList[2])
                if len(valueList[3]) > 0:
                    self.data['MeridianLimitSlew'] = int(valueList[3])
                self.data['TimeToMeridian'] = int(self.data['TimeToFlip'] - self.data['MeridianLimitGuide'] / 360 * 24 * 60)
                if len(valueList[4]) > 0:
                    self.data['RefractionTemperature'] = valueList[4]
                if len(valueList[5]) > 0:
                    self.data['RefractionPressure'] = valueList[5]
                if len(valueList[6]) > 0:
                    self.data['TrackingRate'] = valueList[6]
                if len(valueList[7]) > 0:
                    self.data['TelescopeTempDEC'] = valueList[7]
                if len(valueList[8]) > 0:
                    self.data['RefractionStatus'] = valueList[8][0]
                    self.data['UnattendedFlip'] = valueList[8][1]
                    self.data['DualAxisTracking'] = valueList[8][2]
                    self.data['CurrentHorizonLimitHigh'] = valueList[8][3:]
                if len(valueList[9]) > 0:
                    self.data['CurrentHorizonLimitLow'] = valueList[2]
                if len(valueList[10]) > 0:
                    if self.data['NumberModelNames'] != int(valueList[10]):
                        # make Model list reload
                        self.app.workerMountDispatcher.signalRefreshModelNames.emit()
                    self.data['NumberModelNames'] = int(valueList[10])
                if len(valueList[11]) > 0:
                    if self.data['NumberAlignmentStars'] != int(valueList[11]):
                        # make alignment model reload
                        self.app.workerMountDispatcher.signalRefreshAlignmentModel.emit()
                    self.data['NumberAlignmentStars'] = int(valueList[11])
                if self.data['FW'] > 21500 and len(valueList[12]) > 0:
                    valid, expirationDate = valueList[12].split(',')
                    self.data['UTCDataValid'] = valid
                    self.data['UTCDataExpirationDate'] = expirationDate
                self.app.workerMountDispatcher.signalMountLimits.emit()
            else:
                self.logger.warning('Parsing Status Medium combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Problem parsing response, error: {0}, message:{1}'.format(e, messageToProcess))
        finally:
            self.app.sharedMountDataLock.unlock()
        self.sendLock = False
