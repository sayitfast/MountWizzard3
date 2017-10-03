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


class MWCamera:
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

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
        pass

    def checkAppStatus(self):
        pass

    def connectCamera(self):
        pass

    def disconnectCamera(self):
        pass

    def connectApplication(self):
        pass

    def disconnectApplication(self):
        pass

    def getImage(self, modelData):
        pass

    def solveImage(self, modelData):
        pass

    def getCameraProps(self):
        pass

    def getCameraStatus(self):
        pass
