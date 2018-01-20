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
import logging
import platform
import socket
import timeit
import time
import PyQt5


class TheSkyX(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200
    CYCLEPROPS = 3000

    CAMERASTATUS = {'Not Connected': 'DISCONNECTED', 'Downloading Light': 'IDLE', 'Exposure complete': 'IDLE', 'Ready': 'IDLE', 'Exposing Light': 'INTEGRATING'}

    def __init__(self, app, commandQueue):
        super().__init__()
        self.app = app
        self.commandQueue = commandQueue
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}
        self.data['Camera']['AppAvailable'] = True
        self.data['Camera']['AppName'] = 'None'
        self.data['Camera']['AppInstallPath'] = 'None'
        self.data['Solver']['AppAvailable'] = True
        self.data['Solver']['AppName'] = 'None'
        self.data['Solver']['AppInstallPath'] = 'None'
        self.data['Camera']['Status'] = '---'
        self.data['Camera']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Solver']['Status'] = '---'
        self.data['Solver']['CONNECTION'] = {'CONNECT': 'Off'}

        self.host = '127.0.0.1'
        self.port = 3040
        self.responseSuccess = '|No error. Error = 0.'
        self.appExe = 'TheSkyX.exe'
        if platform.system() == 'Windows':
            self.data['Camera']['AppAvailable'], self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath'] = self.app.checkRegistrationKeys('TheSkyX')
        else:
            self.data['Camera']['AppAvailable'] = True
            self.data['Camera']['AppName'] = 'TheSkyX'
            self.data['Camera']['AppInstallPath'] = ''
        if self.data['Camera']['AppAvailable']:
            self.app.messageQueue.put('Found: {0}\n'.format(self.data['Camera']['AppName']))
            self.logger.info('Name: {0}, Path: {1}'.format(self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath']))
        else:
            self.logger.info('Application TheSkyX not found on computer')
        self.data['Solver']['AppAvailable'] = self.data['Camera']['AppAvailable']
        self.data['Solver']['AppName'] = self.data['Camera']['AppName']
        self.data['Solver']['AppInstallPath'] = self.data['Camera']['AppInstallPath']

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.setStatus()
        self.setCameraProps()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            if not self.commandQueue.empty():
                command = self.commandQueue.get()
                if command['Command'] == 'GetImage':
                    command['ImageParams'] = self.getImage(command['ImageParams'])
                elif command['Command'] == 'SolveImage':
                    command['ImageParams'] = self.solveImage(command['ImageParams'])
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def setStatus(self):
        try:
            captureResponse = {}
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

        self.cameraStatus.emit(self.data['Camera']['Status'])
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

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.setStatus)

    def setCameraProps(self):
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
                    imageParams['Success'] = True
                    imageParams['Message'] = 'Solved'
                else:
                    imageParams['Success'] = False
                    imageParams['Message'] = 'Unsolved'
            else:
                imageParams['Success'] = False
                imageParams['Message'] = 'Request failed'
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            imageParams['Success'] = False
            imageParams['Message'] = 'Request failed'
        finally:
            return imageParams

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
            imageParams['Success'] = success
            imageParams['Message'] = 'OK'
            imageParams['Imagepath'] = response
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            imageParams['Success'] = False
            imageParams['Message'] = 'Request failed'
            imageParams['Imagepath'] = ''
        finally:
            return imageParams

