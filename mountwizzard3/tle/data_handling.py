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
import time
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
                    self.loadSatelliteData(os.getcwd() + '/config/' + self.app.config['SatelliteDataFileName'] + '.tle')
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
            self.loadSatelliteData(value + ext)

    def loadSatelliteData(self, filename):
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
            self.satelliteData['Line0'].append(lines[i])
            self.satelliteData['Line1'].append(lines[i+1])
            self.satelliteData['Line2'].append(lines[i+2])
        self.setSatelliteNameList()

    def setSatelliteNameList(self):
        self.app.ui.listSatelliteName.clear()
        for name in self.satelliteData['Line0']:
            self.app.ui.listSatelliteName.addItem(name)
        self.app.ui.listSatelliteName.sortItems()
        self.app.ui.listSatelliteName.update()

    def parseSatelliteData(self, index):
        # parsing of the data is accordingly to https://www.celestrak.com/NORAD/documentation/tle-fmt.php
        print(self.satelliteData['Line0'][index])
        print(self.satelliteData['Line1'][index])
        print(self.satelliteData['Line2'][index])

        # doing that just for information in the gui. The mount computer itself parses the data
        self.app.ui.le_satelliteName.setText(self.satelliteData['Line0'][index].strip())
        self.app.ui.le_satelliteNumber.setText(self.satelliteData['Line1'][index][2:7])
        self.app.ui.le_satelliteLaunchYear.setText(self.satelliteData['Line1'][index][9:11])
        self.app.ui.le_satelliteEpochDay.setText(self.satelliteData['Line1'][index][20:32])
        self.app.ui.le_satelliteEpochYear.setText(self.satelliteData['Line1'][index][18:20])
        self.app.ui.le_satellite1derrMotion.setText(self.satelliteData['Line1'][index][32:43])
        self.app.ui.le_satellite2derrMotion.setText(self.satelliteData['Line1'][index][44:52])
        self.app.ui.le_satelliteBSTAR.setText(self.satelliteData['Line1'][index][53:61])
        self.app.ui.le_satelliteInclination.setText(self.satelliteData['Line2'][index][8:16])
        self.app.ui.le_satelliteRA.setText(self.satelliteData['Line2'][index][17:25])
        self.app.ui.le_satelliteEccentricity.setText(self.satelliteData['Line2'][index][26:33])
        self.app.ui.le_satellitePerigee.setText(self.satelliteData['Line2'][index][34:42])
        self.app.ui.le_satelliteAnomaly.setText(self.satelliteData['Line2'][index][43:51])
        self.app.ui.le_satelliteMotion.setText(self.satelliteData['Line2'][index][52:63])

    def pushSatelliteDataToMount(self, data, name):
        commandSet = {'command': ':TLEL0{0}#'.format(data), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'][0] == 'V':
            self.app.messageQueue.put('TLE data for {0} loaded\n'.format(name))
            self.app.workerMountDispatcher.workerMountGetModelNames.getModelNames()
            returnValue = True
        else:
            self.app.messageQueue.put('#BRTLE data for {0} could not be loaded\n'.format(name))
            self.logger.warning('TLE data for {0} could not be loaded. Error code: {1}'.format(name, commandSet['reply']))
            returnValue = False
        return returnValue

    def getListAction(self):
        name = self.app.ui.listSatelliteName.currentItem().text()
        index = self.satelliteData['Line0'].index(name)
        self.parseSatelliteData(index)
        data = self.satelliteData['Line0'][index] + '\r' + self.satelliteData['Line1'][index] + '\r' + self.satelliteData['Line2'][index]
        if self.pushSatelliteDataToMount(data, name.strip()):
            pass
            # now calculation transits etc.
        else:
            return
