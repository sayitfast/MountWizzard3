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

# import basic stuff
import logging
import time
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch


class NoneCamera:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.appRunning = False
        self.appConnected = False
        self.appCameraConnected = False
        self.cameraStatus = ''
        self.appInstallPath = ''
        self.appAvailable = False
        self.appName = ''
        self.appExe = ''
        self.checkAppInstall()

    def checkAppInstall(self):
        self.appAvailable = False

    def checkAppStatus(self):
        self.appRunning = False
        self.appConnected = False
        self.appCameraConnected = False

    def startApplication(self):
        pass

    def connectApplication(self):
        pass

    def disconnectApplication(self):
        pass

    def connectCamera(self):
        pass

    def disconnectCamera(self):
        pass

    def getImage(self, modelData):
        return False, 'Camera not Connected', modelData

    def getCameraProps(self):
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        return suc, mes, sizeX, sizeY, canSubframe, gains

    def getCameraStatus(self):
        self.cameraStatus = 'NOT CONNECTED'

    def solveImage(self, modelData):
        return False, 'Error', modelData
