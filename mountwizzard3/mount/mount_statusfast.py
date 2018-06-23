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


class MountStatusRunnerFast(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CONNECTION_TIMEOUT = 2000
    CYCLE_STATUS_FAST = 750
    CYCLE = 250
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread, data, signalConnected, mountStatus):
        super().__init__()

        self.app = app
        self.data = data
        self.thread = thread
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
        self.audioDone = False

    def run(self):
        self.logger.info('mount fast started')
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
        self.dataTimer = PyQt5.QtCore.QTimer(self)
        self.dataTimer.setSingleShot(False)
        self.dataTimer.timeout.connect(self.getStatusFast)
        self.dataTimer.start(self.CYCLE_STATUS_FAST)
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
            self.signalConnected.emit({'Fast': False})
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('mount fast stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.disconnectFromHost()
        self.cycleTimer.stop()
        self.dataTimer.stop()
        self.socket.hostFound.disconnect(self.handleHostFound)
        self.socket.connected.disconnect(self.handleConnected)
        self.socket.stateChanged.disconnect(self.handleStateChanged)
        self.socket.disconnected.disconnect(self.handleDisconnect)
        self.socket.error.disconnect(self.handleError)
        self.socket.readyRead.disconnect(self.handleReadyRead)
        self.signalDestruct.disconnect(self.destruct)
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
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerFast found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot()
    def handleConnected(self):
        self.signalConnected.emit({'Fast': True})
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerFast connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    @PyQt5.QtCore.pyqtSlot(PyQt5.QtNetwork.QAbstractSocket.SocketError)
    def handleError(self, socketError):
        self.logger.warning('Mount RunnerFast connection fault: {0}'.format(socketError))

    @PyQt5.QtCore.pyqtSlot()
    def handleStateChanged(self):
        self.logger.debug('Mount RunnerFast connection has state: {0}'.format(self.socket.state()))

    @PyQt5.QtCore.pyqtSlot()
    def handleDisconnect(self):
        self.logger.info('Mount RunnerFast connection is disconnected from host')
        self.signalConnected.emit({'Fast': False})

    def sendCommand(self, command):
        if self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.sendLock = True
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.sendLock = False
                self.logger.warning('Socket RunnerFast not connected')

    @PyQt5.QtCore.pyqtSlot()
    def getStatusFast(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            self.sendCommandQueue.put(':U2#:GS#:Ginfo#:')

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
        if len(self.messageString) < 71:
            return
        else:
            messageToProcess = self.messageString[:71]
            self.messageString = self.messageString[71:]
        # Try and parse the message. In Fast we ask for GS and Ginfo so we expect 2
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            valueList = messageToProcess.strip('#').split('#')
            # first the GS command
            if len(valueList) == 2:
                if len(valueList[0]) > 0:
                    self.data['LocalSiderealTime'] = valueList[0].strip('#')
                # second the Ginfo
                if len(valueList[1]) > 0:
                    value = ''
                    try:
                        value = valueList[1].rstrip('#').strip().split(',')
                        if len(value) == 8:
                            self.data['RaJNow'] = float(value[0])
                            self.data['DecJNow'] = float(value[1])
                            self.data['Pierside'] = str(value[2])
                            self.data['Az'] = float(value[3])
                            self.data['Alt'] = float(value[4])
                            self.data['JulianDate'] = str(value[5])
                            self.data['Status'] = int(value[6])
                            # if stop , emit warning
                            if value[6] in ['1', '98', '99']:
                                # only emit one time !
                                if not self.audioDone:
                                    self.app.audioCommandQueue.put('MountAlert')
                                    self.app.messageQueue.put('#BRMount STOPPED - WARNING !!!\n')
                                    # stop any modeling
                                    self.app.workerModelingDispatcher.signalCancel.emit()
                                self.audioDone = True
                            else:
                                self.audioDone = False
                            # calculate if slewing stopped
                            if 'Slewing' in self.data:
                                if self.data['Slewing'] and value[7] != '1':
                                    self.app.workerMountDispatcher.signalSlewFinished.emit()
                                    self.app.audioCommandQueue.put('MountSlew')
                            self.data['Slewing'] = (value[7] == '1')
                            self.data['RaJ2000'], self.data['DecJ2000'] = self.transform.transformERFA(self.data['RaJNow'], self.data['DecJNow'], 2)
                            self.data['TelescopeRA'] = '{0}'.format(self.transform.decimalToDegree(self.data['RaJ2000'], False, False))
                            self.data['TelescopeDEC'] = '{0}'.format(self.transform.decimalToDegree(self.data['DecJ2000'], True, False))
                            self.data['TelescopeAltitude'] = '{0:03.2f}'.format(self.data['Alt'])
                            self.data['TelescopeAzimuth'] = '{0:03.2f}'.format(self.data['Az'])
                            self.data['MountStatus'] = '{0}'.format(self.data['Status'])
                            if self.data['Pierside'] == str('W'):
                                self.data['TelescopePierSide'] = 'WEST'
                            else:
                                self.data['TelescopePierSide'] = 'EAST'
                            self.app.workerMountDispatcher.signalMountAzAltPointer.emit(self.data['Az'], self.data['Alt'])
                            self.app.signalJulianDate.emit(float(self.data['JulianDate']))
                        else:
                            self.logger.warning('Ginfo command delivered wrong number of arguments: {0}'.format(value))
                    except Exception as e:
                        self.logger.error('Receive error Ginfo command: {0} reply:{1}'.format(e, value))
                    finally:
                        pass
            else:
                self.logger.warning('Parsing GS-Ginfo combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Problem parsing response, error: {0}, message:{1}'.format(e, messageToProcess))
        finally:
            self.app.sharedMountDataLock.unlock()
        self.sendLock = False
