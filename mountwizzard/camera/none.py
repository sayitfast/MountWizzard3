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
import PyQt5
import logging


class NoneCamera(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)
    finished = PyQt5.QtCore.pyqtSignal()

    CYCLESTATUS = 5000

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
        self.data['AppAvailable'] = True
        self.data['AppName'] = 'None'
        self.data['AppInstallPath'] = 'None'

    def getStatus(self):
        self.cameraConnected = True
        self.solverConnected = True
        self.data['CameraStatus'] = 'IDLE'
        self.data['SolverStatus'] = 'IDLE'

        if self.cameraConnected:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(2)

        if self.solverConnected:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(2)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.getStatus)

    def getImage(self, modelData):
        return False, 'DISCONNECTED', modelData

    def getCameraProps(self):
        suc = True
        mes = 'OK'
        canSubframe = False
        gains = ''
        sizeX = 1
        sizeY = 1
        return suc, mes, sizeX, sizeY, canSubframe, gains

    def solveImage(self, modelData):
        return False, 'ERROR', modelData
