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


class MountProgramAlignmentModel(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

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
        self.sendLock = False
        self.numberBytesToReceive = 0
        self.sendCommandQueue = Queue()
        self.transform = transform.Transform(self.app)

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
            if not self.sendCommandQueue.empty() and self.connected and not self.sendLock:
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
        # if I leave the loop, I close the connection to remote host
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def handleHostFound(self):
        self.logger.debug('Mount ProgramAlignmentModel found at {}:{}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleConnected(self):
        self.socket.setSocketOption(PyQt5.QtNetwork.QAbstractSocket.LowDelayOption, 1)
        self.connected = True
        self.signalConnected.emit({'Align': True})
        self.ProgramAlignmentModel()
        self.logger.info('Mount ProgramAlignmentModel connected at {0}:{1}'.format(self.data['MountIP'], self.data['MountPort']))

    def handleError(self, socketError):
        self.logger.warning('Mount ProgramAlignmentModel connection fault: {0}'.format(self.socket.errorString()))

    def handleStateChanged(self):
        self.logger.debug('Mount ProgramAlignmentModel connection has state: {0}'.format(self.socket.state()))

    def handleDisconnect(self):
        self.logger.info('Mount ProgramAlignmentModel connection is disconnected from host')
        self.signalConnected.emit({'Align': False})
        self.connected = False

    def sendCommand(self, command):
        if self.connected and self.isRunning:
            if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                self.socket.write(bytes(command + '\r', encoding='ascii'))
                self.socket.flush()
                self.sendLock = True
            else:
                self.sendLock = False
                self.logger.warning('Socket ProgramAlignmentModel not connected')

    def programAlignmentModel(self, modelingData):
        self.data['ModelLoading'] = True
        if 'FW' not in self.data:
            self.data['FW'] = 0
        if self.data['FW'] < 21500:
            return
        # start the programming
        command = ':newalig#'
        # collect all the data and transfer it
        for i in range(0, len(modelingData['Index'])):
            self.app.sharedMountDataLock.lockForRead()
            command = ':newalpt{0},{1},{2},{3},{4},{5}#'.format(self.transform.decimalToDegree(modelingData['RaJNow'][i], False, True),
                                                                self.transform.decimalToDegree(modelingData['DecJNow'][i], True, False),
                                                                modelingData['Pierside'][i],
                                                                self.transform.decimalToDegree(modelingData['RaJNowSolved'][i], False, True),
                                                                self.transform.decimalToDegree(modelingData['DecJNowSolved'][i], True, False),
                                                                self.transform.decimalToDegree(modelingData['LocalSiderealTimeFloat'][i], False, True))
            self.app.sharedMountDataLock.unlock()
            # end the programming
        command += ':endalig#'
        # we exspect E# or V# as response for each command
        self.numberBytesToReceive = 4 + 2 * len(modelingData)
        self.sendCommandQueue.put(command)

    def handleReadyRead(self):
        # Get message from socket.
        # print('handle')
        while len(self.messageString) < self.numberBytesToReceive:
            tmp = self.socket.read(1024).decode()
            self.messageString += tmp
        messageToProcess = self.messageString
        self.messageString = ''
        # now getting feedback from programming
        try:
            valueList = messageToProcess.strip('#').split('#')
            # here we have more data in
            if len(valueList[0]) == self.numberBytesToReceive / 2:
                if valueList[len(valueList) - 1] == 'V':
                    self.app.workerMountDispatcher.signalMountConnectedProgAlignSuccess.emit(True)
                else:
                    self.app.workerMountDispatcher.signalMountConnectedProgAlignSuccess.emit(False)
            else:
                self.logger.error('Receive error program alignment command content: {0}'.format(valueList[0]))
        except Exception as e:
            self.logger.error('Parsing ProgramAlignmentModel got error:{0}, values:{1}'.format(e, messageToProcess))
        finally:
            self.sendLock = False
