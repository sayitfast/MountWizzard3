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


class MountStatusRunnerOnce(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, data, signalConnected):
        super().__init__()

        self.app = app
        self.data = data
        self.signalConnected = signalConnected
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
        while self.socket.state() != 0:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def handleHostFound(self):
        pass
        # self.logger.info('Mount RunnerOnce found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.connected = True
        self.signalConnected.emit({'Once': True})
        self.getStatusOnce()
        self.logger.info('Mount RunnerOnce connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount RunnerOnce connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        pass
        # self.logger.info('Mount RunnerOnce connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount RunnerOnce connection is disconnected from host')
        self.signalConnected.emit({'Once': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket RunnerOnce not connected')

    def getStatusOnce(self):
        self.sendCommandQueue.put(':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#')

    def handleReadyRead(self):
        messageToProcess = ''
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(4000), "ascii")
            self.messageString += tmp
            if len(self.messageString.strip('#').split('#')) != 8:
                return
            else:
                messageToProcess = self.messageString
                self.messageString = ''
        # now transfer the model data
        try:
            if len(messageToProcess) == 0:
                return
            valueList = messageToProcess.strip('#').split('#')
            # +0580.9#-011:42:17.3#+48:02:01.6#Oct 25 2017#2.15.8#10micron GM1000HPS#16:58:31#Q-TYPE2012#
            # all parameters are delivered
            if len(valueList) == 8:
                if len(valueList[0]) > 0:
                    self.data['SiteHeight'] = valueList[0]
                if len(valueList[1]) > 0:
                    lon1 = valueList[1]
                    # due to compatibility to LX200 protocol east is negative
                    if lon1[0] == '-':
                        self.data['SiteLongitude'] = lon1.replace('-', '+')
                    else:
                        self.data['SiteLongitude'] = lon1.replace('+', '-')
                if len(valueList[2]) > 0:
                    self.data['SiteLatitude'] = valueList[2]
                if len(valueList[3]) > 0:
                    self.data['FirmwareDate'] = valueList[3]
                if len(valueList[4]) > 0:
                    self.data['FirmwareNumber'] = valueList[4]
                    fw = self.data['FirmwareNumber'].split('.')
                    if len(fw) == 3:
                        self.data['FW'] = int(float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
                    else:
                        self.data['FW'] = 0
                if len(valueList[5]) > 0:
                    self.data['FirmwareProductName'] = valueList[5]
                if len(valueList[6]) > 0:
                    self.data['FirmwareTime'] = valueList[6]
                if len(valueList[7]) > 0:
                    self.data['HardwareVersion'] = valueList[7]
                self.logger.info('FW: {0} Number: {1}'.format(self.data['FirmwareNumber'], self.data['FW']))
                self.logger.info('Site Lon:    {0}'.format(self.data['SiteLongitude']))
                self.logger.info('Site Lat:    {0}'.format(self.data['SiteLatitude']))
                self.logger.info('Site Height: {0}'.format(self.data['SiteHeight']))
            else:
                self.logger.warning('Parsing Status Once combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            pass
        finally:
            pass
