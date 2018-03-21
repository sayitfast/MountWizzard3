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
import logging
import copy
import os
import shutil
import time
import math
import PyQt5
import indi.indi_xml as indiXML
from analyse import analysedata
from modeling import modelingPoints
from queue import Queue
from astrometry import transform
import astropy.io.fits as pyfits


class Slewpoint(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePoint = Queue()
    signalStartSlewing = PyQt5.QtCore.pyqtSignal()
    signalPointImaged = PyQt5.QtCore.pyqtSignal(float, float)

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexTakeNextPoint = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.takeNextPoint = False
        self.signalStartSlewing.connect(self.startSlewing)

    def startSlewing(self):
        self.mutexTakeNextPoint.lock()
        self.takeNextPoint = True
        self.mutexTakeNextPoint.unlock()

    def run(self):
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        while self.isRunning:
            if self.takeNextPoint and not self.queuePoint.empty():
                self.mutexTakeNextPoint.lock()
                self.takeNextPoint = False
                self.mutexTakeNextPoint.unlock()
                modelingData = self.queuePoint.get()
                self.main.app.messageQueue.put('#BGSlewing to point {0:2d}  @ Az: {1:3.0f}\xb0 Alt: {2:2.0f}\xb0\n'.format(modelingData['Index'] + 1, modelingData['Azimuth'], modelingData['Altitude']))
                self.main.slewMountDome(modelingData)
                self.main.app.messageQueue.put('\tWait mount settling / delay time:  {0:02d} sec\n'.format(modelingData['SettlingTime']))
                self.main.app.messageQueue.put('Slewed>{0:02d}'.format(modelingData['Index'] + 1))
                timeCounter = modelingData['SettlingTime'] * 10
                while timeCounter > 0:
                    timeCounter -= 1
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
                self.main.workerImage.queueImage.put(modelingData)
                # make signal for hemisphere that point is imaged
                self.signalPointImaged.emit(modelingData['Azimuth'], modelingData['Altitude'])
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.queuePoint.queue.clear()
        self.thread.quit()
        self.thread.wait()


class Image(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queueImage = Queue()
    signalImaging = PyQt5.QtCore.pyqtSignal()

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.isRunning = True
        self.imageIntegrated = False
        self.imageSaved = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexImageIntegrated = PyQt5.QtCore.QMutex()
        self.mutexImageSaved = PyQt5.QtCore.QMutex()
        self.main.app.workerImaging.imageIntegrated.connect(self.setImageIntegrated)
        self.main.app.workerImaging.imageSaved.connect(self.setImageSaved)

    def setImageIntegrated(self):
        self.mutexImageIntegrated.lock()
        self.imageIntegrated = True
        self.mutexImageIntegrated.unlock()

    def setImageSaved(self):
        self.mutexImageSaved.lock()
        self.imageSaved = True
        self.mutexImageSaved.unlock()

    def run(self):
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        while self.isRunning:
            if not self.queueImage.empty():
                modelingData = self.queueImage.get()
                self.mutexImageSaved.lock()
                self.imageSaved = False
                self.mutexImageSaved.unlock()
                self.mutexImageIntegrated.lock()
                self.imageIntegrated = False
                self.mutexImageIntegrated.unlock()
                modelingData['File'] = 'Model_Image_' + '{0:03d}'.format(modelingData['Index']) + '.fit'
                modelingData['LocalSiderealTime'] = self.main.app.workerMountDispatcher.data['LocalSiderealTime']
                modelingData['LocalSiderealTimeFloat'] = self.main.transform.degStringToDecimal(self.main.app.workerMountDispatcher.data['LocalSiderealTime'][0:9])
                modelingData['RaJ2000'] = self.main.app.workerMountDispatcher.data['RaJ2000']
                modelingData['DecJ2000'] = self.main.app.workerMountDispatcher.data['DecJ2000']
                modelingData['RaJNow'] = self.main.app.workerMountDispatcher.data['RaJNow']
                modelingData['DecJNow'] = self.main.app.workerMountDispatcher.data['DecJNow']
                modelingData['Pierside'] = self.main.app.workerMountDispatcher.data['Pierside']
                modelingData['RefractionTemperature'] = self.main.app.workerMountDispatcher.data['RefractionTemperature']
                modelingData['RefractionPressure'] = self.main.app.workerMountDispatcher.data['RefractionPressure']
                modelingData['Imagepath'] = ''
                self.main.app.messageQueue.put('\tCapturing image for model point {0:2d}\n'.format(modelingData['Index'] + 1))
                # getting next image
                self.main.app.workerImaging.imagingCommandQueue.put(modelingData)
                # wait for imaging ready
                while not self.imageIntegrated and not self.main.cancel:
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
                # next point after integrating but during downloading if possible or after IDLE
                self.main.workerSlewpoint.signalStartSlewing.emit()
                # we have to wait until image is downloaded before being able to plate solve
                while not self.imageSaved and not self.main.cancel:
                    time.sleep(0.1)
                    PyQt5.QtWidgets.QApplication.processEvents()
                self.main.app.messageQueue.put('Imaged>{0:02d}'.format(modelingData['Index'] + 1))
                self.main.workerPlatesolve.queuePlatesolve.put(copy.copy(modelingData))
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.main.app.workerImaging.cameraHandler.cancel = True
        self.queueImage.queue.clear()
        self.thread.quit()
        self.thread.wait()


class Platesolve(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    queuePlatesolve = Queue()

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexImageDataDownloaded = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.imageDataDownloaded = False
        self.main.app.workerAstrometry.imageDataDownloaded.connect(self.setImageDataDownloaded)

    def setImageDataDownloaded(self):
        self.mutexImageDataDownloaded.lock()
        self.imageDataDownloaded = True
        self.mutexImageDataDownloaded.unlock()

    def run(self):
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        while self.isRunning:
            if not self.queuePlatesolve.empty():
                self.mutexImageDataDownloaded.lock()
                self.imageDataDownloaded = False
                self.mutexImageDataDownloaded.unlock()
                modelingData = self.queuePlatesolve.get()
                if modelingData['Imagepath'] != '':
                    self.main.app.messageQueue.put('\tSolving image for model point {0}\n'.format(modelingData['Index'] + 1))
                    self.main.app.workerAstrometry.astrometryCommandQueue.put(modelingData)
                    # wait for solving ready
                    while not self.imageDataDownloaded and not self.main.cancel:
                        time.sleep(0.1)
                        PyQt5.QtWidgets.QApplication.processEvents()
                    if 'RaJ2000Solved' in modelingData:
                        ra_sol_Jnow, dec_sol_Jnow = self.main.transform.transformERFA(modelingData['RaJ2000Solved'], modelingData['DecJ2000Solved'], 3)
                        modelingData['RaJNowSolved'] = ra_sol_Jnow
                        modelingData['DecJNowSolved'] = dec_sol_Jnow
                        modelingData['RaError'] = (modelingData['RaJ2000Solved'] - modelingData['RaJ2000']) * 3600
                        modelingData['DecError'] = (modelingData['DecJ2000Solved'] - modelingData['DecJ2000']) * 3600
                        modelingData['ModelError'] = math.sqrt(modelingData['RaError'] * modelingData['RaError'] + modelingData['DecError'] * modelingData['DecError'])
                        modelingData['Message'] = 'OK - solved'
                        self.main.app.messageQueue.put('\tImage path: {0}\n'.format(modelingData['Imagepath']))
                        self.main.app.messageQueue.put('\tRA_diff:  {0:2.1f}    DEC_diff: {1:2.1f}\n'.format(modelingData['RaError'], modelingData['DecError']))
                        self.main.solvedPointsQueue.put(copy.copy(modelingData))
                    else:
                        if 'Message' in modelingData:
                            self.main.app.messageQueue.put('\tSolving error for point {0}: {1}\n'.format(modelingData['Index'] + 1, modelingData['Message'][:95]))
                        else:
                            self.main.app.messageQueue.put('\tSolving canceled')
                # write progress to hemisphere windows
                self.main.app.messageQueue.put('Solved>{0:02d}'.format(modelingData['Index'] + 1))
                # write progress estimation to main gui
                modelingDone = (modelingData['Index'] + 1) / modelingData['NumberPoints']
                timeDone = time.time() - self.main.timeStart
                if modelingDone != 0:
                    timeEstimation = (1 / modelingDone * timeDone) * (1 - modelingDone)
                else:
                    timeEstimation = 0
                self.main.app.messageQueue.put('percent{0:4.3f}'.format(modelingDone))
                self.main.app.messageQueue.put('timeleft{0}'.format(time.strftime('%M:%S', time.gmtime(timeEstimation))))
                # we come to an end
                if modelingData['NumberPoints'] == modelingData['Index'] + 1:
                    self.main.modelingHasFinished = True
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.queuePlatesolve.queue.clear()
        self.thread.quit()
        self.thread.wait()


class ModelingRunner:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make environment available to class
        self.app = app

        # assign support classes
        self.analyseData = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.modelPoints = modelingPoints.ModelPoints(self.app)

        # initialize the parallel thread modeling parts
        self.threadSlewpoint = PyQt5.QtCore.QThread()
        self.workerSlewpoint = Slewpoint(self, self.threadSlewpoint)
        self.workerSlewpoint.moveToThread(self.threadSlewpoint)
        self.threadSlewpoint.started.connect(self.workerSlewpoint.run)

        self.threadImage = PyQt5.QtCore.QThread()
        self.workerImage = Image(self, self.threadImage)
        self.workerImage.moveToThread(self.threadImage)
        self.threadImage.started.connect(self.workerImage.run)

        self.threadPlatesolve = PyQt5.QtCore.QThread()
        self.workerPlatesolve = Platesolve(self, self.threadPlatesolve)
        self.workerPlatesolve.moveToThread(self.threadPlatesolve)
        self.threadPlatesolve.started.connect(self.workerPlatesolve.run)

        # class variables
        self.solvedPointsQueue = Queue()
        self.timeStart = 0
        self.results = []
        self.modelingResultData = []
        self.modelAlignmentData = []
        self.modelRun = False
        self.modelingHasFinished = False
        self.numberPointsMax = 0
        self.numberSolvedPoints = 0
        self.cancel = False
        self.mountSlewFinished = False
        self.domeSlewFinished = False

        # signal slot
        self.app.workerMountDispatcher.signalSlewFinished.connect(self.setMountSlewFinished)
        self.app.workerDome.signalSlewFinished.connect(self.setDomeSlewFinished)

    def initConfig(self):
        self.modelPoints.initConfig()

    def storeConfig(self):
        self.modelPoints.storeConfig()

    def setMountSlewFinished(self):
        self.mountSlewFinished = True

    def setDomeSlewFinished(self):
        self.domeSlewFinished = True

    def clearAlignmentModel(self):
        # clearing the older results, because they are invalid afterwards
        self.modelingResultData = []
        # clearing the mount model and wait 4 seconds for the mount computer to recover (I don't know why, but Per Frejval did it)
        self.app.mountCommandQueue.put(':delalig#')
        time.sleep(4)

    def slewMountDome(self, modelingData):
        altitude = modelingData['Altitude']
        azimuth = modelingData['Azimuth']
        self.mountSlewFinished = False
        self.domeSlewFinished = False
        # limit azimuth and altitude
        if azimuth >= 360:
            azimuth = 359.9
        elif azimuth < 0.0:
            azimuth = 0.0
        # setting the coordinates for the mount
        self.app.mountCommandQueue.put(':Sz{0:03d}*{1:02d}#'.format(int(azimuth), int((azimuth - int(azimuth)) * 60 + 0.5)))
        self.app.mountCommandQueue.put(':Sa+{0:02d}*{1:02d}#'.format(int(altitude), int((altitude - int(altitude)) * 60 + 0.5)))
        self.app.mountCommandQueue.put(':MS#')
        if modelingData['Simulation']:
            self.app.mountCommandQueue.put(':U2#')
            commandSet = {'command': ':Gd#', 'reply': ''}
            self.app.mountCommandQueue.put(commandSet)
            while len(commandSet['reply']) == 0:
                time.sleep(0.1)
            dec = self.transform.degStringToDecimal(commandSet['reply'], ':')
            # print(commandSet['reply'], dec)
            commandSet = {'command': ':Gr#', 'reply': ''}
            self.app.mountCommandQueue.put(commandSet)
            while len(commandSet['reply']) == 0:
                time.sleep(0.1)
            ra = self.transform.degStringToDecimal(commandSet['reply'], ':')
            # print(commandSet['reply'], ra)
            if self.app.workerINDI.telescopeDevice != '':
                self.app.INDICommandQueue.put(
                    indiXML.newNumberVector([indiXML.oneNumber(ra, indi_attr={'name': 'RA'}),
                                             indiXML.oneNumber(dec, indi_attr={'name': 'DEC'})],
                                            indi_attr={'name': 'EQUATORIAL_EOD_COORD', 'device': self.app.workerINDI.telescopeDevice}))
        # if there is a dome connected, we have to start slewing it, too
        if modelingData['DomeIsConnected']:
            self.app.domeCommandQueue.put(('SlewAzimuth', azimuth))
            while not self.domeSlewFinished and not self.mountSlewFinished:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount and dome wait while for stop slewing')
                    break
                time.sleep(0.2)
                if modelingData['Simulation'] and self.app.workerINDI.telescopeDevice != '':
                    # wait for dome
                    while self.app.workerINDI.data['Device'][self.app.workerINDI.telescopeDevice]['EQUATORIAL_EOD_COORD']['state'] == 'Busy':
                        if self.cancel:
                            self.logger.info('Modeling cancelled in loop mount wait while for stop slewing')
                            break
                        time.sleep(0.2)
        else:
            while not self.mountSlewFinished:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount wait while for stop slewing')
                    break
                time.sleep(0.2)
            if modelingData['Simulation'] and self.app.workerINDI.telescopeDevice != '':
                # wait for dome
                while self.app.workerINDI.data['Device'][self.app.workerINDI.telescopeDevice]['EQUATORIAL_EOD_COORD']['state'] == 'Busy':
                    if self.cancel:
                        self.logger.info('Modeling cancelled in loop mount wait while for stop slewing')
                        break
                    time.sleep(0.2)

    def runModelCore(self, messageQueue, runPoints, modelingData):
        # start clearing hemisphere window
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()
        # start clearing the data
        results = []
        # preparing the gui outputs
        messageQueue.put('Imaged>{0:02d}'.format(0))
        messageQueue.put('Solved>{0:02d}'.format(0))
        messageQueue.put('Slewed>{0:02d}'.format(0))
        messageQueue.put('Processed>{0:02d}'.format(0))
        messageQueue.put('percent0')
        messageQueue.put('timeleft--:--')
        messageQueue.put('#BWStart Full Model\n')
        self.logger.info('modelingData: {0}'.format(modelingData))
        # start tracking
        self.app.mountCommandQueue.put(':PO#')
        self.app.mountCommandQueue.put(':AP#')
        self.modelRun = True
        self.timeStart = time.time()
        # starting the necessary threads
        self.threadSlewpoint.start()
        self.threadImage.start()
        self.threadPlatesolve.start()
        # wait until threads started
        while not self.workerImage.isRunning and not self.workerPlatesolve.isRunning and not self.workerSlewpoint.isRunning:
            time.sleep(0.2)
        # loading the point to the queue
        for i, (p_az, p_alt) in enumerate(runPoints):
            modelingData['Index'] = i
            modelingData['Azimuth'] = p_az
            modelingData['Altitude'] = p_alt
            modelingData['NumberPoints'] = len(runPoints)
            # has to be a copy, otherwise we have always the same content
            self.workerSlewpoint.queuePoint.put(copy.copy(modelingData))
        # start process
        self.modelingHasFinished = False
        self.timeStart = time.time()
        self.workerSlewpoint.signalStartSlewings.emit()
        while self.modelRun:
            # stop loop if modeling is cancelled from external
            if self.cancel:
                self.app.workerAstrometry.astrometryCancel.emit()
                self.app.workerImaging.imagingCancel.emit()
                break
            # stop loop if finished
            if self.modelingHasFinished:
                break
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.cancel:
            # clearing the gui
            messageQueue.put('percent0')
            messageQueue.put('timeleft--:--')
            self.logger.info('Modeling cancelled in main loop')
        self.workerSlewpoint.stop()
        self.workerImage.stop()
        self.workerPlatesolve.stop()
        self.modelRun = False
        while not self.solvedPointsQueue.empty():
            modelingData = self.solvedPointsQueue.get()
            # clean up intermediate data
            results.append(copy.copy(modelingData))
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if 'KeepImages' and 'BaseDirImages' in modelingData:
            if not modelingData['KeepImages']:
                shutil.rmtree(modelingData['BaseDirImages'], ignore_errors=True)
        messageQueue.put('#BWModel finished. Number of processed points: {0:3d}\n'.format(modelingData['NumberPoints']))
        # turn list of dicts to dict of lists
        if len(results) > 0:
            changedResults = dict(zip(results[0], zip(*[d.values() for d in results])))
        else:
            changedResults = {}
        return changedResults

    def runInitialModel(self):
        modelingData = {'Directory': time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())}
        # imaging has to be connected
        if 'CONNECTION' not in self.app.workerImaging.cameraHandler.data:
            return
        if self.app.workerImaging.cameraHandler.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # solver has to be connected
        if 'CONNECTION' not in self.app.workerAstrometry.astrometryHandler.data:
            return
        if self.app.workerAstrometry.astrometryHandler.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # telescope has to be connected
        if not self.app.workerMountDispatcher.mountStatus['Command']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Once']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Slow']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Medium']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Fast']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Align']:
            return
        # there have to be some modeling points
        if len(self.modelPoints.modelPoints) == 0:
            self.logger.warning('There are no modeling points to process')
            return
        # if dome is present, it has to be connected, too
        if not self.app.ui.pd_chooseDome.currentText().startswith('NONE'):
            domeIsConnected = self.app.workerDome.data['Connected']
        else:
            domeIsConnected = False
        modelingData['DomeIsConnected'] = domeIsConnected
        modelingData['SettlingTime'] = int(float(self.app.ui.settlingTime.value()))
        # simulation only works with indi
        if self.app.workerINDI.telescopeDevice != '':
            modelingData['Simulation'] = self.app.ui.checkSimulation.isChecked()
        else:
            modelingData['Simulation'] = False
        modelingData['KeepImages'] = self.app.ui.checkKeepImages.isChecked()
        self.app.workerImaging.cameraHandler.cancel = False
        self.app.workerAstrometry.astrometryHandler.cancel = False
        self.cancel = False
        self.modelAlignmentData = self.runModelCore(self.app.messageQueue, self.modelPoints.modelPoints, modelingData)
        name = modelingData['Directory'] + '_initial'
        if len(self.modelAlignmentData) > 0:
            self.app.workerMountDispatcher.programBatchData(self.modelAlignmentData)
            self.app.messageQueue.put('Reloading actual alignment model from mount\n')
            self.app.workerMountDispatcher.reloadAlignmentModel()
            self.app.messageQueue.put('Syncing actual alignment model and modeling data\n')
            self.app.workerMountDispatcher.retrofitMountData(self.modelAlignmentData)
            self.analyseData.saveData(self.modelAlignmentData, name)
            self.app.ui.le_analyseFileName.setText(name)
            if self.app.analyseWindow.showStatus:
                self.app.ui.btn_openAnalyseWindow.clicked.emit()
            self.app.signalAudio.emit('ModelingFinished')

    def runFullModel(self):
        modelingData = {'Directory': time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())}
        # imaging has to be connected
        if 'CONNECTION' not in self.app.workerImaging.cameraHandler.data:
            return
        if self.app.workerImaging.cameraHandler.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # solver has to be connected
        if 'CONNECTION' not in self.app.workerAstrometry.astrometryHandler.data:
            return
        if self.app.workerAstrometry.astrometryHandler.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # telescope has to be connected
        if not self.app.workerMountDispatcher.mountStatus['Command']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Once']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Slow']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Medium']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Fast']:
            return
        if not self.app.workerMountDispatcher.mountStatus['Align']:
            return
        # there have to be some modeling points
        if len(self.modelPoints.modelPoints) == 0:
            self.logger.warning('There are no modeling points to process')
            return
        # if dome is present, it has to be connected, too
        if not self.app.ui.pd_chooseDome.currentText().startswith('NONE'):
            domeIsConnected = self.app.workerDome.data['Connected']
        else:
            domeIsConnected = False
        modelingData['DomeIsConnected'] = domeIsConnected
        modelingData['SettlingTime'] = int(float(self.app.ui.settlingTime.value()))
        # simulation only works with indi
        if self.app.workerINDI.telescopeDevice != '':
            modelingData['Simulation'] = self.app.ui.checkSimulation.isChecked()
        else:
            modelingData['Simulation'] = False
        modelingData['KeepImages'] = self.app.ui.checkKeepImages.isChecked()
        self.app.workerImaging.cameraHandler.cancel = False
        self.app.workerAstrometry.astrometryHandler.cancel = False
        self.cancel = False
        self.modelAlignmentData = self.runModelCore(self.app.messageQueue, self.modelPoints.modelPoints, modelingData)
        name = modelingData['Directory'] + '_full'
        if len(self.modelAlignmentData) > 0:
            self.app.workerMountDispatcher.programBatchData(self.modelAlignmentData)
            self.app.messageQueue.put('Reloading actual alignment model from mount\n')
            self.app.workerMountDispatcher.reloadAlignmentModel()
            self.app.messageQueue.put('Syncing actual alignment model and modeling data\n')
            self.app.workerMountDispatcher.retrofitMountData(self.modelAlignmentData)
            self.analyseData.saveData(self.modelAlignmentData, name)
            self.app.ui.le_analyseFileName.setText(name)
            if self.app.analyseWindow.showStatus:
                self.app.ui.btn_openAnalyseWindow.clicked.emit()
            self.app.signalAudio.emit('ModelingFinished')

    def runCheckModel(self):
        if not self.checkModelingAvailable():
            return
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        points = self.modelPoints.BasePoints + self.modelPoints.RefinementPoints
        if len(points) > 0:
            simulation = self.app.ui.checkSimulation.isChecked()
            keepImages = self.app.ui.checkKeepImages.isChecked()
            domeIsConnected = self.app.workerAscomDome.isRunning
            self.modelingResultData = self.runModel(self.app.messageQueue, 'Check', points, modelData, settlingTime, simulation, keepImages, domeIsConnected)
            name = modelData['Directory'] + '_check.dat'
            if len(self.modelingResultData) > 0:
                self.app.ui.le_analyseFileName.setText(name)
                self.analyseData.saveData(self.modelingResultData, name)
        else:
            self.logger.warning('There are no Refinement or Base Points to modeling')

    def runTimeChangeModel(self):
        if not self.checkModelingAvailable():
            return
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        points = []
        for i in range(0, int(float(self.app.ui.numberRunsTimeChange.value()))):
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           PyQt5.QtWidgets.QGraphicsTextItem(''), True))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        domeIsConnected = self.app.workerAscomDome.isRunning
        modelData = self.imagingApps.prepareImaging()
        self.modelingResultData = self.runModel(self.app.messageQueue, 'TimeChange', points, modelData, settlingTime, simulation, keepImages, domeIsConnected)
        name = modelData['Directory'] + '_timechange.dat'
        if len(self.modelingResultData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.analyseData.saveData(self.modelingResultData, name)

    def runHystereseModel(self):
        if not self.checkModelingAvailable():
            return
        waitingTime = int(float(self.app.ui.settlingTime.value()))
        alt1 = int(float(self.app.ui.altitudeHysterese1.value()))
        alt2 = int(float(self.app.ui.altitudeHysterese2.value()))
        az1 = int(float(self.app.ui.azimuthHysterese1.value()))
        az2 = int(float(self.app.ui.azimuthHysterese2.value()))
        numberRunsHysterese = int(float(self.app.ui.numberRunsHysterese.value()))
        points = []
        for i in range(0, numberRunsHysterese):
            points.append((az1, alt1, PyQt5.QtWidgets.QGraphicsTextItem(''), True))
            points.append((az2, alt2, PyQt5.QtWidgets.QGraphicsTextItem(''), False))
        simulation = self.app.ui.checkSimulation.isChecked()
        keepImages = self.app.ui.checkKeepImages.isChecked()
        domeIsConnected = self.app.workerAscomDome.isRunning
        self.modelingResultData = self.runModel(self.app.messageQueue, 'Hysterese', points, modelData, waitingTime, simulation, keepImages, domeIsConnected)
        name = modelData['Directory'] + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.modelingResultData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.analyseData.saveData(self.modelingResultData, name)

    def runBatchModel(self):
        nameDataFile = self.app.ui.le_analyseFileName.text()
        self.logger.info('Modeling from {0}'.format(nameDataFile))
        data = self.analyseData.loadData(nameDataFile)
        if not('RaJNow' in data and 'DecJNow' in data):
            self.logger.warning('RaJNow or DecJNow not in data file')
            self.app.messageQueue.put('Mount coordinates missing\n')
            return
        if not('RaJNowSolved' in data and 'DecJNowSolved' in data):
            self.logger.warning('RaJNowSolved or DecJNowSolved not in data file')
            self.app.messageQueue.put('Solved data missing\n')
            return
        if not('Pierside' in data and 'LocalSiderealTimeFloat' in data):
            self.logger.warning('Pierside and LocalSiderealTimeFloat not in data file')
            self.app.messageQueue.put('Time and Pierside missing\n')
            return
        self.app.workerMountDispatcher.programBatchData(data)

    def plateSolveSync(self):
        self.app.messageQueue.put('#BWStart Sync Mount Model\n')

        # link to cam and check if available
        if 'CONNECTION' in self.app.workerImaging.data:
            if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
                return
        else:
            return
        # start prep imaging
        self.app.mountCommandQueue.put(':PO#')
        self.app.mountCommandQueue.put(':AP#')
        imageParams = dict()
        imageParams['Imagepath'] = ''
        imageParams['Exposure'] = self.app.ui.cameraExposure.value()
        imageParams['Directory'] = time.strftime('%Y-%m-%d', time.gmtime())
        imageParams['File'] = 'platesolvesync.fit'

        self.app.messageQueue.put('#BWExposing Image: {0} for {1} seconds\n'.format(imageParams['File'], imageParams['Exposure']))
        self.app.workerImaging.imagingCommandQueue.put(imageParams)

        while imageParams['Imagepath'] == '':
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()

        fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
        fitsHeader = fitsFileHandle[0].header
        imageParams['RaJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTRA'], ' ')
        imageParams['DecJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTDEC'], ' ')
        if 'PIXSCALE' in fitsHeader:
            imageParams['ScaleHint'] = float(fitsHeader['PIXSCALE'])
        else:
            if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                imageParams['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
            if 'FOCALLEN' in fitsHeader and 'PIXSIZE1' in fitsHeader:
                imageParams['ScaleHint'] = float(fitsHeader['PIXSIZE1']) * 206.6 / float(fitsHeader['FOCALLEN'])
        fitsFileHandle.close()

        self.app.messageQueue.put('#BWSolving Image: {0}\n'.format(imageParams['Imagepath']))
        self.app.workerAstrometry.astrometryCommandQueue.put(imageParams)

        # wait for solving
        while 'Solved' not in imageParams:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()

        if imageParams['Solved']:
            self.app.messageQueue.put('#BWSolving result: RA: {0}, DEC: {1}\n'.format(self.transform.decimalToDegree(imageParams['RaJ2000Solved'], False, False),
                                                                                      self.transform.decimalToDegree(imageParams['DecJ2000Solved'], True, False)))
            ra_sol_Jnow, dec_sol_Jnow = self.transform.transformERFA(imageParams['RaJ2000Solved'], imageParams['DecJ2000Solved'], 3)
            ra_form = self.transform.decimalToDegree(ra_sol_Jnow, False, False)
            dec_form = self.transform.decimalToDegree(dec_sol_Jnow, True, False)
            success = self.app.workerMountDispatcher.syncMountModel(ra_form, dec_form)
            if success:
                self.app.messageQueue.put('\tMount Model Synced\n')
            else:
                self.app.messageQueue.put('\tMount Model could not be synced - please check!\n')
        else:
            self.app.messageQueue.put('\tSolving error: {0}\n'.format(mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(imageParams['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('#BWSync Mount Model finished !\n')
