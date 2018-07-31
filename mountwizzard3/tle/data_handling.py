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
from logging import getLogger


class TLEDataHandling:
    logger = getLogger(__name__)

    def __init__(self, app):
        self.app = app

        self.app.ui.btn_loadSatelliteData.clicked.connect(self.selectSatellitesDataFileName)

    def initConfig(self):
        try:
            if 'SatelliteDataFileName' in self.app.config:
                self.app.ui.le_satelliteDataFileName.setText(self.app.config['SatelliteDataFileName'])
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

    def setSatellitesNamesList(self):
        self.app.ui.listSatellitesName.clear()
        for name in self.data['ModelNames']:
            self.app.ui.listSatellitesName.addItem(name)
        self.app.ui.listSatellitesName.sortItems()
        self.app.ui.listSatellitesName.update()
