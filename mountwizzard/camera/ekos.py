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
from baseclasses.camera import MWCamera
from indi.qt_indi_client import QtINDIClient
import indi.indi_xml as indiXML
import pyfits
import PyQt5


class EKOSCamera(MWCamera):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, app):
        self.app = app
        self.appRunning = False
        self.cameraConnected = False
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = 'EKOS - INDI'
        self.appExe = ''
        self.host = '192.168.2.163'
        self.port = 7624
        self.tryConnectionCounter = 0
        self.indiClient = None
        self.indiClient = QtINDIClient()
        self.indiClient.received.connect(self.handleReceived)
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable = False

    def checkAppStatus(self):
        try:
            print('check App')
            if not self.appRunning:
                PyQt5.QtWidgets.QApplication.processEvents()
                self.indiClient.connect(self.host, self.port)
                if self.indiClient.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
                    self.tryConnectionCounter = 0
                    self.appRunning = True
                else:
                    self.tryConnectionCounter += 1
                    self.appRunning = False
                    self.cameraConnected = False
                    if self.tryConnectionCounter < 3:
                        self.logger.warning('{0} is not running'.format(self.appName))
                    elif self.tryConnectionCounter == 3:
                        self.logger.error('No connection to {0} possible - stop logging this connection error'.format(self.appName))
        except Exception as e:
            self.cameraConnected = False
            self.appRunning = False
            self.logger.error('error: {0}'.format(e))
        finally:
            pass

    # central dispatcher for data coming from INDI devices
    def handleReceived(self, message):
        if isinstance(message, indiXML.SetBLOBVector):
            imageHDU = pyfits.HDUList.fromstring(message.getElt(0).getValue())
            imageHeader = imageHDU[0].header
            for key in imageHeader.keys():
                print(key)
        elif isinstance(message, indiXML.SetSwitchVector):
            print(message.getElt(0))
            for elt in message.elt_list:
                if elt.attr['name'] == 'CONNECT':
                    if message.getElt(0).getValue() == 'On':
                        self.cameraConnected = True
                    else:
                        self.cameraConnected = False
        else:
            print(message)

    def send(self, message):
        self.indiClient.sendMessage(message)

    def connectCamera(self):
        if self.appRunning:
            # Connect to the CCD simulator.
            self.indiClient.sendMessage(indiXML.newSwitchVector([indiXML.oneSwitch("On", indi_attr={"name": "CONNECT"})], indi_attr={"name": "CONNECTION", "device": "CCD Simulator"}))
            self.cameraConnected = True

    def disconnectCamera(self):
        if self.cameraConnected:
            # Connect to the CCD simulator.
            self.indiClient.sendMessage(indiXML.newSwitchVector([indiXML.oneSwitch("Off", indi_attr={"name": "CONNECT"})], indi_attr={"name": "CONNECTION", "device": "CCD Simulator"}))
            self.cameraConnected = False

    def getImage(self, modelData):
        if self.cameraConnected:
            # Enable BLOB mode.
            self.indiClient.sendMessage(indiXML.enableBLOB("Also", indi_attr={"device": "CCD Simulator"}))
            self.indiClient.sendMessage(indiXML.newNumberVector([indiXML.oneNumber(2, indi_attr={"name": "CCD_EXPOSURE_VALUE"})], indi_attr={"name": "CCD_EXPOSURE", "device": "CCD Simulator"}))

    def solveImage(self, modelData):
        pass

    def getCameraProps(self):
        if self.cameraConnected:
            pass

    def getCameraStatus(self):
        if self.appRunning:
            self.indiClient.sendMessage(indiXML.clientGetProperties(indi_attr={"version": "1.0", "device": "CCD Simulator"}))
            # Get a list of camera status
            # self.indiClient.sendMessage(indiXML.clientGetProperties(indi_attr={"version": "1.0", "device": "CCD Simulator"}))
