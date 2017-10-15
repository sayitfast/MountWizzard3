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


class EKOS(MWCamera):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

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
        self.app = app
        self.appRunning = False
        self.driverNameTelescope = ''
        self.driverNameCCD = ''
        self.cameraConnected = False
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = 'EKOS - INDI'
        self.appExe = ''
        self.host = '192.168.2.164'
        self.port = 7624
        self.tryConnectionCounter = 0
        self.INDIClient = QtINDIClient(self, self.host, self.port)
        self.INDIClient.received.connect(self.handleReceived)
        self.INDIClient.start()

        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable = True

    def checkAppStatus(self):
        # is in case of indi only a status of the connection to the indi server
        try:
            self.appRunning = self.INDIClient.connected
            if self.appRunning:
                self.tryConnectionCounter = 0
            else:
                self.tryConnectionCounter += 1
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

    def handleReceived(self, message):
        # central dispatcher for data coming from INDI devices. I makes the whole status and data evaluation and fits the
        # data to mountwizzard
        if isinstance(message, indiXML.SetBLOBVector):
            print('blob')
            imageHDU = pyfits.HDUList.fromstring(message.getElt(0).getValue())
            imageHeader = imageHDU[0].header
            for key in imageHeader.keys():
                print(key)
        elif isinstance(message, indiXML.SetSwitchVector) or isinstance(message, indiXML.DefSwitchVector):
            for elt in message.elt_list:
                # print('SWITCHVECTOR', elt)
                if elt.attr['name'] == 'CONNECT':
                    if message.getElt(0).getValue() == 'On':
                        self.cameraConnected = True
                    else:
                        self.cameraConnected = False
        elif isinstance(message, indiXML.SetNumberVector) or isinstance(message, indiXML.DefNumberVector):
            if message.attr['name'] == 'TELESCOPE_INFO':
                print('Apert: ', message.getElt(0).getValue(), 'FL: ', message.getElt(1).getValue())
            elif message.attr['name'] == 'CCD_INFO':
                print('X: ', message.getElt(0).getValue(), 'Y: ', message.getElt(1).getValue(), 'Pixel:', message.getElt(2).getValue(), 'Pixel X: ', message.getElt(3).getValue(), 'Pixel Y: ', message.getElt(4).getValue())
            elif message.attr['name'] == 'CCD_BINNING':
                print('BinX: ', message.getElt(0).getValue(), 'BinY: ', message.getElt(1).getValue())
            elif message.attr['name'] == 'CCD_FRAME':
                print('Left: ', message.getElt(0).getValue(), 'Top: ', message.getElt(1).getValue(), 'Width: ', message.getElt(2).getValue(), 'Height: ', message.getElt(3).getValue())
        elif isinstance(message, indiXML.DefTextVector):
            if 'name' in message.attr:
                if message.attr['name'] == 'DRIVER_INFO':
                    if message.elt_list[3].attr['name'] == 'DRIVER_INTERFACE':
                        if int(message.getElt(3).getValue()) & self.TELESCOPE_INTERFACE:
                            self.driverNameTelescope = message.getElt(0).getValue()
                        elif int(message.getElt(3).getValue()) & self.CCD_INTERFACE:
                            self.driverNameCCD = message.getElt(0).getValue()
        else:
            pass

    def connectCamera(self):
        if self.appRunning:
            # Connect to the CCD Driver
            if self.driverNameCCD:
                self.INDIClient.INDIsendQueue.put(indiXML.setSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.driverNameCCD}))

    def disconnectCamera(self):
        if self.cameraConnected and self.driverNameCCD:
            # Connect to the CCD simulator.
            self.INDIClient.INDIsendQueue.put(indiXML.setSwitchVector([indiXML.oneSwitch('Off', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.driverNameCCD}))

    def getImage(self, modelData):
        if self.cameraConnected and self.driverNameCCD:
            # Enable BLOB mode.
            print('start imaging')
            self.INDIClient.INDIsendQueue.put(indiXML.enableBLOB('Also', indi_attr={'device': self.driverNameCCD}))
            self.INDIClient.INDIsendQueue.put(indiXML.setNumberVector([indiXML.oneNumber(2, indi_attr={'name': 'CCD_EXPOSURE_VALUE'})], indi_attr={'name': 'CCD_EXPOSURE', 'device': self.driverNameCCD}))
        modelData['imagepath'] = 'c:/temp/t2.fit'
        return True, 'OK', modelData

    def solveImage(self, modelData):
        pass

    def getCameraProps(self):
        return True, 'OK', 1280, 900, False, 'High'

    def runConnected(self):
        # enable a list of commands and status messages to be received from INDI server
        # this should be done once in a connection lifecycle
        # first for the devices itself
        self.INDIClient.INDIsendQueue.put(indiXML.clientGetProperties(indi_attr={'version': '1.0'}))
        # second for the parameters of the camera
        # self.INDIClient.INDIsendQueue.put(indiXML.newSwitchVector(indi_attr={"name": "CONNECT", "name": "CONNECTION", "device": "CCD Simulator"}))

    def getCameraStatus(self):
        # not needed, because with INDI I have an event driven system
        pass

