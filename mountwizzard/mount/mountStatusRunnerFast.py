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

    CYCLE_STATUS_FAST = 300

    def __init__(self, app, thread, data, signalConnected):
        super().__init__()

        self.app = app
        self.data = data
        self.thread = thread
        self.signalConnected = signalConnected
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.isRunning = False
        self.connected = False
        self.socket = None
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)
        self.audioDone = False

    def run(self):
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.error.connect(self.handleError)
        while self.isRunning:
            if not self.sendCommandQueue.empty() and self.connected:
                command = self.sendCommandQueue.get()
                self.sendCommand(command)
            if not self.connected and self.socket.state() == 0:
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                self.sendCommandQueue.queue.clear()
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.socket.state() != 3:
            self.socket.abort()
        else:
            self.socket.disconnectFromHost()
        self.socket.hostFound.disconnect(self.handleHostFound)
        self.socket.connected.disconnect(self.handleConnected)
        self.socket.stateChanged.disconnect(self.handleStateChanged)
        self.socket.disconnected.disconnect(self.handleDisconnect)
        self.socket.readyRead.disconnect(self.handleReadyRead)
        self.socket.error.disconnect(self.handleError)
        self.socket.close()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def handleHostFound(self):
        self.app.sharedMountDataLock.lockForRead()
        self.logger.debug('Mount RunnerFast found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Fast': True})
        self.getStatusFast()
        self.app.sharedMountDataLock.lockForRead()
        self.logger.info('Mount RunnerFast connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))
        self.app.sharedMountDataLock.unlock()

    def handleError(self, socketError):
        self.logger.warning('Mount RunnerFast connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        self.logger.debug('Mount RunnerFast connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerFast connection is disconnected from host')
        self.signalConnected.emit({'Fast': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket RunnerFast not connected')

    def getStatusFast(self):
        self.sendCommandQueue.put(':U2#:GS#:Ginfo#:')

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(1000), "ascii")
            self.messageString += tmp
            PyQt5.QtWidgets.QApplication.processEvents()
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
                            self.data['Pierside'] = value[2]
                            self.data['Az'] = float(value[3])
                            self.data['Alt'] = float(value[4])
                            self.data['JulianDate'] = value[5]
                            self.data['Status'] = int(value[6])
                            # if stop , emit warning
                            if value[6] in ['1', '98', '99']:
                                # only emit one time !
                                if not self.audioDone:
                                    self.app.signalAudio.emit('Stop')
                                    self.app.messageQueue.put('#BR\tMOUNT STOPPED - WARNING !!!\n')
                                self.audioDone = True
                            else:
                                self.audioDone = False
                            # calculate if slewing stopped
                            if 'Slewing' in self.data:
                                if self.data['Slewing'] and value[7] != '1':
                                    self.app.workerMountDispatcher.signalSlewFinished.emit()
                                    self.app.signalAudio.emit('MountSlew')
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
                            # self.app.signalJulianDate.emit(self.data['JulianDate'])
                        else:
                            self.logger.warning('Ginfo command delivered wrong number of arguments: {0}'.format(value))
                    except Exception as e:
                        self.logger.error('Receive error Ginfo command: {0} reply:{1}'.format(e, value))
                    finally:
                        pass
            else:
                self.logger.warning('Parsing GS-Ginfo combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Parsing GS-Ginfo combined command got error:{0}'.format(e))
        finally:
            self.app.sharedMountDataLock.unlock()
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_FAST, self.getStatusFast)

