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
import copy
from queue import Queue
from astrometry import transform


class MountGetAlignmentModel(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
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
        self.isRunning = False
        self.connectCounter = 0
        self.numberRequestedAlignmentStars = 0
        self.socket = None
        self.sendLock = False
        self.cycleTimer = None
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
        if not self.sendCommandQueue.empty() and (self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState):
            command = self.sendCommandQueue.get()
            if not self.sendLock:
                self.sendCommand(command)

    def doReconnect(self):
        # to get order in connections, we wait for first connecting the Slow type
        if self.mountStatus['Slow'] and self.data['FW'] > 0:
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
        self.logger.info('{0} connected at {1}:{2}'.format(__name__, self.data['MountIP'], self.data['MountPort']))
        # todo: where to call it once at start up best ?
        self.getAlignmentModel()

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('{0} connection fault: {1}'.format(__name__, socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('{0} has state: {1}'.format(__name__, self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount GetAlignmentModel connection is disconnected from host')
        self.signalConnected.emit({__name__: False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.sendLock = True
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket GetAlignmentModel not connected')

    def getAlignmentModel(self):
        # asking for all model names
        if 'NumberAlignmentStars' in self.data:
            command = ''
            self.numberRequestedAlignmentStars = copy.copy(self.data['NumberAlignmentStars'])
            self.app.sharedMountDataLock.lockForWrite()
            self.data['ModelLoading'] = True
            self.app.sharedMountDataLock.unlock()
            # asking for all points data
            for i in range(1, self.numberRequestedAlignmentStars + 1):
                command += (':getalp{0:d}#'.format(i))
            if self.data['FW'] >= 21500:
                command += ':getain#'
            self.sendCommandQueue.put(command)

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # we have a firmware dependency
        self.app.sharedMountDataLock.lockForRead()
        if self.data['FW'] < 21500:
            numberResults = self.numberRequestedAlignmentStars
        else:
            numberResults = self.numberRequestedAlignmentStars + 1
        self.app.sharedMountDataLock.unlock()
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(4000).decode()
        if self.messageString.count('#') != numberResults:
            if self.messageString.count('#') > numberResults:
                self.logger.error('Receiving data got error:{0}'.format(self.messageString))
                messageToProcess = self.messageString
                self.messageString = ''
            else:
                # go on receiving data
                return
        else:
            messageToProcess = self.messageString
            self.messageString = ''
        # now transfer the model data
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            self.logger.info('Raw data from Mount: {0}'.format(messageToProcess))
            valueList = messageToProcess.strip('#').split('#')
            # now the first part of the command cluster
            self.data['ModelIndex'] = list()
            self.data['ModelAzimuth'] = list()
            self.data['ModelAltitude'] = list()
            self.data['ModelError'] = list()
            self.data['ModelErrorAngle'] = list()
            # we start every time with index 0, because if the first parsing took place, the first list element will be deleted
            self.logger.info('Align info points data: {0}'.format(valueList))
            for i in range(0, len(valueList) - 1):
                values = valueList[i].split(',')
                ha = values[0]
                dec = values[1]
                ErrorRMS = float(values[2])
                ErrorAngle = float(values[3])
                dec = dec.replace('*', ':')
                RaJNow = self.transform.degStringToDecimal(ha)
                DecJNow = self.transform.degStringToDecimal(dec)
                az, alt = self.transform.topocentricToAzAlt(RaJNow, DecJNow)
                # index should start with 0, but numbering in mount starts with 1
                self.data['ModelIndex'].append(i)
                self.data['ModelAzimuth'].append(az)
                self.data['ModelAltitude'].append(alt)
                self.data['ModelError'].append(ErrorRMS)
                self.data['ModelErrorAngle'].append(ErrorAngle)

            # now the second part of the command cluster
            if self.data['FW'] > 21500:
                self.logger.info('Align info data: {0}'.format(valueList[numberResults - 1]))
                # here we have more data in
                if len(valueList[numberResults - 1].split(',')) == 1:
                    valueList[numberResults - 1] = 'E,E,E,E,E,E,E,E,E'
                if len(valueList[numberResults - 1].split(',')) != 9:
                    valueList[numberResults - 1] = 'E,E,E,E,E,E,E,E,E'
                    self.logger.error('Receive error getain command content: {0}'.format(valueList[0]))

                a1, a2, a3, a4, a5, a6, a7, a8, a9 = valueList[numberResults - 1].split(',')
                # 'E' could be sent if not calculable or no value available
                if a1 != 'E':
                    self.data['ModelErrorAzimuth'] = float(a1)
                else:
                    self.data['ModelErrorAzimuth'] = 0
                if a2 != 'E':
                    self.data['ModelErrorAltitude'] = float(a2)
                else:
                    self.data['ModelErrorAltitude'] = 0
                if a3 != 'E':
                    self.data['PolarError'] = float(a3)
                else:
                    self.data['PolarError'] = 0
                if a4 != 'E':
                    self.data['PosAngle'] = float(a4)
                else:
                    self.data['PosAngle'] = 0
                if a5 != 'E':
                    self.data['OrthoError'] = float(a5)
                else:
                    self.data['OrthoError'] = 0
                if a6 != 'E':
                    self.data['AzimuthKnobs'] = float(a6)
                else:
                    self.data['AzimuthKnobs'] = 0
                if a7 != 'E':
                    self.data['AltitudeKnobs'] = float(a7)
                else:
                    self.data['AltitudeKnobs'] = 0
                if a8 != 'E':
                    self.data['Terms'] = int(a8)
                else:
                    self.data['Terms'] = 0
                if a9 != 'E':
                    self.data['RMS'] = float(a9)
                else:
                    self.data['RMS'] = 0
                self.data['ModelRMSError'] = '{0:3.1f}'.format(self.data['RMS'])
                self.data['ModelErrorPosAngle'] = '{0:3.1f}'.format(self.data['PosAngle'])
                self.data['ModelPolarError'] = '{0}'.format(self.transform.decimalToDegree(self.data['PolarError']))
                self.data['ModelOrthoError'] = '{0}'.format(self.transform.decimalToDegree(self.data['OrthoError']))
                self.data['ModelErrorAz'] = '{0}'.format(self.transform.decimalToDegree(self.data['ModelErrorAzimuth']))
                self.data['ModelErrorAlt'] = '{0}'.format(self.transform.decimalToDegree(self.data['ModelErrorAltitude']))
                self.data['ModelTerms'] = '{0:2d}'.format(self.data['Terms'])
                if self.data['AzimuthKnobs'] > 0:
                    value = '{0:2.2f} left'.format(abs(self.data['AzimuthKnobs']))
                else:
                    value = '{0:2.2f} right'.format(abs(self.data['AzimuthKnobs']))
                self.data['ModelKnobTurnAz'] = '{0}'.format(value)
                if self.data['AltitudeKnobs'] > 0:
                    value = '{0:2.2f} down'.format(abs(self.data['AltitudeKnobs']))
                else:
                    value = '{0:2.2f} up'.format(abs(self.data['AltitudeKnobs']))
                self.data['ModelKnobTurnAlt'] = '{0}'.format(value)

        except Exception as e:
            self.logger.error('Parsing GetAlignmentModel got error:{0}, values:{1}'.format(e, messageToProcess))
        finally:
            self.app.sharedMountDataLock.unlock()
            self.app.workerMountDispatcher.signalMountShowAlignmentModel.emit()
        self.data['ModelLoading'] = False
        self.sendLock = False
