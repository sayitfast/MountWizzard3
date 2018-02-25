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
import os
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
                 'scale_err': 50,
                 'center_ra': 315,
                 'center_dec': 68,
                 'radius': 2,
                 'downsample_factor': 2,
                 'use_sextractor': False,
                 'crpix_center': True,
                 'parity': 2
                 }

    data = {
        'ServerIP': '192.168.2.161',
        'ServerPort': 3499,
        'Connected': False,
        'APIKey': ''
    }

    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.isSolving = False
        self.mutexIsSolving = PyQt5.QtCore.QMutex()
        self.checkIP = checkParamIP.CheckIP()
        self.settingsChanged = False
        self.timeoutMax = 60
        self.urlLogin = ''
        self.urlAPI = 'http://{0}:{1}/api'.format(self.data['ServerIP'], self.data['ServerPort'])

    def initConfig(self):
        try:
            if 'CheckEnableAstrometry' in self.app.config:
                self.app.ui.checkEnableAstrometry.setChecked(self.app.config['CheckEnableAstrometry'])
            if 'CheckUseOnlineSolver' in self.app.config:
                self.app.ui.rb_useOnlineSolver.setChecked(self.app.config['CheckUseOnlineSolver'])
            if 'CheckUseLocalSolver' in self.app.config:
                self.app.ui.rb_useLocalSolver.setChecked(self.app.config['CheckUseLocalSolver'])
            if 'AstrometryServerPort' in self.app.config:
                self.app.ui.le_AstrometryServerPort.setText(self.app.config['AstrometryServerPort'])
            if 'AstrometryServerIP' in self.app.config:
                self.app.ui.le_AstrometryServerIP.setText(self.app.config['AstrometryServerIP'])
            if 'AstrometryServerAPIKey' in self.app.config:
                self.app.ui.le_AstrometryServerAPIKey.setText(self.app.config['AstrometryServerAPIKey'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.setIP()
        self.setPort()
        # setting changes in gui on false, because the set of the config changed them already
        self.setAstrometryNet()
        self.app.ui.le_AstrometryServerIP.textChanged.connect(self.setIP)
        self.app.ui.le_AstrometryServerIP.editingFinished.connect(self.changedAstrometryClientConnectionSettings)
        self.app.ui.le_AstrometryServerPort.textChanged.connect(self.setPort)
        self.app.ui.le_AstrometryServerPort.editingFinished.connect(self.changedAstrometryClientConnectionSettings)
        self.app.ui.rb_useOnlineSolver.clicked.connect(self.setAstrometryNet)
        self.app.ui.rb_useLocalSolver.clicked.connect(self.setAstrometryNet)

    def storeConfig(self):
        self.app.config['AstrometryServerPort'] = self.app.ui.le_AstrometryServerPort.text()
        self.app.config['AstrometryServerIP'] = self.app.ui.le_AstrometryServerIP.text()
        self.app.config['AstrometryServerAPIKey'] = self.app.ui.le_AstrometryServerAPIKey.text()
        self.app.config['CheckEnableAstrometry'] = self.app.ui.checkEnableAstrometry.isChecked()
        self.app.config['CheckUseOnlineSolver'] = self.app.ui.rb_useOnlineSolver.isChecked()
        self.app.config['CheckUseLocalSolver'] = self.app.ui.rb_useLocalSolver.isChecked()

    def setAstrometryNet(self):
        self.settingsChanged = True
        self.changedAstrometryClientConnectionSettings()

    def changedAstrometryClientConnectionSettings(self):
        if self.settingsChanged:
            self.settingsChanged = False
            if self.app.ui.rb_useOnlineSolver.isChecked():
                self.urlAPI = 'http://nova.astrometry.net/api'
                self.urlLogin = 'http://nova.astrometry.net/api/login'
                self.timeoutMax = 360
            else:
                self.urlAPI = 'http://{0}:{1}/api'.format(self.data['ServerIP'], self.data['ServerPort'])
                self.urlLogin = ''
                self.timeoutMax = 60
            self.app.messageQueue.put('Setting IP address for Astrometry client: {0}\n'.format(self.urlAPI))

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
        try:
            retValue = 0
            data = {'request-json': ''}
            headers = {}
            result = requests.post(self.urlAPI, data=data, headers=headers)
            if result.status_code > 400:
                self.mutexIsRunning.lock()
                self.isRunning = True
                self.mutexIsRunning.unlock()
                if self.isSolving:
                    retValue = 1
                else:
                    # free to get some solving part
                    retValue = 2
            else:
                self.mutexIsRunning.lock()
                self.isRunning = False
                self.mutexIsRunning.unlock()
                retValue = 0
        except Exception as e:
            self.logger.error('Connection to {0} not possible, error: {1}'.format(self.urlAPI), e)
            self.mutexIsRunning.lock()
            self.isRunning = False
            self.mutexIsRunning.unlock()
            retValue = 0
        finally:
            return retValue

    def solveImage(self, filename, ra, dec, scale):
        # check if solving is possible
        if self.isSolving:
            return
        if not self.isRunning:
            self.logger.warning('Astrometry connection is not available')
            return {'Message': 'Astrometry not available'}
        if self.parent.cancel:
            return {'Message': 'Cancel'}
        if not os.path.isfile(filename):
            return {'Message': 'File missing'}

        # start formal solving
        self.mutexIsSolving.lock()
        self.isSolving = True
        self.mutexIsSolving.unlock()

        # check if we have the online solver running
        if self.urlLogin != '':
            # we have to login with the api key for the online solver to get the session key
            self.data['APIKey'] = self.app.ui.le_AstrometryServerAPIKey.text()
            try:
                result = ''
                response = requests.post(self.urlLogin, data={'request-json': json.dumps({"apikey": self.data['APIKey']})}, headers={})
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem setting api key, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                return {'Message': 'Login with api key failed'}

            if 'status' in result:
                if result['status'] == 'error':
                    self.app.messageQueue.put('\nGet session key for ASTROMETRY.NET failed because: {0}\n'.format(result['errormessage']))
                    self.logger.error('Get session key failed because: {0}'.format(result['errormessage']))
                elif result['status'] == 'success':
                    self.solveData['session'] = result['session']
                    self.app.messageQueue.put('\tSession key for ASTROMETRY.NET is [{0}]\n'.format(result['session']))
            else:
                return {'Message': 'Malformed result in login procedure'}
        else:
            # local solve runs with dummy session key
            self.solveData['session'] = 12345

        # start uploading the data and define the parameters
        data = self.solveData
        data['scale_est'] = scale
        # ra is in
        data['center_ra'] = ra * 360 / 24
        data['center_dec'] = dec
        fields = collections.OrderedDict()
        fields['request-json'] = json.dumps(data)
        fields['file'] = (filename, open(filename, 'rb'), 'application/octet-stream')
        m = MultipartEncoder(fields)
        try:
            result = ''
            response = requests.post(self.urlAPI + '/upload', data=m, headers={'Content-Type': m.content_type})
            result = json.loads(response.text)
            stat = result['status']
        except Exception as e:
            self.logger.error('Problem upload, error: {0}, result: {1}, response: {2}'.format(e, result, response))
            self.mutexIsSolving.lock()
            self.isSolving = False
            self.mutexIsSolving.unlock()
            return {'Message': 'Error upload'}

        if stat != 'success':
            self.mutexIsSolving.lock()
            self.isSolving = False
            self.mutexIsSolving.unlock()
            self.logger.warning('Could not upload image to astrometry server')
            return {'Message': 'Upload failed'}
        submissionID = result['subid']

        # wait for the submission = star detection algorithm to take place
        timeoutCounter = 0
        while self.app.workerModelingDispatcher.isRunning and not self.parent.cancel:
            data = {'request-json': ''}
            headers = {}
            try:
                result = ''
                response = requests.post(self.urlAPI + '/submissions/{0}'.format(submissionID), data=data, headers=headers)
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem submissions, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                self.mutexIsSolving.lock()
                self.isSolving = False
                self.mutexIsSolving.unlock()
                return {'Message': 'Error submission'}

            jobs = result['jobs']
            if len(jobs) > 0:
                if jobs[0] is not None:
                    jobID = jobs[0]
                    break
            timeoutCounter += 1
            if timeoutCounter > self.timeoutMax:
                # timeout after timeoutMax seconds
                self.mutexIsSolving.lock()
                self.isSolving = False
                self.mutexIsSolving.unlock()
                return {'Message': 'Solve failed due to timeout'}
            time.sleep(1)
            PyQt5.QtWidgets.QApplication.processEvents()

        # waiting for the solving results done by jobs are present
        while self.app.workerModelingDispatcher.isRunning and not self.parent.cancel:
            data = {'request-json': ''}
            headers = {}
            try:
                result = ''
                response = requests.post(self.urlAPI + '/jobs/{0}'.format(jobID), data=data, headers=headers)
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem jobs, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                self.mutexIsSolving.lock()
                self.isSolving = False
                self.mutexIsSolving.unlock()
                return {'Message': 'Error Jobs'}
            stat = result['status']
            if stat == 'success':
                break
            timeoutCounter += 1
            if timeoutCounter > self.timeoutMax:
                # timeout after timeoutMax seconds
                self.mutexIsSolving.lock()
                self.isSolving = False
                self.mutexIsSolving.unlock()
                return {'Message': 'Solve failed due to timeout'}
            time.sleep(1)
            PyQt5.QtWidgets.QApplication.processEvents()

        # now get the solving data and results
        try:
            result = ''
            response = requests.post(self.urlAPI + '/jobs/{0}/calibration'.format(jobID), data=data, headers=headers)
            result = json.loads(response.text)
        except Exception as e:
            self.logger.error('Problem get calibration data, error: {0}, result: {1}, response: {2}'.format(e, result, response))
            self.mutexIsSolving.lock()
            self.isSolving = False
            self.mutexIsSolving.unlock()
            return {'Message': 'Error Jobs'}
        result['Message'] = 'Solve OK'
        self.mutexIsSolving.lock()
        self.isSolving = False
        self.mutexIsSolving.unlock()
        return result
