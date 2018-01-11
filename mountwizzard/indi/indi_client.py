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
import time
import threading
from xml.etree import ElementTree
import PyQt5
from PyQt5 import QtCore, QtNetwork, QtWidgets
import indi.indi_xml as indiXML
import astropy.io.fits as pyfits
from baseclasses import checkParamIP


class INDIClient(PyQt5.QtCore.QObject):
    finished = PyQt5.QtCore.pyqtSignal()
    logger = logging.getLogger(__name__)
    received = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(int)
    statusCCD = QtCore.pyqtSignal(bool)
    statusFilter = QtCore.pyqtSignal(bool)
    statusTelescope = QtCore.pyqtSignal(bool)
    statusWeather = QtCore.pyqtSignal(bool)

    GENERAL_INTERFACE = 0
    TELESCOPE_INTERFACE = (1 << 0)
    CCD_INTERFACE = (1 << 1)
    GUIDER_INTERFACE = (1 << 2)
    FOCUSER_INTERFACE = (1 << 3)
    FILTER_INTERFACE = (1 << 4)
    DOME_INTERFACE = (1 << 5)
    GPS_INTERFACE = (1 << 6)
    WEATHER_INTERFACE = (1 << 7)
    AO_INTERFACE = (1 << 8)
    DUSTCAP_INTERFACE = (1 << 9)
    LIGHTBOX_INTERFACE = (1 << 10)
    DETECTOR_INTERFACE = (1 << 11)
    AUX_INTERFACE = (1 << 15)

    data = {
        'ServerIP': '',
        'ServerPort': 7624,
        'Connected': False,
        'Device': {}
    }

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.isRunning = False
        self.ipChangeLock = threading.Lock()
        self._mutex = PyQt5.QtCore.QMutex()
        self.checkIP = checkParamIP.CheckIP()
        self.socket = None
        self.settingsChanged = False
        self.receivedImage = False
        self.imagePath = ''
        self.messageString = ''

    def initConfig(self):
        try:
            if 'INDIServerPort' in self.app.config:
                self.app.ui.le_INDIServerPort.setText(self.app.config['INDIServerPort'])
            if 'INDIServerIP' in self.app.config:
                self.app.ui.le_INDIServerIP.setText(self.app.config['INDIServerIP'])
            if 'CheckEnableINDI' in self.app.config:
                self.app.ui.checkEnableINDI.setChecked(self.app.config['CheckEnableINDI'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.setIP()
        self.setPort()
        # have to choose lambda to get the right threading context
        self.app.ui.checkEnableINDI.stateChanged.connect(lambda: self.enableDisableINDI())
        # setting changes in gui on false, because the set of the config changed them already
        self.settingsChanged = False
        self.app.ui.le_INDIServerIP.textChanged.connect(self.setIP)
        self.app.ui.le_INDIServerIP.editingFinished.connect(self.changedINDIClientConnectionSettings)
        self.app.ui.le_INDIServerPort.textChanged.connect(self.setPort)
        self.app.ui.le_INDIServerPort.editingFinished.connect(self.changedINDIClientConnectionSettings)
        self.status.emit(0)

    def storeConfig(self):
        self.app.config['INDIServerPort'] = self.app.ui.le_INDIServerPort.text()
        self.app.config['INDIServerIP'] = self.app.ui.le_INDIServerIP.text()
        self.app.config['CheckEnableINDI'] = self.app.ui.checkEnableINDI.isChecked()

    def changedINDIClientConnectionSettings(self):
        if self.settingsChanged:
            self.settingsChanged = False
            self.app.messageQueue.put('Setting IP address/port for INDI client: {0}:{1}\n'.format(self.data['ServerIP'], self.data['ServerPort']))
            if self.app.ui.checkEnableINDI.isChecked():
                self.ipChangeLock.acquire()
                self.stop()
                time.sleep(1)
                self.app.threadINDI.start()
                self.ipChangeLock.release()

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_INDIServerPort)
        self.settingsChanged = (self.data['ServerPort'] != value)
        if valid:
            self.data['ServerPort'] = value

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_INDIServerIP)
        self.settingsChanged = (self.data['ServerIP'] != value)
        if valid:
            self.data['ServerIP'] = value

    def enableDisableINDI(self):
        if self.app.ui.checkEnableINDI.isChecked():
            if not self.isRunning:
                self.app.threadINDI.start()
        else:
            if self.isRunning:
                self.stop()

    def run(self):
        if not self.isRunning:
            self.isRunning = True
        self.socket = QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.connectToHost(self.data['ServerIP'], self.data['ServerPort'])
        self.received.connect(self.handleReceived)
        while self.isRunning:
            time.sleep(0.2)
            if not self.app.INDICommandQueue.empty():
                indi_command = self.app.INDICommandQueue.get()
                self.sendMessage(indi_command)
            QtWidgets.QApplication.processEvents()
            if not self.data['Connected'] and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.data['ServerIP'], self.data['ServerPort'])
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()
        # todo handle INDI disconnect as well to tell the server, that we are out
        # wait for the disconnect from host happen
        while self.socket.state() != 0:
            time.sleep(0.1)
            QtWidgets.QApplication.processEvents()
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def handleHostFound(self):
        pass

    def handleConnected(self):
        self.data['Connected'] = True
        self.logger.info('INDI Server connected at {0}:{1}'.format(self.data['ServerIP'], self.data['ServerPort']))
        self.app.INDICommandQueue.put(indiXML.clientGetProperties(indi_attr={'version': '1.0'}))

    def handleError(self, socketError):
        self.logger.error('INDI connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.status.emit(self.socket.state())

    def handleDisconnect(self):
        self.logger.info('INDI client connection is disconnected from host')
        self.data['Connected'] = False
        self.data['Device'] = {}
        self.statusCCD.emit(False)
        self.statusFilter.emit(False)
        self.statusTelescope.emit(False)
        self.statusWeather.emit(False)
        self.app.INDIStatusQueue.put({'Name': 'Weather', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'CCD', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'Telescope', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'Filter', 'value': '---'})

    def handleReceived(self, message):
        # central dispatcher for data coming from INDI devices. I makes the whole status and data evaluation and fits the
        # data to mountwizzard

        device = message.attr['device']

        # receiving all definitions for vectors in indi and building them up in self.data['Device']
        if isinstance(message, indiXML.DefBLOBVector):
            if device not in self.data['Device']:
                self.data['Device'][device] = {}
            if device in self.data['Device']:
                if 'name' in message.attr:
                    defVector = message.attr['name']
                    if defVector not in self.data['Device'][device]:
                        self.data['Device'][device][defVector] = {}
                    for elt in message.elt_list:
                        self.data['Device'][device][defVector][elt.attr['name']] = ''

        elif isinstance(message, indiXML.SetBLOBVector):
            if device in self.data['Device']:
                if int(self.data['Device'][device]['DRIVER_INFO']['DRIVER_INTERFACE']) & self.CCD_INTERFACE:
                    name = message.attr['name']
                    if name == 'CCD1':
                        if 'format' in message.getElt(0).attr:
                            if message.getElt(0).attr['format'] == '.fits':
                                imageHDU = pyfits.HDUList.fromstring(message.getElt(0).getValue())
                                imageHDU.writeto(self.imagePath)
                                self.logger.info('image file is in raw fits format')
                            else:
                                self.logger.info('image file is not in raw fits format')
                            self.receivedImage = True

        # deleting properties from devices
        elif isinstance(message, indiXML.DelProperty):
            if device in self.data['Device']:
                if 'name' in message.attr:
                    delVector = message.attr['name']
                    if delVector in self.data['Device'][device]:
                        del self.data['Device'][device][delVector]

        # receiving changes from vectors and updating them ins self.data['Device]
        elif isinstance(message, indiXML.SetSwitchVector) or \
                isinstance(message, indiXML.SetTextVector) or \
                isinstance(message, indiXML.SetLightVector) or \
                isinstance(message, indiXML.SetNumberVector):
            if device in self.data['Device']:
                if 'name' in message.attr:
                    setVector = message.attr['name']
                    if setVector not in self.data['Device'][device]:
                        self.data['Device'][device][setVector] = {}
                        self.logger.error('Unknown SetVector in INDI protocol, device: {0}, vector: {1}'.format(device, setVector))
                    for elt in message.elt_list:
                        self.data['Device'][device][setVector][elt.attr['name']] = elt.getValue()

        # receiving all definitions for vectors in indi and building them up in self.data['Device']
        elif isinstance(message, indiXML.DefSwitchVector) or \
                isinstance(message, indiXML.DefTextVector) or \
                isinstance(message, indiXML.DefLightVector) or \
                isinstance(message, indiXML.DefNumberVector):
            if device not in self.data['Device']:
                self.data['Device'][device] = {}
            if device in self.data['Device']:
                if 'name' in message.attr:
                    defVector = message.attr['name']
                    if defVector not in self.data['Device'][device]:
                        self.data['Device'][device][defVector] = {}
                    for elt in message.elt_list:
                        self.data['Device'][device][defVector][elt.attr['name']] = elt.getValue()

        if device in self.data['Device']:
            # now place the information about accessible devices in the gui and set the connection status
            if 'DRIVER_INFO' in self.data['Device'][device]:
                if int(self.data['Device'][device]['DRIVER_INFO']['DRIVER_INTERFACE']) & self.CCD_INTERFACE:
                    self.app.INDIStatusQueue.put({'Name': 'CCD', 'value': device})
                    # make a shortcut for later use and knowing which is a Camera
                    self.data['Camera'] = self.data['Device'][device]
                    self.data['Camera']['DriverName'] = device
                    if 'CONNECTION' in self.data['Device'][device]:
                        self.statusCCD.emit(self.data['Device'][device]['CONNECTION']['CONNECT'] == 'On')
                elif int(self.data['Device'][device]['DRIVER_INFO']['DRIVER_INTERFACE']) & self.TELESCOPE_INTERFACE:
                    self.app.INDIStatusQueue.put({'Name': 'Telescope', 'value': device})
                    # make a shortcut for later use
                    self.data['Telescope'] = self.data['Device'][device]
                    if 'CONNECTION' in self.data['Device'][device]:
                        self.statusTelescope.emit(self.data['Device'][device]['CONNECTION']['CONNECT'] == 'On')
                elif int(self.data['Device'][device]['DRIVER_INFO']['DRIVER_INTERFACE']) & self.FILTER_INTERFACE:
                    self.app.INDIStatusQueue.put({'Name': 'Filter', 'value': device})
                    # make a shortcut for later use
                    self.data['Filter'] = self.data['Device'][device]
                    if 'CONNECTION' in self.data['Device'][device]:
                        self.statusFilter.emit(self.data['Device'][device]['CONNECTION']['CONNECT'] == 'On')
                elif int(self.data['Device'][device]['DRIVER_INFO']['DRIVER_INTERFACE']) & self.WEATHER_INTERFACE:
                    self.app.INDIStatusQueue.put({'Name': 'Weather', 'value': device})
                    # make a shortcut for later use
                    self.data['Weather'] = self.data['Device'][device]
                    if 'CONNECTION' in self.data['Device'][device]:
                        self.statusWeather.emit(self.data['Device'][device]['CONNECTION']['CONNECT'] == 'On')

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        if len(self.messageString) == 0:
            self.messageString = "<data>"

        # Get message from socket.
        while self.socket.bytesAvailable():
            # print(self.socket.bytesAvailable())
            tmp = str(self.socket.read(1000000), "ascii")
            self.messageString += tmp

        # Add closing tag.
        self.messageString += "</data>"

        # Try and parse the message.
        try:
            messages = ElementTree.fromstring(self.messageString)
            self.messageString = ""
            for message in messages:
                xml_message = indiXML.parseETree(message)
                self.handleReceived(xml_message)

        # Message is incomplete, remove </data> and wait..
        except ElementTree.ParseError:
            self.messageString = self.messageString[:-7]

    def sendMessage(self, indi_command):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.write(indi_command.toXML() + b'\n')
            self.socket.flush()
        else:
            self.logger.warning('Socket not connected')
