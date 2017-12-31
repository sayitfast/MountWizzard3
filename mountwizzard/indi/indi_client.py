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
# """
#
# A PyQt5 (client) interface to an INDI server. This will only work
# in the context of a PyQt application.
#
# """
import logging
from xml.etree import ElementTree
import PyQt5
from PyQt5 import QtCore, QtNetwork, QtWidgets
import indi.indi_xml as indiXML
import astropy.io.fits as pyfits
from baseclasses import checkParamIP


class INDIClient(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    received = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(int)

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

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.isRunning = False
        self.device = {}
        self.message_string = ""
        self.checkIP = checkParamIP.CheckIP()
        self.socket = None
        self.INDIServerIP = ''
        self.INDIServerPort = 0
        self.driverNameCCD = ''
        self.driverNameTelescope = ''
        self.driverNameWeather = ''
        self.connected = False
        self.receivedImage = False
        self.imagePath = ''
        self.initConfig()
        self.app.ui.le_INDIServerIP.textChanged.connect(self.setIP)
        self.app.ui.le_INDIServerPort.textChanged.connect(self.setPort)
        self.received.connect(self.handleReceived)

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
            self.setIP()
            self.setPort()

    def storeConfig(self):
        self.app.config['INDIServerPort'] = self.app.ui.le_INDIServerPort.text()
        self.app.config['INDIServerIP'] = self.app.ui.le_INDIServerIP.text()
        self.app.config['CheckEnableINDI'] = self.app.ui.checkEnableINDI.isChecked()

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_INDIServerPort)
        if valid:
            self.INDIServerPort = value

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_INDIServerIP)
        if valid:
            self.INDIServerIP = value

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
        self.socket.connectToHost(self.INDIServerIP, self.INDIServerPort)
        while self.isRunning:
            if not self.app.INDICommandQueue.empty():
                indi_command = self.app.INDICommandQueue.get()
                self.sendMessage(indi_command)
            QtWidgets.QApplication.processEvents()
            if not self.connected and self.socket.state() == 0:
                self.socket.readyRead.connect(self.handleReadyRead)
                self.socket.connectToHost(self.INDIServerIP, self.INDIServerPort)
        # if I leave the loop, I close the connection to remote host
        self.socket.disconnectFromHost()

    def stop(self):
        self.isRunning = False

    def handleHostFound(self):
        pass

    def handleConnected(self):
        self.connected = True
        self.logger.info('INDI Server connected at {0}:{1}'.format(self.INDIServerIP, self.INDIServerPort))
        self.app.INDICommandQueue.put(indiXML.clientGetProperties(indi_attr={'version': '1.0'}))

    def handleError(self, socketError):
        self.logger.error('INDI connection fault: {0}, error: {1}'.format(self.socket.errorString(), socketError))

    def handleStateChanged(self):
        self.status.emit(self.socket.state())

    def handleDisconnect(self):
        self.logger.info('INDI client connection is disconnected from host')
        self.driverNameCCD = ''
        self.driverNameTelescope = ''
        self.driverNameWeather = ''
        self.connected = False
        self.app.INDIStatusQueue.put({'Name': 'Weather', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'CCD', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'Telescope', 'value': '---'})
        self.app.INDIStatusQueue.put({'Name': 'Filter', 'value': '---'})

    def handleReceived(self, message):
        # central dispatcher for data coming from INDI devices. I makes the whole status and data evaluation and fits the
        # data to mountwizzard
        if isinstance(message, indiXML.SetBLOBVector) or isinstance(message, indiXML.DefBLOBVector):
            device = message.attr['device']
            if device == self.driverNameCCD:
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

        elif isinstance(message, indiXML.DelProperty):
            device = message.attr['device']
            if device in self.device:
                if 'name' in message.attr:
                    group = message.attr['name']
                    if group in self.device[device]:
                        del self.device[device][group]
        else:
            device = message.attr['device']
            if device not in self.device:
                self.device[device] = {}
            if 'name' in message.attr:
                group = message.attr['name']
                if group not in self.device[device]:
                    self.device[device][group] = {}
                for elt in message.elt_list:
                    self.device[device][group][elt.attr['name']] = elt.getValue()

        if 'name' in message.attr:
            if message.attr['name'] == 'DRIVER_INFO':
                if message.elt_list[3].attr['name'] == 'DRIVER_INTERFACE':
                    if int(message.getElt(3).getValue()) & self.TELESCOPE_INTERFACE:
                        self.driverNameTelescope = message.getElt(0).getValue()
                        self.app.INDIStatusQueue.put({'Name': 'Telescope', 'value': message.getElt(0).getValue()})
                    elif int(message.getElt(3).getValue()) & self.CCD_INTERFACE:
                        self.driverNameCCD = message.getElt(0).getValue()
                        self.app.INDIStatusQueue.put({'Name': 'CCD', 'value': message.getElt(0).getValue()})
                    elif int(message.getElt(3).getValue()) & self.FILTER_INTERFACE:
                        self.driverNameCCD = message.getElt(0).getValue()
                        self.app.INDIStatusQueue.put({'Name': 'Filter', 'value': message.getElt(0).getValue()})
                    elif int(message.getElt(3).getValue()) == self.WEATHER_INTERFACE:
                        self.driverNameWeather = message.getElt(0).getValue()
                        self.app.INDIStatusQueue.put({'Name': 'Weather', 'value': message.getElt(0).getValue()})

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        if len(self.message_string) == 0:
            self.message_string = "<data>"

        # Get message from socket.
        while self.socket.bytesAvailable():
            # print(self.socket.bytesAvailable())
            tmp = str(self.socket.read(1000000), "ascii")
            self.message_string += tmp

        # Add closing tag.
        self.message_string += "</data>"

        # Try and parse the message.
        try:
            messages = ElementTree.fromstring(self.message_string)
            self.message_string = ""
            for message in messages:
                xml_message = indiXML.parseETree(message)
                self.handleReceived(xml_message)

        # Message is incomplete, remove </data> and wait..
        except ElementTree.ParseError:
            self.message_string = self.message_string[:-7]

    def sendMessage(self, indi_command):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.write(indi_command.toXML() + b'\n')
            self.socket.flush()
        else:
            self.logger.warning('Socket not connected')
