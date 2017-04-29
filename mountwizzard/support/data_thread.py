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
import os
import logging
from PyQt5 import QtCore
import time
import urllib


class Data(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems

    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMET = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    ASTEROIDS = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    SPACESTATIONS = 'https://www.celestrak.com/NORAD/elements/stations.txt'
    SAT_BRIGHTEST = 'https://www.celestrak.com/NORAD/elements/visual.txt'
    TARGET_DIR = os.getcwd() + '/config/'

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):                                                                                                          # runnable for doing the work
        while True:                                                                                                         # main loop for stick thread
            if not self.app.commandDataQueue.empty():
                command = self.app.commandDataQueue.get()
                if command == 'SPACESTATIONS':
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                    testfile = urllib.URLopener()
                    testfile.retrieve(self.SPACESTATIONS, self.TARGET_DIR + 'spacestations.tle')
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                elif command == 'SAT_BRIGHTEST':
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                    testfile = urllib.URLopener()
                    testfile.retrieve(self.SAT_BRIGHTEST, self.TARGET_DIR + 'sat_brightest.tle')
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS':
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                    testfile = urllib.URLopener()
                    testfile.retrieve(self.ASTEROIDS, self.TARGET_DIR + 'asteroids.mpc')
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                elif command == 'COMETS':
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                    testfile = urllib.URLopener()
                    testfile.retrieve(self.COMETS, self.TARGET_DIR + 'comets.mpc')
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                elif command == 'EARTHROTATION':
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                    testfile = urllib.URLopener()
                    testfile.retrieve(self.UTC_1, self.TARGET_DIR + 'finals.data')
                    testfile.retrieve(self.UTC_2, self.TARGET_DIR + 'tai-utc.dat')
                    self.app.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                else:
                    pass
            time.sleep(1)                                                                                                   # wait for the next cycle
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()

    def getStatusFast(self):
        pass

    def getStatusMedium(self):
        self.logger.error('getStatusMedium-> error accessing weather ascom data: {}')

    def getStatusSlow(self):
        pass

    def getStatusOnce(self):
        pass

    def downloadTLE(self):
        pass

    def downloadMPC(self):
        pass

    def downloadTest(self):
        pass
