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
import json
import logging
import platform
import socket
import timeit
import time
import PyQt5


class TheSkyX:
    logger = logging.getLogger(__name__)

    host = '127.0.0.1'
    port = 3040

    CAMERASTATUS = {'Not Connected': 'DISCONNECTED', 'Downloading Light': 'DOWNLOAD', 'Exposure complete': 'IDLE', 'Ready': 'IDLE', 'Exposing Light': 'INTEGRATING'}

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.checkIP = checkIP.CheckIP()
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.commandQueue = commandQueue
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = ''
        self.application['InstallPath'] = ''
        self.application['Status'] = ''
        self.application['Runtime'] = 'TheSkyX.exe'

        self.responseSuccess = '|No error. Error = 0.'

        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.application['Available'], self.application['Name'], self.application['InstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.application['Available']:
                self.app.messageQueue.put('Found Imaging: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application TheSkyX not found on computer')

    def start(self):
        pass

    def stop(self):
        pass

    def getStatus(self):
        captureResponse = {}
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'Out=String(\'{"ExposureStatus":"\'+ccdsoftCamera.ExposureStatus+\'","Status":"\'+ccdsoftCamera.Status+\'"}\');'
            # command += 'Out=ccdsoftCamera.ExposureStatus;'
            success, response = self.sendCommand(command)
            captureResponse = json.loads(response)
        except Exception as e:
            self.logger.error('Exception by getting status, error {0}'.format(e))
            success = False
            captureResponse['ExposureStatus'] = ''
            captureResponse['Status'] = ''
        finally:
            pass

        if success:
            if captureResponse['ExposureStatus'].startswith('Exposing Light'):
                captureResponse['ExposureStatus'] = 'Exposing Light'
            if captureResponse['ExposureStatus'] in self.CAMERASTATUS:
                self.data['Camera']['Status'] = self.CAMERASTATUS[captureResponse['ExposureStatus']]
                if self.CAMERASTATUS[captureResponse['ExposureStatus']] == 'DISCONNECTED':
                    self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'
                else:
                    self.data['Camera']['CONNECTION']['CONNECT'] = 'On'
                    self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown camera status: {0}'.format(captureResponse['ExposureStatus']))
        else:
            self.data['Camera']['Status'] = 'ERROR'
            self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'
            self.data['Solver']['Status'] = 'ERROR'
            self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'

        self.cameraStatusText.emit(self.data['Camera']['Status'])
        # construct exposure time if present
        if '(' in captureResponse['Status']:
            exposeval = float(captureResponse['Status'].split('(', 1)[1].split('Left)')[0].replace(',', '.'))
            self.cameraExposureTime.emit('{0:02.0f}'.format(exposeval))
        else:
            self.cameraExposureTime.emit('---')

        if 'CONNECTION' in self.data['Camera']:
            if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(0)

        if 'CONNECTION' in self.data['Solver']:
            if self.data['Solver']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusSolver.emit(2)
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(0)

    def getCameraProps(self):
        if 'CONNECTION' in self.data['Camera']:
            if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                # TODO: Get the chance to implement subframe on / off if a camera doesn't support this
                # TODO: Gain setting in CMOS Cameras necessary ?
                try:
                    command = '/* Java Script */'
                    command += 'var Out = "";'
                    command += 'ccdsoftCamera.Asynchronous=0;'
                    command += 'Out=String(\'{"WidthInPixels":"\'+ccdsoftCamera.WidthInPixels+\'","HeightInPixels":"\'+ccdsoftCamera.HeightInPixels+\'"}\');'
                    success, response = self.sendCommand(command)
                    captureResponse = json.loads(response)
                except Exception as e:
                    self.logger.error('Exception by getting props, error {0}'.format(e))
                    return False, 'Request failed', '', '', '', ''

                if success:
                    self.data['Camera']['Gain'] = ['High']
                    self.data['Camera']['Message'] = ''
                    if False:
                        self.data['Camera']['CCD_FRAME'] = {}
                        self.data['Camera']['CCD_FRAME']['HEIGHT'] = 0
                        self.data['Camera']['CCD_FRAME']['WIDTH'] = 0
                        self.data['Camera']['CCD_FRAME']['X'] = 0
                        self.data['Camera']['CCD_FRAME']['Y'] = 0
                    self.data['Camera']['CCD_INFO'] = {}
                    self.data['Camera']['CCD_INFO']['CCD_MAX_X'] = int(captureResponse['WidthInPixels'])
                    self.data['Camera']['CCD_INFO']['CCD_MAX_Y'] = int(captureResponse['HeightInPixels'])

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLEPROPS, self.setCameraProps)

    def sendCommand(self, command):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            tsxSocket.send(command.encode())
            response = str(tsxSocket.recv(1024).decode())

            if response.endswith(self.responseSuccess):
                response = response.replace(self.responseSuccess, '')
                return True, response
            else:
                return False, response
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, format(e)
        finally:
            # noinspection PyUnboundLocalVariable
            tsxSocket.close()

    def solveImage(self, imageParams):
        if imageParams['Blind']:
            self.logger.warning('Blind mode is not supported. TheSkyX allows to switch to All Sky Image Link by scripting. Please, enable All Sky Image Link manually in TheSkyX')

        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'ImageLink.pathToFITS="' + str(imageParams['ImagePath']).replace('\\', '/') + '";'
            if imageParams['ScaleHint']:
                command += 'ImageLink.unknownScale=0;'
                command += 'ImageLink.scale=' + str(imageParams['ScaleHint']) + ';'
            else:
                command += 'ImageLink.unknownScale=1;'
                command += 'ImageLink.scale=2;'
            command += 'ImageLink.execute();'
            command += 'Out=String(\'{"succeeded":"\'+ImageLinkResults.succeeded+\'","imageCenterRAJ2000":"\'+ImageLinkResults.imageCenterRAJ2000+\'","imageCenterDecJ2000":"\'+ImageLinkResults.imageCenterDecJ2000+\'","imageScale":"\'+ImageLinkResults.imageScale+\'","imagePositionAngle":"\'+ImageLinkResults.imagePositionAngle+\'"}\');'

            startTime = timeit.default_timer()
            success, response = self.sendCommand(command)
            solveTime = timeit.default_timer() - startTime

            if success:
                captureResponse = json.loads(response)
                if captureResponse['succeeded'] == '1':
                    imageParams['RaJ2000Solved'] = float(captureResponse['imageCenterRAJ2000'])
                    imageParams['DecJ2000Solved'] = float(captureResponse['imageCenterDecJ2000'])
                    imageParams['Scale'] = float(captureResponse['imageScale'])
                    imageParams['Angle'] = float(captureResponse['imagePositionAngle'])
                    imageParams['TimeTS'] = solveTime
                    imageParams['Message'] = 'Solved'
                else:
                    imageParams['Message'] = 'Unsolved'
            else:
                imageParams['Message'] = 'Request failed'
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            imageParams['Message'] = 'Request failed'
        finally:
            return imageParams
