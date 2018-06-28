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
import os
import time
import platform
import PyQt5
import queue
import astropy.io.fits as pyfits
from astrometry import transform
from imaging import none_camera
from imaging import indi_camera
if platform.system() == 'Windows':
    from imaging import maximdl_camera
    from imaging import sgpro_camera
if platform.system() == 'Windows' or platform.system() == 'Darwin':
    from imaging import theskyx_camera


class Imaging(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    # signals to be used for others
    # putting status to gui
    cameraStatusText = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)
    imagingCancel = PyQt5.QtCore.pyqtSignal()
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    # putting status to processing
    imageIntegrated = PyQt5.QtCore.pyqtSignal()
    imageDownloaded = PyQt5.QtCore.pyqtSignal()
    imageSaved = PyQt5.QtCore.pyqtSignal()

    # where to place the images
    IMAGEDIR = os.getcwd().replace('\\', '/') + '/images'
    CYCLE = 200
    CYCLE_STATUS = 1000

    def __init__(self, app, thread):
        super().__init__()
        # make main sources available
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.imagingCommandQueue = queue.Queue()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.mutexData = PyQt5.QtCore.QMutex()
        self.statusTimer = None
        self.cycleTimer = None

        # class data
        self.data = dict()
        self.data['CONNECTION'] = {'CONNECT': 'Off'}

        # external classes
        self.transform = transform.Transform(self.app)
        if platform.system() == 'Windows':
            self.SGPro = sgpro_camera.SGPro(self, self.app, self.data)
            self.MaximDL = maximdl_camera.MaximDL(self, self.app, self.data)
        self.INDICamera = indi_camera.INDICamera(self, self.app, self.data)
        self.NoneCam = none_camera.NoneCamera(self, self.app, self.data)

        # set the camera handler to default position
        self.cameraHandler = self.NoneCam

        # signal slot links
        self.imagingCancel.connect(self.setCancelImaging)
        self.app.ui.pd_chooseImaging.activated.connect(self.chooseImaging)

    def initConfig(self):
        # build the drop down menu
        self.app.ui.pd_chooseImaging.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseImaging.setView(view)
        if self.NoneCam.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('No Camera - ' + self.NoneCam.application['Name'])
        if self.INDICamera.application['Available']:
            self.app.ui.pd_chooseImaging.addItem('INDI Camera - ' + self.INDICamera.application['Name'])
        if platform.system() == 'Windows':
            if self.SGPro.application['Available']:
                self.app.ui.pd_chooseImaging.addItem('SGPro - ' + self.SGPro.application['Name'])
            if self.MaximDL.application['Available']:
                self.app.ui.pd_chooseImaging.addItem('MaximDL - ' + self.MaximDL.application['Name'])
        # if platform.system() == 'Windows' or platform.system() == 'Darwin':
        #    if self.workerTheSkyX.data['AppAvailable']:
        #        self.app.ui.pd_chooseImaging.addItem('TheSkyX - ' + self.workerTheSkyX.data['AppName'])
        # load the config data
        try:
            if 'ImagingApplication' in self.app.config:
                self.app.ui.pd_chooseImaging.setCurrentIndex(int(self.app.config['ImagingApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.chooseImaging()

    def storeConfig(self):
        self.app.config['ImagingApplication'] = self.app.ui.pd_chooseImaging.currentIndex()

    def setCancelImaging(self):
        self.cameraHandler.mutexCancel.lock()
        self.cameraHandler.cancel = True
        self.cameraHandler.mutexCancel.unlock()

    def chooseImaging(self):
        self.mutexChooser.lock()
        self.stop()
        if self.app.ui.pd_chooseImaging.currentText().startswith('No Camera'):
            self.cameraHandler = self.NoneCam
            self.logger.info('Actual camera is None')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('SGPro'):
            self.cameraHandler = self.SGPro
            self.logger.info('Actual camera is SGPro')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('MaximDL'):
            self.cameraHandler = self.MaximDL
            self.logger.info('Actual camera is MaximDL')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('INDI'):
            self.cameraHandler = self.INDICamera
            self.logger.info('Actual camera is INDI Camera')
        elif self.app.ui.pd_chooseImaging.currentText().startswith('TheSkyX'):
            self.cameraHandler = self.TheSkyX
            self.logger.info('Actual camera is TheSkyX')
        self.cameraStatusText.emit('')
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        self.logger.info('imaging started')
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.cameraHandler.start()
        # timers
        self.statusTimer = PyQt5.QtCore.QTimer(self)
        self.statusTimer.setSingleShot(False)
        self.statusTimer.timeout.connect(self.getStatusFromDevice)
        self.statusTimer.start(self.CYCLE_STATUS)
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('imaging stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.statusTimer.stop()
        self.cameraHandler.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.imagingCommandQueue.empty():
            imageParams = self.imagingCommandQueue.get()
            self.captureImage(imageParams)

    def captureImage(self, imageParams):
        imageParams['Imagepath'] = ''
        if self.cameraHandler.application['Status'] != 'OK':
            imageParams['Imagepath'] = 'False'
            return
        # preparation for imaging: gathering all the informations for taking a picture from gui
        imageParams['Imagepath'] = ''
        if self.data['CONNECTION']['CONNECT'] == 'Off':
            imageParams['Imagepath'] = 'False'
            return
        self.cameraHandler.getCameraProps()
        imageParams['BaseDirImages'] = self.IMAGEDIR + '/' + imageParams['Directory']
        if not os.path.isdir(imageParams['BaseDirImages']):
            os.makedirs(imageParams['BaseDirImages'])
        imageParams['Binning'] = int(self.app.ui.cameraBin.value())
        imageParams['Exposure'] = int(self.app.ui.cameraExposure.value())
        imageParams['Iso'] = int(self.app.ui.isoSetting.value())
        if self.app.ui.checkDoSubframe.isChecked():
            scaleSubframe = self.app.ui.scaleSubframe.value() / 100
            imageParams['SizeX'] = int(self.data['CCD_INFO']['CCD_MAX_X']) * scaleSubframe
            imageParams['SizeY'] = int(self.data['CCD_INFO']['CCD_MAX_Y']) * scaleSubframe
            imageParams['OffX'] = int((float(self.data['CCD_INFO']['CCD_MAX_X']) - imageParams['SizeX']) / 2)
            imageParams['OffY'] = int((float(self.data['CCD_INFO']['CCD_MAX_Y']) - imageParams['SizeY']) / 2)
            imageParams['CanSubframe'] = True
        else:
            imageParams['SizeX'] = int(self.data['CCD_INFO']['CCD_MAX_X'])
            imageParams['SizeY'] = int(self.data['CCD_INFO']['CCD_MAX_Y'])
            imageParams['OffX'] = 0
            imageParams['OffY'] = 0
            imageParams['CanSubframe'] = False
        if 'Gain' in self.data:
            imageParams['Gain'] = self.data['Gain']
        else:
            imageParams['Gain'] = 'NotSet'
        if self.app.ui.checkFastDownload.isChecked():
            imageParams['Speed'] = 'HiSpeed'
        else:
            imageParams['Speed'] = 'Normal'
        # setting mount conditions for the taken image
        imageParams['LocalSiderealTime'] = str(self.app.workerMountDispatcher.data['LocalSiderealTime'])
        imageParams['LocalSiderealTimeFloat'] = self.transform.degStringToDecimal(self.app.workerMountDispatcher.data['LocalSiderealTime'][0:9])
        imageParams['RaJ2000'] = float(self.app.workerMountDispatcher.data['RaJ2000'])
        imageParams['DecJ2000'] = float(self.app.workerMountDispatcher.data['DecJ2000'])
        imageParams['RaJNow'] = float(self.app.workerMountDispatcher.data['RaJNow'])
        imageParams['DecJNow'] = float(self.app.workerMountDispatcher.data['DecJNow'])
        imageParams['Pierside'] = str(self.app.workerMountDispatcher.data['Pierside'])
        imageParams['RefractionTemperature'] = float(self.app.workerMountDispatcher.data['RefractionTemperature'])
        imageParams['RefractionPressure'] = float(self.app.workerMountDispatcher.data['RefractionPressure'])
        self.logger.info('Params before imaging: {0}'.format(imageParams))
        # now we take the picture
        self.cameraHandler.getImage(imageParams)
        # if we got an image, than we work with it
        if os.path.isfile(imageParams['Imagepath']):
            # add the coordinates to the image of the telescope if not present
            fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
            fitsHeader = fitsFileHandle[0].header
            # if we are missing coordinates, we are replacing them with actual data from mount
            if 'OBJCTRA' not in fitsHeader:
                self.logger.warning('No OBJCTRA in FITS Header, writing')
            else:
                self.logger.info('OBJCTRA in header was: {0}'.format(fitsHeader['OBJCTRA']))
            if 'OBJCTDEC' not in fitsHeader:
                self.logger.warning('No OBJCTDEC in FITS Header, writing')
            else:
                self.logger.info('OBJCTDEC in header was: {0}'.format(fitsHeader['OBJCTDEC']))
            # setting coordinates explicit, because MW does slewing after imaging and MW does not know, when imaging application takes coordinates from mount driver
            fitsHeader['OBJCTRA'] = self.transform.decimalToDegree(imageParams['RaJ2000'], False, True, ' ')
            fitsHeader['OBJCTDEC'] = self.transform.decimalToDegree(imageParams['DecJ2000'], True, True, ' ')
            self.logger.info('OBJCTRA in header written: {0}'.format(fitsHeader['OBJCTRA']))
            self.logger.info('OBJCTDEC in header written: {0}'.format(fitsHeader['OBJCTDEC']))
            # if optical system data is missing in header, we replace them with data from GUI of mountwizzard
            if 'FOCALLEN' not in fitsHeader:
                fitsHeader['FOCALLEN'] = self.app.ui.focalLength.value()
                self.logger.warning('No FOCALLEN in FITS Header, writing')
            if 'XPIXSZ' not in fitsHeader:
                fitsHeader['XPIXSZ'] = self.app.ui.pixelSize.value() * self.app.ui.cameraBin.value()
                self.logger.warning('No XPIXSZ in FITS Header, writing')
            if 'PIXSIZE1' not in fitsHeader:
                fitsHeader['PIXSIZE1'] = self.app.ui.pixelSize.value()
                self.logger.warning('No PIXSIZE1 in FITS Header, writing')
            if 'YPIXSZ' not in fitsHeader:
                fitsHeader['YPIXSZ'] = self.app.ui.pixelSize.value() * self.app.ui.cameraBin.value()
                self.logger.warning('No YPIXSZ in FITS Header, writing')
            if 'PIXSIZE2' not in fitsHeader:
                fitsHeader['PIXSIZE2'] = self.app.ui.pixelSize.value()
                self.logger.warning('No PIXSIZE2 in FITS Header, writing')
            if 'XBINNING' not in fitsHeader:
                fitsHeader['XBINNING'] = self.app.ui.cameraBin.value()
                self.logger.warning('No XBINNING in FITS Header, writing')
            # refreshing FITS file with that data
            fitsFileHandle.flush()
            fitsFileHandle.close()
        else:
            pass
        # now imaging process is finished and told to everybody
        self.imageSaved.emit()
        self.data['Imaging'] = False
        # show it
        self.app.imageWindow.signalShowFitsImage.emit(imageParams['Imagepath'])

    @PyQt5.QtCore.pyqtSlot()
    def getStatusFromDevice(self):
        self.cameraHandler.getStatus()
        # get status to gui
        if not self.cameraHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'gray')
        elif self.cameraHandler.application['Status'] == 'ERROR':
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'red')
        elif self.cameraHandler.application['Status'] == 'OK':
            if self.data['CONNECTION']['CONNECT'] == 'Off':
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'yellow')
            else:
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_cameraConnected, 'color', 'green')

    def updateApplicationName(self):
        # updating camera name if possible
        for i in range(0, self.app.ui.pd_chooseImaging.count()):
            if self.app.ui.pd_chooseImaging.itemText(i).startswith('No Camera'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('SGPro'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('MaximDL'):
                pass
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('INDI'):
                self.app.ui.pd_chooseImaging.setItemText(i, 'INDI Camera - ' + self.INDICamera.application['Name'])
            elif self.app.ui.pd_chooseImaging.itemText(i).startswith('TheSkyX'):
                pass
