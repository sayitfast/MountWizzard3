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


class NoneDome:

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = 'None Dome'
        self.application['Status'] = 'OK'

    def start(self):
        pass

    def stop(self):
        pass

    def slewToAzimuth(self, azimuth):
        pass

    def getData(self):
        pass

    def getStatus(self):
        pass

