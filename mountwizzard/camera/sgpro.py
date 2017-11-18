############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
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

    CYCLESTATUS = 200
    SOLVERSTATUS = {'ERROR': 'Error', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'BUSY', }
    CAMERASTATUS = {'ERROR': 'Error', 'DISCONNECTED': 'DISCONNECTED', 'BUSY': 'DOWNLOADING', 'READY': 'IDLE', 'IDLE': 'IDLE', 'INTEGRATING': 'INTEGRATING'}

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {}

        self.cameraConnected = False
        self.data['CameraStatus'] = 'DISCONNECTED'
        self.solverConnected = False
        self.data['SolverStatus'] = 'DISCONNECTED'
        self.tryConnectionCounter = 0

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
        self.checkAppInstall()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.getStatus()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        '''
        while self.isRunning:
            # time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()
        '''

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        # if no running main loop is necessary, finished emit moves to stop directly
        self.finished.emit()

    def checkAppInstall(self):
        if platform.system() == 'Windows':
            self.data['AppAvailable'], self.data['AppName'], self.data['AppInstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.data['AppAvailable']:
                self.app.messageQueue.put('Found: {0}'.format(self.data['AppName']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.data['AppName'], self.data['AppInstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')

    def getStatus(self):
        suc, mes = self.SgGetDeviceStatus('Camera')
        if suc:
            self.cameraConnected = True
            if mes in self.CAMERASTATUS:
                self.data['CameraStatus'] = self.CAMERASTATUS[mes]
                if self.data['CameraStatus'] == 'DISCONNECTED':
                    self.cameraConnected = False
            else:
                print('error status {0}'.format(mes))
        else:
            self.data['CameraStatus'] = 'ERROR'
            self.cameraConnected = False

        suc, mes = self.SgGetDeviceStatus('PlateSolver')
        if suc:
            self.solverConnected = True
            if mes in self.SOLVERSTATUS:
                self.data['SolverStatus'] = self.SOLVERSTATUS[mes]
                if self.data['SolverStatus'] == 'DISCONNECTED':
                    self.solverConnected = False
                else:
                    print('error status {0}'.format(mes))
        else:
            self.data['SolverStatus'] = 'ERROR'
            self.solverConnected = False

        if self.cameraConnected and self.solverConnected:
            self.app.workerModelingDispatcher.signalStatusImagingApp.emit(3)
        else:
            self.app.workerModelingDispatcher.signalStatusImagingApp.emit(2)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.getStatus)

    def getImage(self, modelData):
        suc, mes, guid = self.SgCaptureImage(binningMode=modelData['Binning'],
                                             exposureLength=modelData['Exposure'],
                                             iso=str(modelData['Iso']),
                                             gain=modelData['GainValue'],
                                             speed=modelData['Speed'],
                                             frameType='Light',
                                             filename=modelData['File'],
                                             path=modelData['BaseDirImages'],
                                             useSubframe=modelData['CanSubframe'],
                                             posX=modelData['OffX'],
                                             posY=modelData['OffY'],
                                             width=modelData['SizeX'],
                                             height=modelData['SizeY'])
        modelData['ImagePath'] = ''
        self.logger.info('message: {0}'.format(mes))
        if suc:
            while True:
                suc, modelData['ImagePath'] = self.SgGetImagePath(guid)
                if suc:
                    break
                else:
                    time.sleep(0.5)
        return suc, mes, modelData

    def solveImage(self, modelData):
        suc, mes, guid = self.SgSolveImage(modelData['ImagePath'],
                                           scaleHint=modelData['ScaleHint'],
                                           blindSolve=modelData['Blind'],
                                           useFitsHeaders=modelData['UseFitsHeaders'])
        if not suc:
            self.logger.warning('no start {0}'.format(mes))
            return False, mes, modelData
        while True:                                                                                                         # retrieving solving data in loop
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)                               # retrieving the data from solver
            mes = mes.strip('\n')                                                                                           # sometimes there are heading \n in message
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:                                                     # if there is success, we can move on
                self.logger.info('modelData {0}'.format(modelData))
                solved = True
                modelData['RaJ2000Solved'] = float(ra_sol)
                modelData['DecJ2000Solved'] = float(dec_sol)                                                                       # convert values to float, should be stored in float not string
                modelData['Scale'] = float(scale)
                modelData['Angle'] = float(angle)
                modelData['TimeTS'] = float(timeTS)
                break
            elif mes != 'Solving':                                                                                          # general error
                solved = False
                break
            # TODO: clarification should we again introduce model run cancel during plate solving -> very complicated solver should cancel if not possible after some time
            # elif app.model.cancel:
            #    solved = False
            #    break
            else:                                                                                                           # otherwise
                if modelData['Blind']:                                                                                      # when using blind solve, it takes 30-60 s
                    time.sleep(5)                                                                                           # therefore slow cycle
                else:                                                                                                       # local solver takes 1-2 s
                    time.sleep(.25)                                                                                         # therefore quicker cycle
        return solved, mes, modelData

    def getCameraProps(self):
        return self.SgGetCameraProps()

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
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            if 'GainValues' not in captureResponse:
                captureResponse['GainValues'] = ['High']
            return captureResponse['Success'], captureResponse['Message'], int(captureResponse['NumPixelsX']), int(captureResponse['NumPixelsY']), captureResponse['SupportsSubframe'], captureResponse['GainValues'][0]
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
