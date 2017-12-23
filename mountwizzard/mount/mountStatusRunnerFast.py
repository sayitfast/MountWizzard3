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


class MountStatusRunnerFast(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLE_STATUS_FAST = 100

    def __init__(self, app, data, signalConnected, signalMountAzAltPointer):
        super().__init__()

        self.app = app
        self.data = data
        self.signalConnected = signalConnected
        self.signalMountAzAltPointer = signalMountAzAltPointer
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.counter = 0
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = self.app.transform

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = PyQt5.QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        while self.isRunning:
            if not self.sendCommandQueue.empty() and self.connected:
                command = self.sendCommandQueue.get()
                self.sendCommand(command)
            time.sleep(0.2)
            self.socket.state()
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
                self.sendCommandQueue.queue.clear()
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.finished.emit()

    def handleHostFound(self):
        pass
        # self.logger.info('Mount RunnerFast found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.connected = True
        self.signalConnected.emit({'Fast': True})
        self.getStatusFast()
        self.logger.info('Mount RunnerFast connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerFast connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount RunnerFast connection has state: {0}'.format(self.socket.state()))

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
        if len(self.messageString) < 71:
            return
        else:
            messageToProcess = self.messageString[:71]
            self.messageString = self.messageString[71:]
        # Try and parse the message. In Fast we ask for GS and Ginfo so we expect 2
        try:
            if len(messageToProcess) == 0:
                return
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
                            self.signalMountAzAltPointer.emit(self.data['Az'], self.data['Alt'])
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
            if self.isRunning:
                PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS_FAST, self.getStatusFast)

