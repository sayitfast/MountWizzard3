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
import platform
import PyQt5
import time
import queue
import os
import astropy.io.fits as pyfits

from astrometry import client_astrometry
if platform.system() == 'Windows':
    from astrometry import sgpro_astrometry
    from astrometry import pinpoint_astrometry
from astrometry import none_astrometry
from astrometry import transform


class Astrometry(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    # signals to be used for others
    # putting status to gui
    astrometryStatusText = PyQt5.QtCore.pyqtSignal(str)
    astrometrySolvingTime = PyQt5.QtCore.pyqtSignal(str)
    astrometryCancel = PyQt5.QtCore.pyqtSignal()
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    # putting status to processing
    imageUploaded = PyQt5.QtCore.pyqtSignal()
    imageSolved = PyQt5.QtCore.pyqtSignal()
    imageDataDownloaded = PyQt5.QtCore.pyqtSignal()

    CYCLE = 200
    CYCLE_STATUS = 1000

    def __init__(self, app, thread):
        super().__init__()
        # make main sources available
        self.app = app
        self.thread = thread
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.astrometryCommandQueue = queue.Queue()
        self.mutexChooser = PyQt5.QtCore.QMutex()
        self.transform = transform.Transform(self.app)
        self.statusTimer = None
        self.cycleTimer = None

        # class data
        self.data = dict()
        self.data['CONNECTION'] = {'CONNECT': 'Off'}

        # external classes
        self.AstrometryClient = client_astrometry.AstrometryClient(self, self.app, self.data)
        if platform.system() == 'Windows':
            self.SGPro = sgpro_astrometry.SGPro(self, self.app, self.data)
            self.PinPoint = pinpoint_astrometry.PinPoint(self, self.app, self.data)
        self.NoneSolve = none_astrometry.NoneAstrometry(self, self.app, self.data)

        # set handler to default position
        self.astrometryHandler = self.NoneSolve

        # signal slot links
        self.astrometryCancel.connect(self.setCancelAstrometry)
        self.app.ui.pd_chooseAstrometry.activated.connect(self.chooseAstrometry)

    def initConfig(self):
        # build the drop down menu
        self.app.ui.pd_chooseAstrometry.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseAstrometry.setView(view)
        if self.NoneSolve.application['Available']:
            self.app.ui.pd_chooseAstrometry.addItem('No Astrometry - ' + self.NoneSolve.application['Name'])
        if self.AstrometryClient.application['Available']:
            self.app.ui.pd_chooseAstrometry.addItem('Astrometry - ' + self.AstrometryClient.application['Name'])
        if platform.system() == 'Windows':
            if self.SGPro.application['Available']:
                self.app.ui.pd_chooseAstrometry.addItem('SGPro - ' + self.SGPro.application['Name'])
            if self.PinPoint.application['Available']:
                self.app.ui.pd_chooseAstrometry.addItem('PinPoint - ' + self.PinPoint.application['Name'])
        # if platform.system() == 'Windows' or platform.system() == 'Darwin':
        #    if self.workerTheSkyX.data['AppAvailable']:
        #        self.app.ui.pd_chooseAstrometry.addItem('TheSkyX - ' + self.workerTheSkyX.data['AppName'])
        # load the config data
        if 'PinPointCatalogue' in self.app.config:
            self.app.ui.le_pinpointCatalogue.setText(self.app.config['PinPointCatalogue'])
        try:
            if 'AstrometryApplication' in self.app.config:
                self.app.ui.pd_chooseAstrometry.setCurrentIndex(int(self.app.config['AstrometryApplication']))
        except Exception as e:
            self.logger.error('Item in config.cfg for astrometry could not be initialized, error:{0}'.format(e))
        finally:
            pass
        self.AstrometryClient.initConfig()
        if platform.system() == 'Windows':
            self.SGPro.initConfig()
        self.chooseAstrometry()

    def storeConfig(self):
        self.app.config['AstrometryApplication'] = self.app.ui.pd_chooseAstrometry.currentIndex()
        self.app.config['PinPointCatalogue'] = self.app.ui.le_pinpointCatalogue.text()
        if platform.system() == 'Windows':
            self.SGPro.storeConfig()
        self.AstrometryClient.storeConfig()

    def setCancelAstrometry(self):
        self.astrometryHandler.mutexCancel.lock()
        self.astrometryHandler.cancel = True
        self.astrometryHandler.mutexCancel.unlock()

    def chooseAstrometry(self):
        self.mutexChooser.lock()
        self.stop()
        if self.app.ui.pd_chooseAstrometry.currentText().startswith('No Astrometry'):
            self.astrometryHandler = self.NoneSolve
            self.logger.info('Actual plate solver is None')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('SGPro'):
            self.astrometryHandler = self.SGPro
            self.logger.info('Actual plate solver is SGPro')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('PinPoint'):
            self.astrometryHandler = self.PinPoint
            self.logger.info('Actual plate solver is PinPoint')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('Astrometry'):
            self.astrometryHandler = self.AstrometryClient
            self.logger.info('Actual plate solver is ASTROMETRY.NET')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('TheSkyX'):
            self.astrometryHandler = self.TheSkyX
            self.logger.info('Actual plate solver is TheSkyX')
        self.astrometryStatusText.emit('')
        if not self.astrometryHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'gray')
        else:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'red')
        self.thread.start()
        self.mutexChooser.unlock()

    def run(self):
        self.logger.info('astrometry started')
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.astrometryHandler.start()
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
        self.logger.info('astrometry stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.statusTimer.stop()
        self.astrometryHandler.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.astrometryCommandQueue.empty():
            imageParams = self.astrometryCommandQueue.get()
            self.solveImage(imageParams)

    def solveImage(self, imageParams):
        dataPresentForSolving = True
        if self.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # reset message
        imageParams['Message'] = 'Cancelled'
        # check for use of FITS data
        if not os.path.isfile(imageParams['Imagepath']):
            return
        # open the fits header and check content.
        # we need for solving "OBJCTRA", "OBJCTDEC" and "PIXSCALE" field
        fitsFileHandle = pyfits.open(imageParams['Imagepath'])
        fitsHeader = fitsFileHandle[0].header
        if 'OBJCTRA' in fitsHeader:
            imageParams['RaJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTRA'], ' ')
        else:
            self.logger.error('FITS data OBJCTRA for start solving is missing, present headers: {0}'.format(fitsHeader))
            dataPresentForSolving = False
        if 'OBJCTDEC' in fitsHeader:
            imageParams['DecJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTDEC'], ' ')
        else:
            self.logger.error('FITS data OBJCTDEC for start solving is missing, present headers: {0}'.format(fitsHeader))
            dataPresentForSolving = False
        if 'PIXSCALE' in fitsHeader:
            imageParams['ScaleHint'] = fitsHeader['PIXSCALE']
        else:
            self.logger.info('FITS data PIXSCALE for start solving is missing try to recalculate')
            # now trying to recalculate this value
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                if float(fitsHeader['FOCALLEN']) > 0:
                    imageParams['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
                else:
                    self.logger.error('FITS data FOCALLEN is 0 -> cannot solve, present headers: {0}'.format(fitsHeader))
                    dataPresentForSolving = False
            elif 'FOCALLEN' in fitsHeader and 'PIXSIZE1' in fitsHeader and 'XBINNING' in fitsHeader:
                if float(fitsHeader['FOCALLEN']) > 0:
                    imageParams['ScaleHint'] = float(fitsHeader['PIXSIZE1']) * 206.6 / float(fitsHeader['FOCALLEN']) * float(fitsHeader['XBINNING'])
                else:
                    self.logger.error('FITS data FOCALLEN is 0 -> cannot solve, present headers: {0}'.format(fitsHeader))
                    dataPresentForSolving = False
            else:
                # if we cannot recalculate, there is no chance to get this parameter
                self.logger.error('FITS data FOCALLEN or XPIXSZ or PIXSIZE1 or XBINNING for start solving is missing, present headers: {0}'.format(fitsHeader))
                dataPresentForSolving = False
        fitsFileHandle.close()
        if dataPresentForSolving:
            self.logger.info('Params before solving: {0}'.format(imageParams))
            self.astrometryHandler.solveImage(imageParams)
            self.logger.info('Params after solving: {0}'.format(imageParams))
            if self.app.imageWindow.showStatus:
                if 'Solved' in imageParams:
                    if imageParams['Solved']:
                        self.app.imageWindow.signalSetRaSolved.emit(self.transform.decimalToDegree(imageParams['RaJ2000Solved'], False, False))
                        self.app.imageWindow.signalSetDecSolved.emit(self.transform.decimalToDegree(imageParams['DecJ2000Solved'], True, False))
                        self.app.imageWindow.signalSetAngleSolved.emit('{0:3.1f}'.format(imageParams['Angle']))
                    else:
                        self.app.imageWindow.signalSetRaSolved.emit('not solved')
                        self.app.imageWindow.signalSetDecSolved.emit('not solved')
                        self.app.imageWindow.signalSetAngleSolved.emit('-')
                else:
                    self.app.imageWindow.signalSetRaSolved.emit('not solved')
                    self.app.imageWindow.signalSetDecSolved.emit('not solved')
                    self.app.imageWindow.signalSetAngleSolved.emit('-')
        else:
            imageParams['Solved'] = False
            imageParams['Message'] = 'FITS header parameters missing'
            self.app.imageWindow.signalSetRaSolved.emit('no data')
            self.app.imageWindow.signalSetDecSolved.emit('no data')
            self.app.imageWindow.signalSetAngleSolved.emit('-')

    @PyQt5.QtCore.pyqtSlot()
    def getStatusFromDevice(self):
        # get status to gui
        if not self.astrometryHandler.application['Available']:
            self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'gray')
        else:
            self.astrometryHandler.getStatus()
            if self.astrometryHandler.application['Status'] == 'ERROR':
                self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'red')
            elif self.astrometryHandler.application['Status'] in ['OK', '']:
                if self.data['CONNECTION']['CONNECT'] == 'Off':
                    self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'yellow')
                else:
                    self.app.signalChangeStylesheet.emit(self.app.ui.btn_astrometryConnected, 'color', 'green')
            else:
                self.logger.warning('This state is undefined')

    def updateApplicationName(self):
        # updating solver name name if possible
        for i in range(0, self.app.ui.pd_chooseAstrometry.count()):
            if self.app.ui.pd_chooseAstrometry.itemText(i).startswith('No Astrometry'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('SGPro'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('MaximDL'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('Astrometry'):
                self.app.ui.pd_chooseAstrometry.setItemText(i, 'Astrometry - ' + self.AstrometryClient.application['Name'])
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('TheSkyX'):
                pass
