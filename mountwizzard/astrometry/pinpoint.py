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
import numpy
import astropy.io.fits as pyfits
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
                self.app.messageQueue.put('Found Imaging: {0}\n'.format(self.application['Name']))
                self.logger.info('Name: {0}, Path: {1}'.format(self.application['Name'], self.application['InstallPath']))
            else:
                self.logger.info('Application PinPoint not found on computer')

    def start(self):
        pythoncom.CoInitialize()
        try:
            self.pinpoint = Dispatch('PinPoint.Plate')
            self.pinpoint.Catalog = 11
            self.pinpoint.CatalogPath = 'C:/UCAC4'
        except Exception as e:
            self.logger.info('Pinpoint could not be started, error:{0}'.format(e))
            self.application['Status'] = 'ERROR'
        finally:
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
            self.pinpoint.AttachFITS(imageParams['Imagepath'])
            self.pinpoint.ArcsecPerPixelHoriz = imageParams['ScaleHint']
            self.pinpoint.ArcsecPerPixelVert = imageParams['ScaleHint']
            self.pinpoint.RightAscension = self.pinpoint.TargetRightAscension
            self.pinpoint.Declination = self.pinpoint.TargetDeclination
            self.pinpoint.Solve()
            self.pinpoint.DetachFITS()
            imageParams['DecJ2000Solved'] = float(self.pinpoint.Declination)
            imageParams['RaJ2000Solved'] = float(self.pinpoint.RightAscension)
            imageParams['Scale'] = float(self.pinpoint.ArcsecPerPixelHoriz)
            imageParams['Angle'] = float(self.pinpoint.RollAngle)
            imageParams['TimeTS'] = 2.0
            imageParams['Solved'] = True
            imageParams['Message'] = 'OK'
        except Exception as e:
            self.pinpoint.DetachFITS()
            imageParams['Solved'] = False
            imageParams['Message'] = 'Solve failed'
            self.logger.error('PinPoint solving error -> error: {0}'.format(e))
        finally:
            pass
