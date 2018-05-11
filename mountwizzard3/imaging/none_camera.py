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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import PyQt5

class NoneCamera:

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = True
        self.application['Name'] = 'Dummy Camera'
        self.application['InstallPath'] = ''
        self.application['Status'] = 'OK'
        self.application['Runtime'] = 'Dummy Camera'

    def start(self):
        pass

    def stop(self):
        pass

    def getStatus(self):
        self.application['Status'] = 'OK'
        self.data['CONNECTION']['CONNECT'] = 'On'

    def getCameraProps(self):
        self.data['CCD_INFO'] = {}
        self.data['CCD_INFO']['CCD_MAX_X'] = 1024
        self.data['CCD_INFO']['CCD_MAX_Y'] = 768
        self.data['Gain'] = 'High'

    def getImage(self, imageParams):
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()
