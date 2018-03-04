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
import requests


class SGPro:
    logger = logging.getLogger(__name__)

    # base definitions of class
    host = '127.0.0.1'
    port = 59590
    ipSGProBase = 'http://' + host + ':' + str(port)
    ipSGPro = 'http://' + host + ':' + str(port) + '/json/reply/'

    getDeviceStatusPath = 'SgGetDeviceStatus'
    getSolvedImageDataPath = 'SgGetSolvedImageData'
    solveImagePath = 'SgSolveImage'

    ASTROMETRY_STATUS = {'ERROR': 'ERROR', 'DISCONNECTED': 'DISCONNECTED', 'IDLE': 'IDLE', 'BUSY': 'BUSY'}

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.cancel = False
        self.mutexCancel = PyQt5.QtCore.QMutex()

        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = ''
        self.application['InstallPath'] = ''
        self.application['Status'] = ''
        self.application['Runtime'] = 'Sequence Generator.exe'

        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.application['Available'], self.application['Name'], self.application['InstallPath'] = self.app.checkRegistrationKeys('Sequence Generator')
            if self.application['Available']:
                self.app.messageQueue.put('Found: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application SGPro not found on computer')

    def setCancelAstrometry(self):
        self.mutexCancel.lock()
        self.cancel = True
        self.mutexCancel.unlock()

    def getStatus(self):
        # todo: SGPro does not report the status of the solver right. Even if not set in SGPro I get positive feedback and IDLE
        suc, state, message = self.SgGetDeviceStatus('PlateSolver')
        if suc:
            self.application['Status'] = 'OK'
            if state in self.ASTROMETRY_STATUS:
                self.data['Status'] = self.ASTROMETRY_STATUS[state]
                if self.ASTROMETRY_STATUS[state] == 'DISCONNECTED':
                    self.data['CONNECTION']['CONNECT'] = 'Off'
                else:
                    self.data['CONNECTION']['CONNECT'] = 'On'
            else:
                self.logger.error('Unknown solver status: {0}'.format(state))
        else:
            self.main.astrometryStatusText.emit('Not OK')
            self.data['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def solveImage(self, imageParams):
        self.mutexCancel.lock()
        self.cancel = False
        self.mutexCancel.unlock()

        # waiting for start solving
        timeSolvingStart = time.time()
        self.main.astrometryStatusText.emit('START')
        if imageParams['UseFitsHeader']:
            suc, mes, guid = self.SgSolveImage(imageParams['Imagepath'],
                                               BlindSolve=imageParams['Blind'],
                                               UseFitsHeaders=imageParams['UseFitsHeader'])
        else:
            suc, mes, guid = self.SgSolveImage(imageParams['Imagepath'],
                                               RaHint=imageParams['RaJ2000'],
                                               DecHint=imageParams['DecJ2000'],
                                               ScaleHint=imageParams['ScaleHint'],
                                               BlindSolve=imageParams['Blind'],
                                               UseFitsHeaders=imageParams['UseFitsHeader'])
        if not suc:
            self.logger.warning('Solver no start, message: {0}'.format(mes))
            self.main.astrometryStatusText.emit('ERROR')
            imageParams['Imagepath'] = ''
            return

        # loop for upload
        self.main.waitForUpload.wakeAll()
        self.main.astrometryStatusText.emit('UPLOAD')
        while not self.cancel:
            suc, state, mes = self.SgGetDeviceStatus('PlateSolver')
            if 'IDLE' in state:
                break
            self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
            time.sleep(0.1)

        # loop for solve
        self.main.waitForSolve.wakeAll()
        self.main.astrometryStatusText.emit('SOLVE')
        while True:
            solved, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SgGetSolvedImageData(guid)
            if solved:
                # solved gives the status for PinPoint
                break
            if 'ailed' in mes:
                # Failed or failed is in PlanWave, Astrometry
                print(mes)
                break
            self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        imageParams['Solved'] = solved

        # Loop for data
        self.main.waitForData.wakeAll()
        self.main.imageSolved.emit()
        self.main.astrometryStatusText.emit('GET DATA')
        while not self.cancel and solved:
            if solved:
                imageParams['RaJ2000Solved'] = float(ra_sol)
                imageParams['DecJ2000Solved'] = float(dec_sol)
                imageParams['Scale'] = float(scale)
                imageParams['Angle'] = float(angle)
                imageParams['TimeTS'] = float(timeTS)
                time.sleep(0.1)
            self.main.astrometrySolvingTime.emit('{0:02.0f}'.format(time.time()-timeSolvingStart))
            break

        # finally idle
        self.main.imageDataDownloaded.emit()
        self.main.waitForFinished.wakeAll()
        self.main.astrometryStatusText.emit('IDLE')
        self.main.astrometrySolvingTime.emit('')

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        data = {'Device': device}
        try:
            result = requests.post(self.ipSGPro + self.getDeviceStatusPath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            if 'Message' not in result:
                result['Message'] = 'None'
            return result['Success'], result['State'], result['Message']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', 'Request failed'

    def SgGetSolvedImageData(self, _guid):
        # reference {"Receipt":"00000000000000000000000000000000"}
        data = {'Receipt': _guid}
        try:
            result = requests.post(self.ipSGPro + self.getSolvedImageDataPath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message'], result['Ra'], result['Dec'], result['Scale'], result['Angle'], result['TimeToSolve']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', '', '', '', '', ''

    def SgSolveImage(self, path, RaHint=None, DecHint=None, ScaleHint=None, BlindSolve=False, UseFitsHeaders=False):
        # reference {"ImagePath":"String","RaHint":0,"DecHint":0,"ScaleHint":0,"BlindSolve":false,"UseFitsHeadersForHints":false}
        data = {"ImagePath": path, "BlindSolve": BlindSolve, "UseFitsHeadersForHints": UseFitsHeaders}
        if RaHint:
            data['RaHint'] = RaHint
        if DecHint:
            data['DecHint'] = DecHint
        if ScaleHint:
            data['ScaleHint'] = ScaleHint
        try:
            result = requests.post(self.ipSGPro + self.solveImagePath, data=bytes(json.dumps(data).encode('utf-8')))
            result = json.loads(result.text)
            return result['Success'], result['Message'], result['Receipt']
        except Exception as e:
            self.logger.error('error: {0}'.format(e))
            return False, 'Request failed', ''
