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
import time


class NoneCamera(PyQt5.QtCore.QObject):
    cameraStatus = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 5000

    def __init__(self, app, thread, commandQueue):
        super().__init__()
        self.app = app
        self.thread = thread
        self.commandQueue = commandQueue
        self.isRunning = False
        self._mutex = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}
        self.data['Camera']['Status'] = 'IDLE'
        self.data['Camera']['CanSubframe'] = False
        self.data['Camera']['CONNECTION'] = {'CONNECT': 'On'}
        self.data['Solver']['Status'] = 'IDLE'
        self.data['Solver']['CONNECTION'] = {'CONNECT': 'On'}
        self.data['Camera']['AppAvailable'] = True
        self.data['Camera']['AppName'] = 'None'
        self.data['Camera']['AppInstallPath'] = 'None'
        self.data['Solver']['AppAvailable'] = True
        self.data['Solver']['AppName'] = 'None'
        self.data['Solver']['AppInstallPath'] = 'None'

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        if not self.isRunning:
            self.isRunning = True
        self.setStatus()
        # main loop, if there is something to do, it should be inside. Important: all functions should be non blocking or calling processEvents()
        while self.isRunning:
            if not self.commandQueue.empty():
                command = self.commandQueue.get()
                if command['Command'] == 'GetImage':
                    command['ImageParams'] = self.getImage(command['ImageParams'])
                elif command['Command'] == 'SolveImage':
                    command['ImageParams'] = self.solveImage(command['ImageParams'])
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()

    def stop(self):
        self._mutex.lock()
        self.isRunning = False
        self._mutex.unlock()
        self.thread.quit()
        self.thread.wait()

    def setStatus(self):
        self.data['Camera']['Status'] = 'IDLE'
        self.data['Solver']['Status'] = 'IDLE'

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

    @staticmethod
    def getImage(imageParams):
        imageParams['Success'] = False
        imageParams['Message'] = 'Not OK'
        return imageParams

    @staticmethod
    def solveImage(imageParams):
        imageParams['Success'] = False
        imageParams['Message'] = 'Not OK'
        return imageParams
