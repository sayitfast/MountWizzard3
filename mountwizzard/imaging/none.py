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
import PyQt5
import logging
import time


class NoneCamera:

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data

        self.application = dict()
        self.application['Available'] = True
        self.application['Name'] = 'Dummy Camera'
        self.application['InstallPath'] = ''
        self.application['Status'] = 'OK'
        self.application['Runtime'] = 'Dummy Camera'

    def getStatus(self):
        self.application['Status'] = 'OK'
        self.data['CONNECTION']['CONNECT'] = 'Off'

    @staticmethod
    def getCameraProps():
        pass

    @staticmethod
    def getImage(imageParams):
        pass

    @staticmethod
    def solveImage(imageParams):
        pass
