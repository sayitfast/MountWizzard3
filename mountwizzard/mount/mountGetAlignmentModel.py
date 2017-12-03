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
from astrometry import transform


class MountGetAlignmentModel(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    BLIND_COMMANDS = ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']

    def __init__(self, app, data, signalMountShowAlignmentModel):
        super().__init__()

        self.app = app
        self.data = data
        self.signalMountShowAlignmentModel = signalMountShowAlignmentModel
        self._mutex = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.connected = False
        self.socket = None
        self.counter = 0
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.parseQueue = Queue()

        self.transform = transform.Transform(self.app)

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
            if not self.sendCommandQueue.empty():
                command = self.sendCommandQueue.get()
                self.sendCommand(command)
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.finished.emit()

    def handleHostFound(self):
        self.logger.info('Mount found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.connected = True
        self.getAlignmentModel()
        self.logger.info('Mount connected at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.error('Mount connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.logger.info('Mount connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount connection is disconnected from host')
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
            else:
                self.logger.warning('Socket not connected')

    def getAlignmentModel(self):
        command = ''
        # asking for 100 points data
        for i in range(1, 102):
            command += (':getalp{0:d}#'.format(i))
        self.sendCommandQueue.put(command)

    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable():
            tmp = str(self.socket.read(4000), "ascii")
            self.messageString += tmp
        # if the last characters are not E#, there are more points to receive
        if self.messageString[-2:] != 'E#':
            return
        else:
            # if the start is E#, than we got all points, the rest is invalid, we copy to process an start over
            if self.messageString[:2] != 'E#':
                messageToProcess = self.messageString
                self.messageString = ''
            else:
                # if we start with E# it's the rest of an closed transfer, we just delete it
                self.messageString = ''
                messageToProcess = ''
        # Try and parse the message.
        # clear up trailing E#
        while messageToProcess[-2:] == 'E#':
            messageToProcess = messageToProcess.strip('E#')
        # now transfer the model data
        try:
            if len(messageToProcess) == 0 or 'FW' not in self.data:
                return
            valueList = messageToProcess.strip('#').split('#')
            self.data['Number'] = len(valueList)
            self.data['ModelIndex'] = list()
            self.data['ModelAzimuth'] = list()
            self.data['ModelAltitude'] = list()
            self.data['ModelError'] = list()
            self.data['ModelErrorAngle'] = list()
            for i in range(0, len(valueList)):
                values = valueList[i].split(',')
                ha = values[0]
                dec = values[1]
                ErrorRMS = float(values[2])
                ErrorAngle = float(values[3])
                dec = dec.replace('*', ':')
                RaJNow = self.transform.degStringToDecimal(ha)
                DecJNow = self.transform.degStringToDecimal(dec)
                az, alt = self.transform.ra_dec_lst_to_az_alt(RaJNow, DecJNow)
                # index should start with 0, but numbering in mount starts with 1
                self.data['ModelIndex'].append(i - 1)
                self.data['ModelAzimuth'].append(az)
                self.data['ModelAltitude'].append(alt)
                self.data['ModelError'].append(ErrorRMS)
                self.data['ModelErrorAngle'].append(ErrorAngle)
            self.signalMountShowAlignmentModel.emit()
        except Exception as e:
            self.logger.error('Parsing Get Align Model got error:{0}'.format(e))
        finally:
            pass
