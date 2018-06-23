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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import time
import PyQt5
import requests
from requests_toolbelt.multipart import encoder
from baseclasses import checkIP
import json
import collections


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

    def __init__(self, main, app, data):
        self.main = main
        self.app = app
        self.data = data
        self.application = dict()
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.checkIP = checkIP.CheckIP()

        self.application = {
            'AstrometryHost': '192.168.2.161',
            'AstrometryPort': 3499,
            'URLLogin': '',
            'URLAPI': '',
            'APIKey': '',
            'TimeoutMax': 60,
            'Connected': False,
            'Available': True,
            'Name': 'ASTROMETRY.NET',
            'Status': ''
        }

        self.app.ui.le_AstrometryHost.editingFinished.connect(self.changeIPSettings)
        self.app.ui.le_AstrometryPort.editingFinished.connect(self.changeIPSettings)
        self.app.ui.le_AstrometryAPIKey.editingFinished.connect(self.changeIPSettings)

    def initConfig(self):
        try:
            if 'AstrometryTimeout' in self.app.config:
                self.app.ui.le_astrometryTimeout.setText(self.app.config['AstrometryTimeout'])
            if 'AstrometryHost' in self.app.config:
                self.app.ui.le_AstrometryHost.setText(self.app.config['AstrometryHost'])
            if 'AstrometryPort' in self.app.config:
                self.app.ui.le_AstrometryPort.setText(self.app.config['AstrometryPort'])
            if 'AstrometryAPIKey' in self.app.config:
                self.app.ui.le_AstrometryAPIKey.setText(self.app.config['AstrometryAPIKey'])
            if 'AstrometryDownsample' in self.app.config:
                self.app.ui.astrometryDownsampling.setValue(self.app.config['AstrometryDownsample'])
        except Exception as e:
            self.logger.error('Item in config.cfg for astrometry client could not be initialized, error:{0}'.format(e))
        finally:
            pass
        self.changeIPSettings()

    def storeConfig(self):
        self.app.config['AstrometryPort'] = self.app.ui.le_AstrometryPort.text()
        self.app.config['AstrometryHost'] = self.app.ui.le_AstrometryHost.text()
        self.app.config['AstrometryAPIKey'] = self.app.ui.le_AstrometryAPIKey.text()
        self.app.config['AstrometryTimeout'] = self.app.ui.le_astrometryTimeout.text()
        self.app.config['AstrometryDownsample'] = self.app.ui.astrometryDownsampling.value()

    def start(self):
        pass

    def stop(self):
        pass

    def setCancelAstrometry(self):
        self.mutexCancel.lock()
        self.cancel = True
        self.mutexCancel.unlock()

    def changeIPSettings(self):
        self.data['Status'] = 'ERROR'
        self.data['CONNECTION']['CONNECT'] = 'Off'
        host = self.app.ui.le_AstrometryHost.text()
        port = self.app.ui.le_AstrometryPort.text()
        self.application['AstrometryHost'] = host
        self.application['AstrometryPort'] = int(port)
        self.application['URLAPI'] = 'http://' + host + ':' + port + '/api'
        self.application['URLLogin'] = 'http://' + host + ':' + port + '/api/login'
        self.application['APIKey'] = self.app.ui.le_AstrometryAPIKey.text()
        self.application['Name'] = 'Astrometry'
        self.application['TimeoutMax'] = float(self.app.ui.le_astrometryTimeout.text())
        self.app.messageQueue.put('Setting IP address for astrometry to: {0}:{1}\n'.format(self.application['AstrometryHost'],
                                                                                           self.application['AstrometryPort']))
        self.logger.info('Setting IP address for astrometry to: {0}:{1}, key: {2}'.format(self.application['AstrometryHost'],
                                                                                          self.application['AstrometryPort'],
                                                                                          self.application['APIKey']))

    def getStatus(self):
        if self.application['URLAPI'] == '':
            return
        if self.checkIP.checkIPAvailable(self.application['AstrometryHost'], self.application['AstrometryPort']):
            self.application['Status'] = 'OK'
            self.data['CONNECTION']['CONNECT'] = 'On'
        else:
            self.data['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def callbackUpload(self, monitor):
        self.main.astrometrySolvingTime.emit('{0:3d}%'.format(int(monitor.bytes_read / monitor.len * 100)))

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
        if self.application['APIKey'] != '':
            # we have to login with the api key for the online solver to get the session key
            try:
                response = requests.post(self.application['URLLogin'],
                                         data={'request-json': json.dumps({"apikey": self.application['APIKey']})},
                                         headers={})
                result = json.loads(response.text)
            except Exception as e:
                self.logger.error('Problem setting api key, error: {0}, result: {1}, response: {2}'
                                  .format(e, result, response))
                imageParams['Message'] = 'Login with api key failed'
                errorState = True
            finally:
                pass
            if not errorState:
                if 'status' in result:
                    if result['status'] == 'error':
                        self.app.messageQueue.put('Get session key for ASTROMETRY.NET failed because: {0}\n'.format(result['errormessage']))
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
        data['scale_est'] = float(imageParams['ScaleHint'])
        # ra is in hours
        data['center_ra'] = imageParams['RaJ2000'] * 360 / 24
        data['center_dec'] = float(imageParams['DecJ2000'])

        if not errorState:
            fields = collections.OrderedDict()
            fields['request-json'] = json.dumps(data)
            fields['file'] = (imageParams['Imagepath'], open(imageParams['Imagepath'], 'rb'), 'application/octet-stream')
            encodedMultipart = encoder.MultipartEncoder(fields)
            monitorMultipart = encoder.MultipartEncoderMonitor(encodedMultipart, self.callbackUpload)
            try:
                result = ''
                response = requests.post(self.application['URLAPI'] + '/upload',
                                         data=monitorMultipart,
                                         headers={'Content-Type': monitorMultipart.content_type})
                result = json.loads(response.text)
                stat = result['status']
                self.logger.info('Result upload: {0}, reply: {1}'.format(result, response))
            except Exception as e:
                self.logger.error('Problem upload, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error upload'
            finally:
                pass
            if not errorState:
                if stat != 'success':
                    self.logger.warning('Could not upload image to astrometry server, error: {0}'.format(result))
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
                response = requests.get(self.application['URLAPI'] + '/submissions/{0}'
                                        .format(submissionID),
                                        data=data,
                                        headers=headers)
                result = json.loads(response.text)
                self.logger.info('Result submissions: {0}, reply: {1}'.format(result, response))
            except Exception as e:
                self.logger.error('Problem submissions, error: {0}, result: {1}, response: {2}'
                                  .format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error submissions'
                break
            finally:
                pass
            if 'jobs' in result:
                jobs = result['jobs']
            else:
                self.logger.error('Problem submissions, job not found, result: {0}, response: {1}'.format(result, response))
                errorState = True
                break
            if len(jobs) > 0:
                if jobs[0] is not None:
                    jobID = jobs[0]
                    break
            if time.time()-timeSolvingStart > self.application['TimeoutMax']:
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
                response = requests.get(self.application['URLAPI'] + '/jobs/{0}'
                                        .format(jobID),
                                        data=data,
                                        headers=headers)
                result = json.loads(response.text)
                self.logger.info('Result jobs: {0}, reply: {1}'.format(result, response))
            except Exception as e:
                self.logger.error('Problem jobs, error: {0}, result: {1}, response: {2}'.format(e, result, response))
                errorState = True
                imageParams['Message'] = 'Error jobs'
            finally:
                pass
            if 'status' in result:
                stat = result['status']
            else:
                self.logger.error('Problem jobs, status not found, result: {0}, response: {1}'.format(result, response))
                errorState = True
                break
            if stat == 'success':
                break
            if stat == 'failure':
                errorState = True
                break
            if time.time()-timeSolvingStart > self.application['TimeoutMax']:
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
        if not self.cancel and not errorState:
            try:
                result = ''
                response = requests.get(self.application['URLAPI'] + '/jobs/{0}/calibration'
                                        .format(jobID),
                                        data=data,
                                        headers=headers)
                result = json.loads(response.text)
                self.logger.info('Result calibration: {0}, reply: {1}'.format(result, response))
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
                imageParams['RaJ2000Solved'] = 0
                imageParams['DecJ2000Solved'] = 0
                imageParams['Scale'] = 0
                imageParams['Angle'] = 0
                imageParams['TimeTS'] = time.time()-timeSolvingStart
                imageParams['Solved'] = False
                imageParams['Message'] = 'Solve failed'
            finally:
                pass
        else:
            imageParams['Solved'] = False
            imageParams['Message'] = 'Solve failed'

        # finally idle
        self.main.imageDataDownloaded.emit()
        self.main.astrometryStatusText.emit('IDLE')
        self.main.astrometrySolvingTime.emit('')
