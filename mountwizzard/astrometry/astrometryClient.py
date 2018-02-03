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
import logging
import requests
import json
import time
import PyQt5
import collections
from requests_toolbelt import MultipartEncoder
import io
import sys
from baseclasses import checkParamIP


class AstrometryClient:
    logger = logging.getLogger(__name__)

    solveData = {'session': 12345,
                 'allow_commercial_use': 'd',
                 'allow_modifications': 'd',
                 'publicly_visible': 'n',
                 'scale_units': 'arcsecperpix',
                 'scale_type': 'ev',
                 'scale_est': 1.3,
                 'scale_err': 20,
                 'center_ra': 315,
                 'center_dec': 68,
                 # 'radius': float,
                 # 'downsample_factor': 2,
                 # 'use_sextractor': False,
                 # 'crpix_center': False,
                 # 'parity': 2
                 }

    data = {
        'ServerIP': '192.168.2.161',
        'ServerPort': 3499,
        'Connected': False,
    }

    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.isRunning = False
        self.isSolving = False
        self.checkIP = checkParamIP.CheckIP()
        self.settingsChanged = False
        self.urlAPI = 'http://{0}:{1}/api'.format(self.data['ServerIP'], self.data['ServerPort'])

    def initConfig(self):
        try:
            if 'CheckEnableAstrometry' in self.app.config:
                self.app.ui.checkEnableAstrometry.setChecked(self.app.config['CheckEnableAstrometry'])
            if 'AstrometryServerPort' in self.app.config:
                self.app.ui.le_AstrometryServerPort.setText(self.app.config['AstrometryServerPort'])
            if 'AstrometryServerIP' in self.app.config:
                self.app.ui.le_AstrometryServerIP.setText(self.app.config['AstrometryServerIP'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.setIP()
        self.setPort()
        # setting changes in gui on false, because the set of the config changed them already
        self.settingsChanged = False
        self.app.ui.le_AstrometryServerIP.textChanged.connect(self.setIP)
        self.app.ui.le_AstrometryServerIP.editingFinished.connect(self.changedAstrometryClientConnectionSettings)
        self.app.ui.le_AstrometryServerPort.textChanged.connect(self.setPort)
        self.app.ui.le_AstrometryServerPort.editingFinished.connect(self.changedAstrometryClientConnectionSettings)

    def storeConfig(self):
        self.app.config['AstrometryServerPort'] = self.app.ui.le_AstrometryServerPort.text()
        self.app.config['AstrometryServerIP'] = self.app.ui.le_AstrometryServerIP.text()
        self.app.config['CheckEnableAstrometry'] = self.app.ui.checkEnableAstrometry.isChecked()

    def changedAstrometryClientConnectionSettings(self):
        if self.settingsChanged:
            self.settingsChanged = False
            self.app.messageQueue.put('Setting IP address/port for Astrometry client: {0}:{1}\n'.format(self.data['ServerIP'], self.data['ServerPort']))

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_AstrometryServerPort)
        self.settingsChanged = (self.data['ServerPort'] != value)
        if valid:
            self.data['ServerPort'] = value

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_AstrometryServerIP)
        self.settingsChanged = (self.data['ServerIP'] != value)
        if valid:
            self.data['ServerIP'] = value

    def checkAstrometryServerRunning(self):
        jobID = 12345
        data = {'request-json': ''}
        headers = {}
        result = requests.post(self.urlAPI + '/submissions/{0}'.format(jobID), data=data, headers=headers)
        result = json.loads(result.text)
        if 'jobs' in result:
            self.isRunning = True
            if self.isSolving:
                return 1
            else:
                # free to get some solving part
                return 2
        else:
            self.isRunning = False
            return 0

    def solveImage(self, filename, ra, dec, scale):
        if not self.isRunning:
            self.logger.warning('Astrometry connection is not available')
            return {}
        if self.parent.cancel:
            return {}
        self.isSolving = True
        data = self.solveData
        data['scale_est'] = scale
        data['center_ra'] = ra
        data['center_dec'] = dec
        fields = collections.OrderedDict()
        fields['request-json'] = json.dumps(data)
        fields['file'] = (filename, open(filename, 'rb'), 'application/octet-stream')
        m = MultipartEncoder(fields)
        result = requests.post(self.urlAPI + '/upload', data=m, headers={'Content-Type': m.content_type})
        result = json.loads(result.text)
        stat = result['status']
        if stat != 'success':
            self.isSolving = False
            self.logger.warning('Could not upload image to astrometry server')
            return {}
        jobID = result['subid']

        while self.app.workerModelingDispatcher.isRunning and not self.parent.cancel:
            data = {'request-json': ''}
            headers = {}
            result = requests.post(self.urlAPI + '/submissions/{0}'.format(jobID), data=data, headers=headers)
            result = json.loads(result.text)
            jobs = result['jobs']
            if len(jobs) > 0:
                break
            time.sleep(1)
            PyQt5.QtWidgets.QApplication.processEvents()

        data = {'request-json': ''}
        headers = {}
        result = requests.post(self.urlAPI + '/jobs/{0}'.format(jobID), data=data, headers=headers)
        result = json.loads(result.text)
        stat = result['status']
        if stat == 'success':
            result = requests.post(self.urlAPI + '/jobs/{0}/calibration'.format(jobID), data=data, headers=headers)
            value = json.loads(result.text)
        else:
            value = {}
        self.isSolving = False
        return value
