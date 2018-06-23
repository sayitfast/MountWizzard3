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
import shutil
import datetime
import time
import math
import PyQt5
import indi.indi_xml as indiXML
from analyse import analysedata
from modeling import model_points
from queue import Queue
from astrometry import transform
import astropy.io.fits as pyfits


class Slewpoint(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    queuePoint = Queue()
    signalStartSlewing = PyQt5.QtCore.pyqtSignal()
    signalPointImaged = PyQt5.QtCore.pyqtSignal(float, float)

    CYCLE = 200
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexTakeNextPoint = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.takeNextPoint = False
        self.cycleTimer = None
        self.signalStartSlewing.connect(self.startSlewing)

    def startSlewing(self):
        self.mutexTakeNextPoint.lock()
        self.takeNextPoint = True
        self.mutexTakeNextPoint.unlock()

    def run(self):
        self.logger.info('model build slewpoint started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
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
        self.queuePoint.queue.clear()

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if self.takeNextPoint and not self.queuePoint.empty():
            self.mutexTakeNextPoint.lock()
            self.takeNextPoint = False
            self.mutexTakeNextPoint.unlock()
            modelingData = self.queuePoint.get()
            self.main.app.messageQueue.put('#BGSlewing to point {0:2d}  @ Az: {1:3.0f}\xb0 Alt: {2:2.0f}\xb0\n'.format(modelingData['Index'] + 1, modelingData['Azimuth'], modelingData['Altitude']))
            self.logger.info('Slewing to point {0:2d}  @ Az: {1:3.0f}\xb0 Alt: {2:2.0f}\xb0'.format(modelingData['Index'] + 1, modelingData['Azimuth'], modelingData['Altitude']))
            self.main.slewMountDome(modelingData)
            self.main.app.messageQueue.put('\tWait mount settling / delay time:  {0:02d} sec\n'.format(modelingData['SettlingTime']))
            self.main.app.messageQueue.put('Slewed>{0:02d}'.format(modelingData['Index'] + 1))
            time.sleep(modelingData['SettlingTime'])
            self.main.workerImage.queueImage.put(modelingData)
            # make signal for hemisphere that point is imaged
            self.signalPointImaged.emit(modelingData['Azimuth'], modelingData['Altitude'])


class Image(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    queueImage = Queue()
    signalImaging = PyQt5.QtCore.pyqtSignal()

    CYCLE = 200
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.isRunning = True
        self.imageIntegrated = False
        self.imageSaved = False
        self.cycleTimer = None
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
        self.logger.info('model build imaging started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
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
        # self.main.app.workerImaging.cameraHandler.cancel = True
        self.queueImage.queue.clear()

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.queueImage.empty():
            modelingData = self.queueImage.get()
            self.mutexImageSaved.lock()
            self.imageSaved = False
            self.mutexImageSaved.unlock()
            self.mutexImageIntegrated.lock()
            self.imageIntegrated = False
            self.mutexImageIntegrated.unlock()
            modelingData['File'] = 'Model_Image_' + '{0:03d}'.format(modelingData['Index']) + '.fit'
            modelingData['Imagepath'] = ''
            self.main.app.messageQueue.put('\tCapturing image for model point {0:2d}\n'.format(modelingData['Index'] + 1))
            self.logger.info('Capturing image for model point {0:2d}'.format(modelingData['Index'] + 1))
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
            self.logger.info('Imaged {0:02d}'.format(modelingData['Index'] + 1))
            self.main.workerPlatesolve.queuePlatesolve.put(copy.copy(modelingData))


class Platesolve(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    queuePlatesolve = Queue()

    CYCLE = 200
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, main, thread):
        super().__init__()
        self.main = main
        self.thread = thread
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexImageDataDownloaded = PyQt5.QtCore.QMutex()
        self.isRunning = True
        self.cycleTimer = None
        self.imageDataDownloaded = False
        self.main.app.workerAstrometry.imageDataDownloaded.connect(self.setImageDataDownloaded)

    def setImageDataDownloaded(self):
        self.mutexImageDataDownloaded.lock()
        self.imageDataDownloaded = True
        self.mutexImageDataDownloaded.unlock()

    def run(self):
        self.logger.info('model build solving started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
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
        self.queuePlatesolve.queue.clear()

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.queuePlatesolve.empty():
            self.mutexImageDataDownloaded.lock()
            self.imageDataDownloaded = False
            self.mutexImageDataDownloaded.unlock()
            modelingData = self.queuePlatesolve.get()
            if modelingData['Imagepath'] != '':
                self.main.app.messageQueue.put('\tSolving image for model point {0}\n'.format(modelingData['Index'] + 1))
                self.logger.info('Solving image for model point {0}'.format(modelingData['Index'] + 1))
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
                    self.logger.info('RA_diff:  {0:2.1f}    DEC_diff: {1:2.1f}, image path: {2}'.format(modelingData['RaError'], modelingData['DecError'], modelingData['Imagepath']))
                    self.main.solvedPointsQueue.put(copy.copy(modelingData))
                else:
                    if 'Message' in modelingData:
                        self.main.app.messageQueue.put('\tSolving error for point {0}: {1}\n'.format(modelingData['Index'] + 1, modelingData['Message']))
                        self.logger.warning('Solving error for point {0}: {1}'.format(modelingData['Index'] + 1, modelingData['Message']))
                    else:
                        self.main.app.messageQueue.put('\tSolving canceled\n')
                        self.logger.warning('Solving canceled')
            # write progress to hemisphere windows
            self.main.app.messageQueue.put('Solved>{0:02d}'.format(modelingData['Index'] + 1))
            # write progress estimation to main gui
            modelingDone = (modelingData['Index'] + 1) / modelingData['NumberPoints']
            timeElapsed = time.time() - self.main.timeStart
            if modelingDone != 0:
                timeEstimation = (1 / modelingDone * timeElapsed) * (1 - modelingDone)
            else:
                timeEstimation = 0
            self.main.app.messageQueue.put('percent{0:4.3f}'.format(modelingDone))
            self.main.app.messageQueue.put('timeEst{0}'.format(time.strftime('%M:%S', time.gmtime(timeEstimation))))
            finished = datetime.timedelta(seconds=timeEstimation) + datetime.datetime.now()
            self.main.app.messageQueue.put('timeFin{0}'.format(finished.strftime('%H:%M:%S')))
            # we come to an end
            if modelingData['NumberPoints'] == modelingData['Index'] + 1:
                self.main.modelingHasFinished = True


class ModelingBuild:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        # make environment available to class
        self.app = app

        # assign support classes
        self.analyseData = analysedata.Analyse(self.app)
        self.transform = transform.Transform(self.app)
        self.modelPoints = model_points.ModelPoints(self.app)

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
        self.imageReady = False
        self.solveReady = False
        self.mountSlewFinished = False
        self.domeSlewFinished = False

        # signal slot
        self.app.workerMountDispatcher.signalSlewFinished.connect(self.setMountSlewFinished)
        self.app.workerDome.signalSlewFinished.connect(self.setDomeSlewFinished)
        self.app.workerImaging.imageSaved.connect(self.setImageReady)
        self.app.workerAstrometry.imageDataDownloaded.connect(self.setSolveReady)

    def initConfig(self):
        self.modelPoints.initConfig()

    def storeConfig(self):
        self.modelPoints.storeConfig()

    def setCancel(self):
        self.cancel = True

    def setImageReady(self):
        self.imageReady = True

    def setSolveReady(self):
        self.solveReady = True

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
        # if there is a dome connected, we have to start slewing it, too
        if modelingData['DomeIsConnected']:
            self.app.domeCommandQueue.put(('SlewAzimuth', azimuth))
            while not self.domeSlewFinished and not self.mountSlewFinished:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount and dome wait while for stop slewing')
                    break
                time.sleep(0.2)
        else:
            while not self.mountSlewFinished:
                if self.cancel:
                    self.logger.info('Modeling cancelled in loop mount wait while for stop slewing')
                    break
                time.sleep(0.2)

    def runModelCore(self, messageQueue, runPoints, modelingData):
        self.app.imageWindow.signalSetManualEnable.emit(False)
        # start clearing the data
        results = []
        # preparing the gui outputs
        messageQueue.put('Imaged>{0:02d}'.format(0))
        messageQueue.put('Solved>{0:02d}'.format(0))
        messageQueue.put('Slewed>{0:02d}'.format(0))
        messageQueue.put('percent0')
        messageQueue.put('timeEla--:--')
        messageQueue.put('timeEst--:--')
        messageQueue.put('timeFin--:--:--')
        self.logger.info('modelingData: {0}'.format(modelingData))
        # start tracking
        self.app.mountCommandQueue.put(':PO#')
        self.app.mountCommandQueue.put(':AP#')
        self.workerSlewpoint.mutexTakeNextPoint.lock()
        self.workerSlewpoint.takeNextPoint = False
        self.workerSlewpoint.mutexTakeNextPoint.unlock()
        self.modelRun = True
        self.timeStart = time.time()
        # starting the necessary threads
        self.threadSlewpoint.start()
        self.threadImage.start()
        self.threadPlatesolve.start()
        # wait until threads started
        while not self.workerImage.isRunning and not self.workerPlatesolve.isRunning and not self.workerSlewpoint.isRunning:
            time.sleep(0.2)
        if len(runPoints) > 100:
            messageQueue.put('#BYMore than 100 points defined, using only first 100 points for model build\n')
            messageQueue.put('ToModel>{0:02d}'.format(100))
        # loading the points to the queue, but only the first 100, because mount computer does only allow 100 points
        for i, (p_az, p_alt) in enumerate(runPoints[:100]):
            modelingData['Index'] = i
            modelingData['Azimuth'] = p_az
            modelingData['Altitude'] = p_alt
            modelingData['NumberPoints'] = len(runPoints)
            # has to be a copy, otherwise we have always the same content
            self.workerSlewpoint.queuePoint.put(copy.copy(modelingData))
        # start process
        self.modelingHasFinished = False
        self.timeStart = time.time()
        self.workerSlewpoint.signalStartSlewing.emit()
        while self.modelRun:
            # stop loop if modeling is cancelled from external
            if self.cancel:
                self.app.workerAstrometry.astrometryCancel.emit()
                self.app.workerImaging.imagingCancel.emit()
                break
            # stop loop if finished
            if self.modelingHasFinished:
                break
            timeElapsed = time.time() - self.timeStart
            messageQueue.put('timeEla{0}'.format(time.strftime('%M:%S', time.gmtime(timeElapsed))))
            time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        if self.cancel:
            # clearing the gui
            messageQueue.put('percent0')
            messageQueue.put('timeEst--:--')
            self.logger.info('Modeling cancelled in main loop')
        self.workerSlewpoint.stop()
        self.workerImage.stop()
        self.workerPlatesolve.stop()
        self.modelRun = False
        while not self.solvedPointsQueue.empty():
            modelingData = self.solvedPointsQueue.get()
            # clean up intermediate data
            results.append(copy.copy(modelingData))
        if 'KeepImages' and 'BaseDirImages' in modelingData:
            if not modelingData['KeepImages']:
                shutil.rmtree(modelingData['BaseDirImages'], ignore_errors=True)
        # turn list of dicts to dict of lists
        if len(results) > 0:
            changedResults = dict(zip(results[0], zip(*[d.values() for d in results])))
        else:
            changedResults = {}
        self.app.imageWindow.signalSetManualEnable.emit(True)
        return changedResults

    def runInitialModel(self):
        modelingData = {'Directory': time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())}
        # imaging has to be connected
        if 'CONNECTION' not in self.app.workerImaging.cameraHandler.data:
            return
        if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # solver has to be connected
        if 'CONNECTION' not in self.app.workerAstrometry.astrometryHandler.data:
            return
        if self.app.workerAstrometry.data['CONNECTION']['CONNECT'] == 'Off':
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
        if not self.app.workerMountDispatcher.mountStatus['GetAlign']:
            return
        if not self.app.workerMountDispatcher.mountStatus['SetAlign']:
            return
        # there have to be some modeling points
        if len(self.modelPoints.modelPoints) == 0:
            self.logger.warning('There are no modeling points to process')
            return
        # if dome is present, it has to be connected, too
        if not self.app.ui.pd_chooseDome.currentText().startswith('No Dome'):
            domeIsConnected = self.app.workerDome.data['Connected']
        else:
            domeIsConnected = False
        modelingData['DomeIsConnected'] = domeIsConnected
        modelingData['SettlingTime'] = int(self.app.ui.settlingTime.value())
        modelingData['KeepImages'] = self.app.ui.checkKeepImages.isChecked()
        self.app.workerImaging.cameraHandler.cancel = False
        self.app.workerAstrometry.astrometryHandler.cancel = False
        self.cancel = False
        timeStartModeling = time.time()
        self.app.messageQueue.put('#BWStart Initial Model\n')
        self.app.workerMountDispatcher.mountModelHandling.saveModel('BACKUP')
        self.modelAlignmentData = self.runModelCore(self.app.messageQueue, self.modelPoints.modelPoints, modelingData)
        self.app.messageQueue.put('#BWModel processed\n')
        name = modelingData['Directory'] + '_initial'
        if len(self.modelAlignmentData) > 0:
            self.app.messageQueue.put('Programming model to mount\n')
            self.app.workerMountDispatcher.programBatchData(self.modelAlignmentData)
            self.app.messageQueue.put('Reloading actual alignment model from mount\n')
            self.app.workerMountDispatcher.reloadAlignmentModel()
            self.app.messageQueue.put('Syncing actual alignment model and modeling data\n')
            if self.app.workerMountDispatcher.retrofitMountData(self.modelAlignmentData):
                self.analyseData.saveData(self.modelAlignmentData, name)
                self.app.signalSetAnalyseFilename.emit(name)
                if self.app.analyseWindow.showStatus:
                    self.app.ui.btn_openAnalyseWindow.clicked.emit()
                self.app.audioCommandQueue.put('ModelingFinished')
                self.app.workerMountDispatcher.mountModelHandling.saveModel('INITIAL')
                self.app.messageQueue.put('#BGInitial Model finished with success, runtime: {0} (MM:SS)\n'.format(time.strftime("%M:%S", time.gmtime(time.time() - timeStartModeling))))
                self.logger.info('Initial Model finished with success, runtime: {0} (MM:SS)'.format(time.strftime("%M:%S", time.gmtime(time.time() - timeStartModeling))))
            else:
                self.app.messageQueue.put('#BRModel finished with errors\n')
                self.logger.warning('Model finished with errors')
        else:
            self.app.messageQueue.put('#BRModel finished with errors\n')
            self.logger.warning('Model finished with errors')

    def runFullModel(self):
        modelingData = {'Directory': time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())}
        # imaging has to be connected
        if 'CONNECTION' not in self.app.workerImaging.data:
            return
        if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
            return
        # solver has to be connected
        if 'CONNECTION' not in self.app.workerAstrometry.data:
            return
        if self.app.workerAstrometry.data['CONNECTION']['CONNECT'] == 'Off':
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
        if not self.app.workerMountDispatcher.mountStatus['GetAlign']:
            return
        if not self.app.workerMountDispatcher.mountStatus['SetAlign']:
            return
        # there have to be some modeling points
        if len(self.modelPoints.modelPoints) == 0:
            self.logger.warning('There are no modeling points to process')
            return
        # if dome is present, it has to be connected, too
        if not self.app.ui.pd_chooseDome.currentText().startswith('No Dome'):
            domeIsConnected = self.app.workerDome.data['Connected']
        else:
            domeIsConnected = False
        modelingData['DomeIsConnected'] = domeIsConnected
        modelingData['SettlingTime'] = int(self.app.ui.settlingTime.value())
        modelingData['KeepImages'] = self.app.ui.checkKeepImages.isChecked()
        self.app.workerImaging.cameraHandler.cancel = False
        self.app.workerAstrometry.astrometryHandler.cancel = False
        self.cancel = False
        timeStartModeling = time.time()
        self.app.messageQueue.put('#BWStart Full Model\n')
        self.app.workerMountDispatcher.mountModelHandling.saveModel('BACKUP')
        self.modelAlignmentData = self.runModelCore(self.app.messageQueue, self.modelPoints.modelPoints, modelingData)
        self.app.messageQueue.put('#BWModel processed\n')
        name = modelingData['Directory'] + '_full'
        if len(self.modelAlignmentData) > 0:
            self.app.messageQueue.put('Programming model to mount\n')
            self.app.workerMountDispatcher.programBatchData(self.modelAlignmentData)
            self.app.messageQueue.put('Reloading actual alignment model from mount\n')
            self.app.workerMountDispatcher.reloadAlignmentModel()
            self.app.messageQueue.put('Syncing actual alignment model and modeling data\n')
            if self.app.workerMountDispatcher.retrofitMountData(self.modelAlignmentData):
                self.analyseData.saveData(self.modelAlignmentData, name)
                self.app.signalSetAnalyseFilename.emit(name)
                if self.app.analyseWindow.showStatus:
                    self.app.ui.btn_openAnalyseWindow.clicked.emit()
                self.app.audioCommandQueue.put('ModelingFinished')
                self.app.workerMountDispatcher.mountModelHandling.saveModel('FULL')
                self.app.messageQueue.put('#BGFull Model finished with success, runtime: {0} (MM:SS)\n'.format(time.strftime('%M:%S', time.gmtime(time.time() - timeStartModeling))))
                self.logger.info('Full Model finished with success, runtime: {0} (MM:SS)'.format(time.strftime('%M:%S', time.gmtime(time.time() - timeStartModeling))))
            else:
                self.app.messageQueue.put('#BRModel finished with errors\n')
                self.logger.warning('Model finished with errors')
        else:
            self.app.messageQueue.put('#BRModel finished with errors\n')
            self.logger.warning('Model finished with errors')

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
        self.imageReady = False
        self.app.workerImaging.imagingCommandQueue.put(imageParams)
        while not self.imageReady and not self.cancel:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        self.app.messageQueue.put('#BWSolving Image: {0}\n'.format(imageParams['Imagepath']))
        # wait for solving
        self.solveReady = False
        self.app.workerAstrometry.astrometryCommandQueue.put(imageParams)
        while not self.solveReady and not self.cancel:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if 'Solved' in imageParams:
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
                self.logger.warning('Solve key in imageParams missing')
        else:
            self.app.messageQueue.put('\tSolving error: {0}\n'.format(mes))
        if not self.app.ui.checkKeepImages.isChecked():
            shutil.rmtree(imageParams['BaseDirImages'], ignore_errors=True)
        self.app.messageQueue.put('#BWSync Mount Model finished !\n')

    def runCheckModel(self):
        if not self.checkModelingAvailable():
            return
        settlingTime = int(self.app.ui.settlingTime.value())
        points = self.modelPoints.BasePoints + self.modelPoints.RefinementPoints
        if len(points) > 0:
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
        settlingTime = int(self.app.ui.settlingTime.value())
        points = []
        for i in range(0, int(self.app.ui.numberRunsTimeChange.value())):
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           PyQt5.QtWidgets.QGraphicsTextItem(''), True))
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
        waitingTime = int(self.app.ui.settlingTime.value())
        alt1 = int(self.app.ui.altitudeHysterese1.value())
        alt2 = int(self.app.ui.altitudeHysterese2.value())
        az1 = int(self.app.ui.azimuthHysterese1.value())
        az2 = int(self.app.ui.azimuthHysterese2.value())
        numberRunsHysterese = int(self.app.ui.numberRunsHysterese.value())
        points = []
        for i in range(0, numberRunsHysterese):
            points.append((az1, alt1, PyQt5.QtWidgets.QGraphicsTextItem(''), True))
            points.append((az2, alt2, PyQt5.QtWidgets.QGraphicsTextItem(''), False))
        keepImages = self.app.ui.checkKeepImages.isChecked()
        domeIsConnected = self.app.workerAscomDome.isRunning
        self.modelingResultData = self.runModel(self.app.messageQueue, 'Hysterese', points, modelData, waitingTime, simulation, keepImages, domeIsConnected)
        name = modelData['Directory'] + '_hysterese.dat'
        self.app.ui.le_analyseFileName.setText(name)
        if len(self.modelingResultData) > 0:
            self.app.ui.le_analyseFileName.setText(name)
            self.analyseData.saveData(self.modelingResultData, name)
