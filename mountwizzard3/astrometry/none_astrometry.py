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
###########################################################
import PyQt5


class NoneAstrometry:

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = True
        self.application['Name'] = 'Dummy Solver'
        self.application['InstallPath'] = ''
        self.application['Status'] = 'OK'
        self.application['Runtime'] = 'Dummy Solver'

    def start(self):
        pass

    def stop(self):
        pass

    def getStatus(self):
        self.application['Status'] = 'OK'
        self.data['CONNECTION']['CONNECT'] = 'On'

    def solveImage(self, imageParams):
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()
