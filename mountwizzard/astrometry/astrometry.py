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
import logging
import time
import platform
import PyQt5
import queue
import astropy.io.fits as pyfits

from astrometry import astrometryClient
from astrometry import sgpro_solve
from astrometry import noneSolver


class Astrometry(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    # signals to be used for others
    # putting status to gui
    astrometryStatusText = PyQt5.QtCore.pyqtSignal(str)
    astrometrySolvingTime = PyQt5.QtCore.pyqtSignal(str)
    astrometryCancel = PyQt5.QtCore.pyqtSignal()

    # putting status to processing
    imageUploaded = PyQt5.QtCore.pyqtSignal()
    imageSolved = PyQt5.QtCore.pyqtSignal()
    imageDataDownloaded = PyQt5.QtCore.pyqtSignal()

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

        # class data
        self.data = dict()
        self.data['CONNECTION'] = {'CONNECT': 'Off'}

        # external classes
        self.SGPro = sgpro_solve.SGPro(self, self.app, self.data)
        self.AstrometryClient = astrometryClient.AstrometryClient(self, self.app, self.data)
        self.NoneSolve = noneSolver.NoneSolver(self, self.app, self.data)

        # shortcuts for better usage
        self.astrometryHandler = self.NoneSolve

        # signal slot links
        self.astrometryCancel.connect(self.setCancelAstrometry)
        self.app.ui.pd_chooseAstrometry.currentIndexChanged.connect(self.chooseAstrometry)

    def initConfig(self):
        # build the drop down menu
        self.app.ui.pd_chooseAstrometry.clear()
        view = PyQt5.QtWidgets.QListView()
        self.app.ui.pd_chooseAstrometry.setView(view)

        if self.NoneSolve.application['Available']:
            self.app.ui.pd_chooseAstrometry.addItem('No Solver - ' + self.NoneSolve.application['Name'])
        if self.AstrometryClient.application['Available']:
            self.app.ui.pd_chooseAstrometry.addItem('Astrometry - ' + self.AstrometryClient.application['Name'])
        if platform.system() == 'Windows':
            if self.SGPro.application['Available']:
                self.app.ui.pd_chooseAstrometry.addItem('SGPro - ' + self.SGPro.application['Name'])
        #    if self.workerMaximDL.data['AppAvailable']:
        #        self.app.ui.pd_chooseAstrometry.addItem('MaximDL - ' + self.workerMaximDL.data['AppName'])
        #if platform.system() == 'Windows' or platform.system() == 'Darwin':
        #    if self.workerTheSkyX.data['AppAvailable']:
        #        self.app.ui.pd_chooseAstrometry.addItem('TheSkyX - ' + self.workerTheSkyX.data['AppName'])
        # load the config data
        try:
            if 'AstrometryApplication' in self.app.config:
                self.app.ui.pd_chooseAstrometry.setCurrentIndex(int(self.app.config['AstrometryApplication']))
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass
        self.AstrometryClient.initConfig()
        self.chooseAstrometry()

    def storeConfig(self):
        self.app.config['AstrometryApplication'] = self.app.ui.pd_chooseAstrometry.currentIndex()
        self.AstrometryClient.storeConfig()

    def setCancelAstrometry(self):
        self.astrometryHandler.mutexCancel.lock()
        self.astrometryHandler.cancel = True
        self.astrometryHandler.mutexCancel.unlock()

    def chooseAstrometry(self):
        self.mutexChooser.lock()
        if self.app.ui.pd_chooseAstrometry.currentText().startswith('No Solver'):
            self.astrometryHandler = self.NoneSolve
            self.logger.info('Actual plate solver is None')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('SGPro'):
            self.astrometryHandler = self.SGPro
            self.logger.info('Actual plate solver is SGPro')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('MaximDL'):
            self.astrometryHandler = self.MaximDL
            self.logger.info('Actual plate solver is MaximDL')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('Astrometry'):
            self.astrometryHandler = self.AstrometryClient
            self.logger.info('Actual plate solver is ASTROMETRY.NET')
        elif self.app.ui.pd_chooseAstrometry.currentText().startswith('TheSkyX'):
            self.astrometryHandler = self.TheSkyX
            self.logger.info('Actual plate solver is TheSkyX')
        self.astrometryStatusText.emit('')
        self.mutexChooser.unlock()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.getStatus()
        while self.isRunning:
            if not self.astrometryCommandQueue.empty():
                imageParams = self.astrometryCommandQueue.get()
                self.solveImage(imageParams)
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def solveImage(self, imageParams):
        if self.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # check for blind solve:
        imageParams['Blind'] = self.app.ui.checkUseBlindSolve.isChecked()
        # check for use of FITS data
        imageParams['UseFitsHeader'] = self.app.ui.checkUseFitsHeader.isChecked()
        # if fits data, check if scale hint was calculated
        if not os.path.isfile(imageParams['Imagepath']):
            return
        fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
        fitsHeader = fitsFileHandle[0].header
        if 'PIXSCALE' not in fitsHeader:
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                scaleHint = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
            if 'FOCALLEN' in fitsHeader and 'PIXSIZE1' in fitsHeader:
                scaleHint = float(fitsHeader['PIXSIZE1']) * 206.6 / float(fitsHeader['FOCALLEN'])
            fitsHeader['PIXSCALE'] = str(scaleHint)
            fitsFileHandle.flush()
        fitsFileHandle.close()
        self.astrometryHandler.solveImage(imageParams)

    def getStatus(self):
        self.astrometryHandler.getStatus()
        # get status to gui
        if not self.astrometryHandler.application['Available']:
            self.app.ui.btn_astrometryConnected.setStyleSheet('QPushButton {background-color: gray;color: black;}')
        elif self.astrometryHandler.application['Status'] == 'ERROR':
            self.app.ui.btn_astrometryConnected.setStyleSheet('QPushButton {background-color: red; color: black;}')
        elif self.astrometryHandler.application['Status'] == 'OK':
            if self.data['CONNECTION']['CONNECT'] == 'Off':
                self.app.ui.btn_astrometryConnected.setStyleSheet('QPushButton {background-color: yellow; color: black;}')
            else:
                self.app.ui.btn_astrometryConnected.setStyleSheet('QPushButton {background-color: green; color: black;}')

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_STATUS, self.getStatus)

    def updateApplicationName(self):
        # updating solver name name if possible
        for i in range(0, self.app.ui.pd_chooseAstrometry.count()):
            if self.app.ui.pd_chooseAstrometry.itemText(i).startswith('No Solve'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('SGPro'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('MaximDL'):
                pass
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('Astrometry'):
                self.app.ui.pd_chooseAstrometry.setItemText(i, 'Astrometry - ' + self.AstrometryClient.application['Name'])
            elif self.app.ui.pd_chooseAstrometry.itemText(i).startswith('TheSkyX'):
                pass
