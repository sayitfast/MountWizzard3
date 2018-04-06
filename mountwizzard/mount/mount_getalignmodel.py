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


class MountGetAlignmentModel(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CYCLE_COMMAND = 200

    def __init__(self, app, thread, data, signalConnected):
        super().__init__()

        self.app = app
        self.thread = thread
        self.data = data
        self.signalConnected = signalConnected
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.isRunning = False
        self.connected = False
        self.socket = None
        self.messageString = ''
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

    def run(self):
        self.logger.info('mount align started')
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
        self.doCommandQueue()

    def stop(self):
        # if I leave the loop, I close the connection to remote host
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()
        self.logger.info('mount align stopped')

    def destruct(self):
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

    def doCommandQueue(self):
        if not self.sendCommandQueue.empty() and self.connected:
            command = self.sendCommandQueue.get()
            self.sendCommand(command)
        if not self.connected and self.socket.state() == 0:
            self.app.sharedMountDataLock.lockForRead()
            self.socket.connectToHost(self.data['MountIP'], self.data['MountPort'])
            self.app.sharedMountDataLock.unlock()
            self.sendCommandQueue.queue.clear()
        # loop
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_COMMAND, self.doCommandQueue)

    def handleHostFound(self):
        self.logger.debug('Mount GetAlignmentModel found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Align': True})
        self.getAlignmentModel()
        self.logger.info('Mount GetAlignmentModel connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.warning('Mount GetAlignmentModel connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        self.logger.debug('Mount GetAlignmentModel connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount GetAlignmentModel connection is disconnected from host')
        self.signalConnected.emit({'Align': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
            else:
                self.logger.warning('Socket GetAlignmentModel not connected')

    def getAlignmentModel(self):
        self.data['ModelLoading'] = True
        if 'FW' not in self.data:
            self.data['FW'] = 0
        if self.data['FW'] < 21500:
            command = ':getalst#'
        else:
            command = ':getalst#:getain#'
        # asking for 100 points data
        for i in range(1, 102):
            command += (':getalp{0:d}#'.format(i))
        self.sendCommandQueue.put(command)

    def handleReadyRead(self):
        # Get message from socket.
        # print('handle')
        while self.socket.bytesAvailable():
            tmp = self.socket.read(4000).decode()
            self.messageString += tmp
        # if the last characters are not E#, there are more points to receive
        if not self.messageString.endswith('E#'):
            return
        else:
            messageToProcess = self.messageString
            self.messageString = ''
        while messageToProcess.endswith('E#'):
            messageToProcess = messageToProcess.rstrip('E#')
        while messageToProcess.startswith('E#'):
            messageToProcess = messageToProcess.lstrip('E#')
        # now transfer the model data
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            if 'FW' not in self.data:
                self.data['FW'] = 0
            valueList = messageToProcess.strip('#').split('#')
            # now the first part of the command cluster
            numberStars = int(float(valueList[0]))
            self.data['NumberAlignmentStars'] = numberStars
            self.data['Number'] = numberStars
            del valueList[0]
            if numberStars < 3:
                valueList = ['E,E,E,E,E,E,E,E,E']
            # now the second part of the command cluster. it is related to firmware feature
            if self.data['FW'] > 21500:
                if numberStars < 3:
                    valueList = ['E,E,E,E,E,E,E,E,E']
                # here we have more data in
                if len(valueList[0]) > 3:
                    a1, a2, a3, a4, a5, a6, a7, a8, a9 = valueList[0].split(',')
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
                        self.data['Terms'] = int(float(a8))
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
                else:
                    self.logger.error('Receive error getain command content: {0}'.format(valueList[0]))
                # remove the first remaining element in list if it was there
                del valueList[0]
            # now the third part of the command cluster
            self.data['ModelIndex'] = list()
            self.data['ModelAzimuth'] = list()
            self.data['ModelAltitude'] = list()
            self.data['ModelError'] = list()
            self.data['ModelErrorAngle'] = list()
            # we start every time with index 0, because if the first parsing took place, the first list element will be deleted
            for i in range(0, len(valueList)):
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
            self.data['ModelLoading'] = False
        except Exception as e:
            self.logger.error('Parsing GetAlignmentModel got error:{0}, values:{1}'.format(e, messageToProcess))
        finally:
            self.app.sharedMountDataLock.unlock()
            self.app.workerMountDispatcher.signalMountShowAlignmentModel.emit()
