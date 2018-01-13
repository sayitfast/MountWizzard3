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
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 5000

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}
        self.data['Camera']['Status'] = 'DISCONNECTED'
        self.data['Camera']['CanSubframe'] = False
        self.data['Camera']['CONNECTION'] = {'CONNECT': 'On'}
        # self.data['Camera']['']
        self.data['Solver']['Status'] = 'DISCONNECTED'
        self.data['Solver']['CONNECTION'] = {'CONNECT': 'On'}
        self.cameraConnected = False
        self.solverConnected = False
        self.data['AppAvailable'] = True
        self.data['AppName'] = 'None'
        self.data['AppInstallPath'] = 'None'

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.setStatus()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            # time.sleep(0.2)
            PyQt5.QtWidgets.QApplication.processEvents()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.finished.emit()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()

    def setStatus(self):
        self.cameraConnected = True
        self.solverConnected = True
        self.data['Camera']['Status'] = 'NONE'
        self.data['Solver']['Status'] = 'NONE'

        self.cameraStatus.emit(self.data['Camera']['Status'])
        self.cameraExposureTime.emit('---')

        if 'CONNECTION' in self.data['Camera']:
            if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(0)

        if 'CONNECTION' in self.data['Solver']:
            if self.data['Solver']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusSolver.emit(2)
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(0)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.setStatus)

    def getImage(self, imageParams):
        imageParams['Success'] = False
        imageParams['Message'] = 'Not OK'
        return imageParams

    def solveImage(self, imageParams):
        imageParams['Success'] = False
        imageParams['Message'] = 'Not OK'
        return imageParams
