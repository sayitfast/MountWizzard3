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

    def getImage(self, imageParams):
        # TODO: how is TSX dealing with ISO settings for DSLR?
        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=1;'
            if imageParams['CanSubframe']:
                command += 'ccdsoftCamera.Subframe=1;'
                command += 'ccdsoftCamera.SubframeLeft=' + str(imageParams['OffX']) + ';'
                command += 'ccdsoftCamera.SubframeTop=' + str(imageParams['OffY']) + ';'
                command += 'ccdsoftCamera.SubframeRight=' + str(imageParams['OffX'] + imageParams['SizeX']) + ';'
                command += 'ccdsoftCamera.SubframeBottom=' + str(imageParams['OffY'] + imageParams['SizeY']) + ';'
            else:
                command += 'ccdsoftCamera.Subframe=0;'

            if imageParams['Speed'] == 'HiSpeed':
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "Fast Image Download");'
            else:
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "High Image Quality");'

            command += 'ccdsoftCamera.BinX='+str(imageParams['Binning'])+';'
            command += 'ccdsoftCamera.BinY='+str(imageParams['Binning'])+';'
            command += 'ccdsoftCamera.ExposureTime='+str(imageParams['Exposure'])+';'
            command += 'ccdsoftCamera.AutoSavePath="'+str(imageParams['BaseDirImages'])+'";'
            command += 'ccdsoftCamera.AutoSaveOn=1;'
            command += 'ccdsoftCamera.Frame="cdLight";'
            command += 'ccdsoftCamera.TakeImage();'
            success, response = self.sendCommand(command)
            if success:
                command = '/* Java Script */'
                command += 'ccdsoftCamera.Asynchronous=1;'
                command += 'var Out = "";'
                command += 'Out=ccdsoftCamera.IsExposureComplete;'
                while True:
                    success, response = self.sendCommand(command)
                    if response == '1':
                        break
                    else:
                        time.sleep(0.2)
                        PyQt5.QtWidgets.QApplication.processEvents()
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=1;'
            command += 'var Out = "";'
            command += 'Out=ccdsoftCamera.LastImageFileName;'
            success, response = self.sendCommand(command)
            imageParams['Message'] = 'OK'
            imageParams['Imagepath'] = response
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            imageParams['Message'] = 'Request failed'
            imageParams['Imagepath'] = ''
        finally:
            return imageParams

    def connectCamera(self):
        if self.isRunning:
            tsxSocket = None
            try:
                tsxSocket = socket.socket()
                tsxSocket.connect((self.host, self.port))
                command = '/* Java Script */ '
                command += 'ccdsoftCamera.Connect();'
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                if tsxSocket:
                    tsxSocket.close()

    def disconnectCamera(self):
        if self.isRunning:
            tsxSocket = None
            try:
                tsxSocket = socket.socket()
                tsxSocket.connect((self.host, self.port))
                command = '/* Java Script */ '
                command += 'ccdsoftCamera.Disconnect();'
                self.sendCommand(command)
            except Exception as e:
                self.logger.error('error: {0}'.format(e))
            finally:
                if tsxSocket:
                    tsxSocket.close()
