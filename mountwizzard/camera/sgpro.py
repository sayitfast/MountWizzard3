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
import time
import PyQt5
# packages for handling web interface to SGPro
from urllib import request


class SGPro(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 200
    CYCLEPROPS = 3000
    SOLVERSTATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'IDLE': 'IDLE', 'BUSY': 'BUSY'}
    CAMERASTATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'DOWNLOADING', 'READY': 'IDLE', 'IDLE': 'IDLE', 'INTEGRATING': 'INTEGRATING'}

    def __init__(self, app, commandQueue):
        super().__init__()
        self.app = app
        self.commandQueue = commandQueue
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}
        self.tryConnectionCounter = 0
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
        self.port = 59590
        self.ipSGProBase = 'http://' + self.host + ':' + str(self.port)
        self.ipSGPro = 'http://' + self.host + ':' + str(self.port) + '/json/reply/'
        self.captureImagePath = 'SgCaptureImage'
        self.connectDevicePath = 'SgConnectDevicePath'
        self.disconnectDevicePath = 'SgDisconnectDevicePath'
        self.getCameraPropsPath = 'SgGetCameraProps'
        self.getDeviceStatusPath = 'SgGetDeviceStatus'
        self.enumerateDevicePath = 'SgEnumerateDevices'
        self.getImagePath = 'SgGetImagePath'
        self.getSolvedImageDataPath = 'SgGetSolvedImageData'
        self.solveImagePath = 'SgSolveImage'

        self.appExe = 'Sequence Generator.exe'
        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.data['Camera']['AppAvailable'], self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.data['Camera']['AppAvailable']:
                self.app.messageQueue.put('Found: {0}\n'.format(self.data['Camera']['AppName']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.data['Camera']['AppName'], self.data['Camera']['AppInstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')
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
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def setStatus(self):
        suc, mes = self.SgGetDeviceStatus('Camera')
        if suc:
            if mes in self.CAMERASTATUS:
                self.data['Camera']['Status'] = self.CAMERASTATUS[mes]
                self.data['Camera']['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown camera status: {0}'.format(mes))
        else:
            self.data['Camera']['Status'] = 'ERROR'
            self.data['Camera']['CONNECTION']['CONNECT'] = 'Off'

        # todo: SGPro does not report the status of the solver right. Even if not set in SGPro I get positive feedback and IDLE
        suc, mes = self.SgGetDeviceStatus('PlateSolver')
        if suc:
            if mes in self.SOLVERSTATUS:
                self.data['Solver']['Status'] = self.SOLVERSTATUS[mes]
                self.data['Solver']['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown solver status: {0}'.format(mes))
        else:
            self.data['Solver']['Status'] = 'ERROR'
            self.data['Solver']['CONNECTION']['CONNECT'] = 'Off'

        self.cameraStatus.emit(self.data['Camera']['Status'])
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
                value = self.SgGetCameraProps()
                if value['Success']:
                    if 'GainValues' not in value['GainValues']:
                        self.data['Camera']['Gain'] = ['High']
                    else:
                        self.data['Camera']['Gain'] = value['GainValues']
                    self.data['Camera']['Message'] = value['Message']
                    if value['SupportsSubframe']:
                        self.data['Camera']['CCD_FRAME'] = {}
                        self.data['Camera']['CCD_FRAME']['HEIGHT'] = value['NumPixelsX']
                        self.data['Camera']['CCD_FRAME']['WIDTH'] = value['NumPixelsY']
                        self.data['Camera']['CCD_FRAME']['X'] = 0
                        self.data['Camera']['CCD_FRAME']['Y'] = 0
                    self.data['Camera']['CCD_INFO'] = {}
                    self.data['Camera']['CCD_INFO']['CCD_MAX_X'] = value['NumPixelsX']
                    self.data['Camera']['CCD_INFO']['CCD_MAX_Y'] = value['NumPixelsY']

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLEPROPS, self.setCameraProps)

    def getImage(self, imageParams):
        suc, mes, guid = self.SgCaptureImage(binningMode=imageParams['Binning'],
                                             exposureLength=imageParams['Exposure'],
                                             iso=str(imageParams['Iso']),
                                             gain='Not Set',
                                             speed=imageParams['Speed'],
                                             frameType='Light',
                                             filename=imageParams['File'],
                                             path=imageParams['BaseDirImages'],
                                             useSubframe=imageParams['CanSubframe'],
                                             posX=imageParams['OffX'],
                                             posY=imageParams['OffY'],
                                             width=imageParams['SizeX'],
                                             height=imageParams['SizeY'])
        imageParams['Imagepath'] = ''
        self.logger.info('message: {0}'.format(mes))
        if suc:
            while True:
                suc, imageParams['Imagepath'] = self.SgGetImagePath(guid)
                if suc:
                    break
                else:
                    time.sleep(0.2)
                    PyQt5.QtWidgets.QApplication.processEvents()
        else:
            imageParams['Imagepath'] = ''
        imageParams['Success'] = suc
        imageParams['Message'] = mes
        return imageParams

    def solveImage(self, imageParams):
        suc, mes, guid = self.SgSolveImage(imageParams['Imagepath'],
                                           scaleHint=imageParams['ScaleHint'],
                                           blindSolve=imageParams['Blind'],
                                           useFitsHeaders=imageParams['UseFitsHeaders'])
        if not suc:
            self.logger.warning('Solver no start, message: {0}'.format(mes))
            imageParams['Success'] = False
            imageParams['Message'] = mes
            return imageParams
        while True:
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)
            mes = mes.strip('\n')
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:
                self.logger.info('Imaging parameters {0}'.format(imageParams))
                solved = True
                imageParams['RaJ2000Solved'] = float(ra_sol)
                imageParams['DecJ2000Solved'] = float(dec_sol)
                imageParams['Scale'] = float(scale)
                imageParams['Angle'] = float(angle)
                imageParams['TimeTS'] = float(timeTS)
                break
            elif mes != 'Solving':
                solved = False
                break
            # TODO: clarification should we again introduce model run cancel during plate solving -> very complicated solver should cancel if not possible after some time
            # elif app.model.cancel:
            #    solved = False
            #    break
            else:
                time.sleep(0.2)
                PyQt5.QtWidgets.QApplication.processEvents()
        imageParams['Success'] = solved
        imageParams['Message'] = mes
        return mimageParams

    def SgCaptureImage(self, binningMode=1, exposureLength=1,
                       gain=None, iso=None, speed=None, frameType=None, filename=None,
                       path=None, useSubframe=False, posX=0, posY=0,
                       width=1, height=1):
        # reference {"BinningMode":0,"ExposureLength":0,"Gain":"String","Speed":"Normal","FrameType":"Light",
        # reference "Path":"String","UseSubframe":false,"X":0,"Y":0,"Width":0,"Height":0}
        data = {"BinningMode": binningMode, "ExposureLength": exposureLength, "UseSubframe": useSubframe, "X": posX, "Y": posY,
                "Width": width, "Height": height}
        if gain:
            data['Gain'] = gain
        if iso:
            data['Iso'] = iso
        if speed:
            data['Speed'] = speed
        if frameType:
            data['FrameType'] = frameType
        if path and filename:
            data['Path'] = path + '/' + filename
        try:
            req = request.Request(self.ipSGPro + self.captureImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgGetCameraProps(self):
        # reference {}
        data = {}
        try:
            req = request.Request(self.ipSGPro + self.getCameraPropsPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            return captureResponse
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', ''

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            req = request.Request(self.ipSGPro + self.getDeviceStatusPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # states are  "IDLE", "CAPTURING", "BUSY", "MOVING", "DISCONNECTED", "PARKED"
            # {"State":"IDLE","Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['State']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetImagePath(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.getImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String"}
            return captureResponse['Success'], captureResponse['Message']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetSolvedImageData(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            req = request.Request(self.ipSGPro + self.getSolvedImageDataPath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))
            # {"Success":false,"Message":"String","Ra":0,"Dec":0,"Scale":0,"Angle":0,"TimeToSolve":0}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Ra'], captureResponse['Dec'], captureResponse['Scale'], captureResponse['Angle'], captureResponse['TimeToSolve']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, path, raHint=None, decHint=None, scaleHint=None, blindSolve=False, useFitsHeaders=False):
        # reference {"ImagePath":"String","RaHint":0,"DecHint":0,"ScaleHint":0,"BlindSolve":false,"UseFitsHeadersForHints":false}
        data = {"ImagePath": path, "BlindSolve": blindSolve, "UseFitsHeadersForHints": useFitsHeaders}
        if raHint:
            data['RaHint'] = raHint
        if decHint:
            data['DecHint'] = decHint
        if scaleHint:
            data['ScaleHint'] = scaleHint
        try:
            req = request.Request(self.ipSGPro + self.solveImagePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as f:
                captureResponse = json.loads(f.read().decode('utf-8'))                                                      # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return captureResponse['Success'], captureResponse['Message'], captureResponse['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''
