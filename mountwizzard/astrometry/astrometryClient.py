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
import collections
from astrometry.encode import MultipartEncoder
import io
import sys
from baseclasses import checkParamIP


class AstrometryClient:
    logger = logging.getLogger(__name__)

    dataTest = {'session': 12345,
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

    def __init__(self, app):
        self.app = app
        self.checkIP = checkParamIP.CheckIP()
        self.settingsChanged = False
        self.urlAPI = '{0}:{1}/api'.format(self.data['ServerIP'], self.data['ServerPort'])

    def initConfig(self):
        try:
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

    def solveImage(self, filename):
        fields = collections.OrderedDict()
        fields['request-json'] = (json.dumps(self.data), 'text/plain')
        fields['file'] = (filename, open(filename, 'rb'), 'application/octet-stream')
        m = MultipartEncoder(fields)
        result = requests.post(self.urlAPI + '/upload', data=m, headers={'Content-Type': m.content_type})
        return json.loads(result.text)

        while True:
            data = {'request-json': json}
            headers = {}
            result = requests.post(self.urlAPI + '/submissions/{0}'.format(sub_id), data=data, headers=headers)
            json.loads(result.text)
            jobs = stat['jobs']
            if len(jobs) > 0:
                break

        data = {'request-json': json}
        headers = {}
        result = requests.post(self.urlAPI + '/jobs/{0}'.format(job_id), data=data, headers=headers)
        result = json.loads(result.text)
        stat = result['status']
        if stat == 'success':
            result = requests.post(self.urlAPI + '/jobs/{0}/calibration'.format(job_id), data=data, headers=headers)
            return json.loads(result.text)
        else:
            return {}



if __name__ == '__main__':

    c = AstrometryClient()
    c.solveImage('NGC7023.fit')

