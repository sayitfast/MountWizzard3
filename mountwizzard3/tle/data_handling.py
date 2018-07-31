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
import json
import math
import os
import PyQt5
from logging import getLogger


class TLEDataHandling:
    logger = getLogger(__name__)
    signalUpdateSatelliteList = PyQt5.QtCore.pyqtSignal()

    satelliteData = {
        'Line0': list(),
        'Line1': list(),
        'Line2': list()
    }

    def __init__(self, app):
        self.app = app

        self.app.ui.btn_loadSatelliteData.clicked.connect(self.selectSatellitesDataFileName)
        self.app.ui.listSatelliteName.itemDoubleClicked.connect(self.getListAction)

    def initConfig(self):
        try:
            if 'SatelliteDataFileName' in self.app.config:
                self.app.ui.le_satelliteDataFileName.setText(self.app.config['SatelliteDataFileName'])
                if self.app.config['SatelliteDataFileName'] != '':
                    self.loadSatelliteData(os.getcwd() + '/config/' + self.app.config['SatelliteDataFileName'] + '.tle', self.satelliteData)
        except Exception as e:
            self.logger.error('item in config.cfg could not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['SatelliteDataFileName'] = self.app.ui.le_satelliteDataFileName.text()

    def selectSatellitesDataFileName(self):
        value, ext = self.app.selectFile(self.app, 'Open satellite data file', '/config', 'TLE File (*.tle)', True)
        if value != '':
            self.app.ui.le_satelliteDataFileName.setText(os.path.basename(value))
            # next is to load and populate the data dictionary
            self.loadSatelliteData(value + ext, self.satelliteData)

    def loadSatelliteData(self, filename, data):
        if not os.path.isfile(filename):
            self.logger.error('Data file {0} is not existent'.format(filename))
        try:
            with open(filename, 'r') as infile:
                lines = infile.read().splitlines()
        except Exception as e:
            self.logger.error('Error loading satellite data: {0}'.format(e))
        finally:
            pass
        # if we don't have a full set of data (3 lines each, we have a problem
        if (len(lines) % 3) != 0:
            self.logger.error('Problem in data file - could not load data')
            return
        else:
            self.logger.info('Data from file : {0} loaded'.format(filename))
        # as we have now loaded a set of data, we could parse it.
        # first delete the data
        self.satelliteData = {
            'Line0': list(),
            'Line1': list(),
            'Line2': list()
        }
        # then make three lists for each line of TLE data
        # Line0 holds the name for the selection list
        # Line1 and Line2 hold the data
        for i in range(0, len(lines), 3):
            data['Line0'].append(lines[i])
            data['Line1'].append(lines[i+1])
            data['Line2'].append(lines[i+2])
        self.setSatelliteNameList(data['Line0'], self.app.ui.listSatelliteName)

    @staticmethod
    def setSatelliteNameList(data, satelliteList):
        satelliteList.clear()
        for name in data:
            satelliteList.addItem(name)
        satelliteList.sortItems()
        satelliteList.update()

    def getListAction(self):
        print(self.app.ui.listSatelliteName.currentItem().text())
