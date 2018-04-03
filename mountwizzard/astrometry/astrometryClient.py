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
import logging
import os
import io
import sys
import time
import PyQt5
import requests
from requests_toolbelt import MultipartEncoder
import json
import collections

from baseclasses import checkParamIP


class AstrometryClient:
    logger = logging.getLogger(__name__)

    solveData = {'session': '12345',
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

    application = {
        'ServerIP': '192.168.2.161',
        'ServerPort': 3499,
        'Connected': False,
        'APIKey': '',
        'Available': True,
        'Name': 'ASTROMETRY.NET',
        'Status': ''
    }

    def __init__(self, main, app, data):
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.checkIP = checkParamIP.CheckIP()
        self.settingsChanged = False
        self.timeoutMax = 60
        self.urlLogin = ''
        self.urlAPI = ''

    def initConfig(self):
        try:
            if 'CheckUseOnlineSolver' in self.app.config:
                self.app.ui.rb_useOnlineSolver.setChecked(self.app.config['CheckUseOnlineSolver'])
            if 'CheckUseLocalSolver' in self.app.config:
                self.app.ui.rb_useLocalSolver.setChecked(self.app.config['CheckUseLocalSolver'])
            if 'OnlineSolverTimeout' in self.app.config:
                self.app.ui.le_timeoutOnline.setText(self.app.config['OnlineSolverTimeout'])
            if 'LocalSolverTimeout' in self.app.config:
                self.app.ui.le_timeoutLocal.setText(self.app.config['LocalSolverTimeout'])
            if 'AstrometryServerPort' in self.app.config:
                self.app.ui.le_AstrometryServerPort.setText(self.app.config['AstrometryServerPort'])
            if 'AstrometryServerIP' in self.app.config:
                self.app.ui.le_AstrometryServerIP.setText(self.app.config['AstrometryServerIP'])
            if 'AstrometryServerAPIKey' in self.app.config:
                self.app.ui.le_AstrometryServerAPIKey.setText(self.app.config['AstrometryServerAPIKey'])
            if 'AstrometryDownsample' in self.app.config:
                self.app.ui.astrometryDownsampling.setValue(self.app.config['AstrometryDownsample'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.setIP()
        self.setPort()
        self.urlAPI = 'http://{0}:{1}/api'.format(self.application['ServerIP'], self.application['ServerPort'])

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
        self.app.config['CheckUseOnlineSolver'] = self.app.ui.rb_useOnlineSolver.isChecked()
        self.app.config['CheckUseLocalSolver'] = self.app.ui.rb_useLocalSolver.isChecked()
        self.app.config['OnlineSolverTimeout'] = self.app.ui.le_timeoutOnline.text()
        self.app.config['LocalSolverTimeout'] = self.app.ui.le_timeoutLocal.text()
        self.app.config['AstrometryDownsample'] = self.app.ui.astrometryDownsampling.value()

    def start(self):
        pass

    def stop(self):
        pass

    def setAstrometryNet(self):
        self.settingsChanged = True
        self.changedAstrometryClientConnectionSettings()

    def setCancelAstrometry(self):
        self.mutexCancel.lock()
        self.cancel = True
        self.mutexCancel.unlock()

    def changedAstrometryClientConnectionSettings(self):
        if self.settingsChanged:
            self.data['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'
            self.settingsChanged = False
            if self.app.ui.rb_useOnlineSolver.isChecked():
                self.urlAPI = 'http://nova.astrometry.net/api'
                self.urlLogin = 'http://nova.astrometry.net/api/login'
                self.application['Name'] = 'Online'
                self.timeoutMax = float(self.app.ui.le_timeoutOnline.text())
            else:
                self.urlAPI = 'http://{0}:{1}/api'.format(self.application['ServerIP'], self.application['ServerPort'])
                self.urlLogin = ''
                self.application['Name'] = 'Local'
                self.timeoutMax = float(self.app.ui.le_timeoutLocal.text())
            self.app.messageQueue.put('Setting IP address for Astrometry client: {0}\n'.format(self.urlAPI))

    def setPort(self):
        valid, value = self.checkIP.checkPort(self.app.ui.le_AstrometryServerPort)
        self.settingsChanged = (self.application['ServerPort'] != value)
        if valid:
            self.application['ServerPort'] = value

    def setIP(self):
        valid, value = self.checkIP.checkIP(self.app.ui.le_AstrometryServerIP)
        self.settingsChanged = (self.application['ServerIP'] != value)
        if valid:
            self.application['ServerIP'] = value

    def getStatus(self):
        if self.urlAPI == '':
            return
        try:
            result = requests.post(self.urlAPI)
            if result.status_code in [200, 404]:
                self.application['Available'] = True
                self.application['Status'] = 'OK'
                self.data['CONNECTION']['CONNECT'] = 'On'
            else:
                self.application['Available'] = True
                self.data['Status'] = 'ERROR'
                self.data['CONNECTION']['CONNECT'] = 'Off'
        except requests.exceptions.ConnectionError:
            self.logger.error('Connection to {0} not possible, connection refused')
            self.application['Available'] = False
            self.data['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'
        except Exception as e:
            self.logger.error('Connection to {0} not possible, error: {1}'.format(self.urlAPI, e))
            self.application['Available'] = False
            self.data['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'
        finally:
            pass

    def solveImage(self, imageParams):
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        downsampleFactor = self.app.ui.astrometryDownsampling.value()
        # waiting for start solving
        timeSolvingStart = time.time()
        # defining start values
        errorState = False
        result = ''
        response = ''
        stat = ''
        submissionID = ''
        jobID = ''
        headers = dict()
        imageParams['Message'] = ''

        self.main.astrometryStatusText.emit('START')
        # check if we have the online solver running
        self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
        if self.urlLogin != '':
            # we have to login with the api key for the online solver to get the session key
            self.application['APIKey'] = self.app.ui.le_AstrometryServerAPIKey.text()
            try:
                response = requests.post(self.urlLogin, data={'request-json': json.dumps({"apikey": self.application['APIKey']})}, headers={})
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem setting api key, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                imageParams['Message'] = 'Login with api key failed'
                errorState = True
            finally:
                pass
            if not errorState:
                if 'status' in result:
                    if result['status'] == 'error':
                        self.app.messageQueue.put('\nGet session key for ASTROMETRY.NET failed because: {0}\n'.format(result['errormessage']))
                        self.logger.error('Get session key failed because: {0}'.format(result['errormessage']))
                        errorState = True
                    elif result['status'] == 'success':
                        self.solveData['session'] = result['session']
                        self.app.messageQueue.put('\tSession key for ASTROMETRY.NET is [{0}]\n'.format(result['session']))
                else:
                    imageParams['Message'] = 'Malformed result in login procedure'
                    errorState = True
        else:
            # local solve runs with dummy session key
            self.solveData['session'] = '12345'

        self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))

        # loop for upload
        self.main.astrometryStatusText.emit('UPLOAD')
        # start uploading the data and define the parameters
        data = self.solveData
        data['downsample_factor'] = downsampleFactor
        data['scale_est'] = imageParams['ScaleHint']
        # ra is in hours
        data['center_ra'] = imageParams['RaJ2000'] * 360 / 24
        data['center_dec'] = imageParams['DecJ2000']

        if not errorState:
            fields = collections.OrderedDict()
            fields['request-json'] = json.dumps(data)
            fields['file'] = (imageParams['Imagepath'], open(imageParams['Imagepath'], 'rb'), 'application/octet-stream')
            m = MultipartEncoder(fields)
            try:
                result = ''
                response = requests.post(self.urlAPI + '/upload', data=m, headers={'Content-Type': m.content_type})
                result = json.loads(response.text)
                stat = result['status']
            except Exception as e:
                self.logger.error('Problem upload, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error upload'
            finally:
                pass
            if not errorState:
                if stat != 'success':
                    self.logger.warning('Could not upload image to astrometry server')
                    imageParams['Message'] = 'Upload failed'
                    errorState = True
                else:
                    submissionID = result['subid']
        self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))

        # loop for solve
        self.main.astrometryStatusText.emit('SOLVE-Sub')
        # wait for the submission = star detection algorithm to take place
        while not self.cancel and not errorState:
            data = {'request-json': ''}
            headers = {}
            try:
                result = ''
                response = requests.post(self.urlAPI + '/submissions/{0}'.format(submissionID), data=data, headers=headers)
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem submissions, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error submissions'
                break
            finally:
                pass
            jobs = result['jobs']
            if len(jobs) > 0:
                if jobs[0] is not None:
                    jobID = jobs[0]
                    break
            if time.time()-timeSolvingStart > self.timeoutMax:
                # timeout after timeoutMax seconds
                errorState = True
                imageParams['Message'] = 'Timeout'
                break
            self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
            time.sleep(1)

        # waiting for the solving results done by jobs are present
        self.main.astrometryStatusText.emit('SOLVE-Job')
        while not self.cancel and not errorState:
            data = {'request-json': ''}
            headers = {}
            try:
                result = ''
                response = requests.post(self.urlAPI + '/jobs/{0}'.format(jobID), data=data, headers=headers)
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem jobs, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error jobs'
            finally:
                pass
            stat = result['status']
            if stat == 'success':
                break
            if time.time()-timeSolvingStart > self.timeoutMax:
                # timeout after timeoutMax seconds
                errorState = True
                imageParams['Message'] = 'Timeout'
                break
            self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
            time.sleep(1)

        # Loop for data
        self.main.imageSolved.emit()
        self.main.astrometryStatusText.emit('GET DATA')
        # now get the solving data and results
        if not errorState:
            try:
                result = ''
                response = requests.post(self.urlAPI + '/jobs/{0}/calibration'.format(jobID), data=data, headers=headers)
                result = json.loads(response.text)
                imageParams['Solved'] = True
                imageParams['RaJ2000Solved'] = result['ra'] * 24 / 360
                imageParams['DecJ2000Solved'] = result['dec']
                imageParams['Scale'] = result['pixscale']
                imageParams['Angle'] = result['orientation']
                imageParams['TimeTS'] = time.time()-timeSolvingStart
                self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
                imageParams['Message'] = 'Solved with success'
            except Exception as e:
                self.logger.error('Problem get calibration data, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                imageParams['Solved'] = False
                imageParams['Message'] = 'Solve failed'
            finally:
                pass
        else:
            imageParams['Solved'] = False

        # finally idle
        self.main.imageDataDownloaded.emit()
        self.main.astrometryStatusText.emit('IDLE')
        self.main.astrometrySolvingTime.emit('')
