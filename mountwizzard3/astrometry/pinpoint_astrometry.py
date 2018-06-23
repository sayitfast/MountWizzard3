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
import PyQt5
import platform
import logging
from win32com.client.dynamic import Dispatch
import pythoncom


class PinPoint:
    logger = logging.getLogger(__name__)

    def __init__(self, main, app, data):
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
        self.application['Runtime'] = 'PinPoint.dll'
        self.pinpoint = None

        if platform.system() == 'Windows':
            # sgpro only supported on local machine
            self.application['Available'], self.application['Name'], self.application['InstallPath'] = self.app.checkRegistrationKeys('PinPoint')
            if self.application['Available']:
                self.app.messageQueue.put('Found Astrometry: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application PinPoint not found on computer')

        # slots:
        self.app.ui.btn_selectCatalogue.clicked.connect(self.setCatalogue)

    def setCatalogue(self):
        value = self.app.selectDir(self.app, 'Set PinPoint Star Catalogue', '/')
        if value != '':
            self.app.ui.le_pinpointCatalogue.setText(value)
        else:
            self.logger.warning('No catalogue file selected')

    def start(self):
        pythoncom.CoInitialize()
        try:
            if self.app.ui.le_pinpointCatalogue.text() != '':
                if 'UCAC4' in self.app.ui.le_pinpointCatalogue.text():
                    cat = 11
                elif 'GSC' in self.app.ui.le_pinpointCatalogue.text():
                    cat = 3
                elif 'UCAC3' in self.app.ui.le_pinpointCatalogue.text():
                    cat = 10
                elif 'USNO' in self.app.ui.le_pinpointCatalogue.text():
                    cat = 7
                else:
                    self.logger.info('Pinpoint catalogue could not be configured')
                    self.application['Status'] = 'ERROR'
                    self.app.messageQueue.put('#BRPinpoint catalogue could not be configured\n')
                    return
            else:
                self.logger.info('Pinpoint catalogue not defined')
                self.application['Status'] = 'ERROR'
                self.app.messageQueue.put('#BRPinpoint catalogue not defined !\n')
                return
            self.pinpoint = Dispatch('PinPoint.Plate')
            self.pinpoint.Catalog = cat
            self.pinpoint.CatalogPath = self.app.ui.le_pinpointCatalogue.text()
        except Exception as e:
            self.logger.info('Pinpoint could not be started, error:{0}'.format(e))
            self.application['Status'] = 'ERROR'
        finally:
            self.app.messageQueue.put('Catalogue path: {0}, number scheme PinPoint: {1}\n'.format(self.app.ui.le_pinpointCatalogue.text(), cat))
            pass

    def stop(self):
        try:
            if self.pinpoint:
                self.data['CONNECTION']['CONNECT'] = 'Off'
        except Exception as e:
            self.logger.error('Could not stop maxim, error: {0}'.format(e))
            self.application['Status'] = 'ERROR'
        finally:
            self.data['CONNECTION']['CONNECT'] = 'Off'
            self.pinpoint = None
            pythoncom.CoUninitialize()

    def getStatus(self):
        if self.pinpoint:
            self.data['CONNECTION']['CONNECT'] = 'On'
            self.application['Status'] = 'OK'
        else:
            self.application['Status'] = 'ERROR'
            self.data['CONNECTION']['CONNECT'] = 'Off'

    def solveImage(self, imageParams):

        try:
            # waiting for start solving
            self.main.astrometryStatusText.emit('START')
            if not self.pinpoint.AttachFITS(imageParams['Imagepath']):
                return
            self.pinpoint.ArcsecPerPixelHoriz = imageParams['ScaleHint']
            self.pinpoint.ArcsecPerPixelVert = imageParams['ScaleHint']
            self.pinpoint.RightAscension = self.pinpoint.TargetRightAscension
            self.pinpoint.Declination = self.pinpoint.TargetDeclination

            # loop for solve
            self.main.astrometryStatusText.emit('SOLVE')
            try:
                self.pinpoint.Solve()
                imageParams['Solved'] = True
            except pythoncom.com_error as e:
                imageParams['Solved'] = False
                imageParams['Message'] = e.excepinfo[2][:80]
            finally:
                pass
            # loop for get data
            self.main.astrometryStatusText.emit('GET DATA')
            self.pinpoint.DetachFITS()
            if imageParams['Solved']:
                imageParams['DecJ2000Solved'] = float(self.pinpoint.Declination)
                imageParams['RaJ2000Solved'] = float(self.pinpoint.RightAscension)
                imageParams['Scale'] = float(self.pinpoint.ArcsecPerPixelHoriz)
                imageParams['Angle'] = float(self.pinpoint.RollAngle)
                imageParams['TimeTS'] = 2.0
                imageParams['Message'] = 'OK'
            else:
                imageParams['DecJ2000Solved'] = 0
                imageParams['RaJ2000Solved'] = 0
                imageParams['Scale'] = 0
                imageParams['Angle'] = 0
                imageParams['TimeTS'] = 2.0

        except Exception as e:
            imageParams['Solved'] = False
            imageParams['Message'] = 'Solve failed'
            self.logger.error('PinPoint solving error -> error: {0}'.format(e))
        finally:
            pass

        # finally idle
        self.main.imageDataDownloaded.emit()
        self.main.astrometryStatusText.emit('IDLE')
        self.main.astrometrySolvingTime.emit('')
