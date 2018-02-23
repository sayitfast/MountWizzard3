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
    cameraStatusText = PyQt5.QtCore.pyqtSignal(str)
    solverStatusText = PyQt5.QtCore.pyqtSignal(str)
    cameraExposureTime = PyQt5.QtCore.pyqtSignal(str)

    CYCLESTATUS = 5000
    CYCLE_MAIN_LOOP = 200

    def __init__(self, app, thread, commandQueue):
        super().__init__()
        self.app = app
        self.thread = thread
        self.commandQueue = commandQueue
        self.isRunning = False
        self.cancel = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.data = {'Camera': {}, 'Solver': {}}
        self.data['Camera']['Status'] = 'IDLE'
        self.data['Camera']['CanSubframe'] = False
        # self.data['Camera']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Solver']['Status'] = 'IDLE'
        # self.data['Solver']['CONNECTION'] = {'CONNECT': 'Off'}
        self.data['Camera']['AppAvailable'] = True
        self.data['Camera']['AppName'] = 'None'
        self.data['Camera']['AppInstallPath'] = 'None'
        self.data['Solver']['AppAvailable'] = True
        self.data['Solver']['AppName'] = 'None'
        self.data['Solver']['AppInstallPath'] = 'None'

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should have it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.setStatus()
        self.mainLoop()

    def mainLoop(self):
        if not self.isRunning:
            return
        if not self.commandQueue.empty():
            command = self.commandQueue.get()
            if command['Command'] == 'GetImage':
                command['ImageParams'] = self.getImage(command['ImageParams'])
            elif command['Command'] == 'SolveImage':
                command['ImageParams'] = self.solveImage(command['ImageParams'])
        self.mutexIsRunning.lock()
        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLE_MAIN_LOOP, self.mainLoop)
        self.mutexIsRunning.unlock()

    def stop(self):
        self.mutexIsRunning.lock()
        self.isRunning = False
        self.mutexIsRunning.unlock()
        self.thread.quit()
        self.thread.wait()

    def setStatus(self):
        self.data['Camera']['Status'] = 'IDLE'
        self.data['Solver']['Status'] = 'IDLE'

        if 'CONNECTION' in self.data['Camera']:
            if self.data['Camera']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusCamera.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusCamera.emit(2)
            self.cameraStatusText.emit(self.data['Camera']['Status'])
            self.cameraExposureTime.emit('---')
        else:
            self.app.workerModelingDispatcher.signalStatusCamera.emit(0)

        if 'CONNECTION' in self.data['Solver']:
            if self.data['Solver']['CONNECTION']['CONNECT'] == 'On':
                self.app.workerModelingDispatcher.signalStatusSolver.emit(3)
            else:
                self.app.workerModelingDispatcher.signalStatusSolver.emit(2)
            self.solverStatusText.emit(self.data['Solver']['Status'])
        else:
            self.app.workerModelingDispatcher.signalStatusSolver.emit(0)

        if self.isRunning:
            PyQt5.QtCore.QTimer.singleShot(self.CYCLESTATUS, self.setStatus)

    @staticmethod
    def getImage(imageParams):
        imageParams['Message'] = 'Not OK'
        imageParams['Imagepath'] = ''
        return imageParams

    @staticmethod
    def solveImage(imageParams):
        imageParams['Message'] = 'Not OK'
        return imageParams
