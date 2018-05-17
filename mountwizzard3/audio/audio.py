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
import PyQt5
import time
from baseclasses import checkIP


class Audio(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    signalDestruct = PyQt5.QtCore.pyqtSignal()
    CYCLE = 500

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexIPChanged = PyQt5.QtCore.QMutex()

        self.app = app
        self.thread = thread
        self.cycleTimer = None

        # define audio signals
        self.audioSignalsSet = dict()
        self.guiAudioList = dict()
        self.prepareGui()

    def initConfig(self):
        try:
            if 'PlayMountSlew' in self.app.config:
                self.app.ui.soundMountSlewFinished.setCurrentIndex(self.app.config['PlayMountSlew'])
            if 'PlayDomeSlew' in self.app.config:
                self.app.ui.soundDomeSlewFinished.setCurrentIndex(self.app.config['PlayDomeSlew'])
            if 'PlayMountAlert' in self.app.config:
                self.app.ui.soundMountAlert.setCurrentIndex(self.app.config['PlayMountAlert'])
            if 'PlayModelingFinished' in self.app.config:
                self.app.ui.soundModelingFinished.setCurrentIndex(self.app.config['PlayModelingFinished'])
        except Exception as e:
            self.logger.error('item in config.cfg for audio could not be initialized, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['PlayMountSlew'] = self.app.ui.soundMountSlewFinished.currentIndex()
        self.app.config['PlayDomeSlew'] = self.app.ui.soundDomeSlewFinished.currentIndex()
        self.app.config['PlayMountAlert'] = self.app.ui.soundMountAlert.currentIndex()
        self.app.config['PlayModelingFinished'] = self.app.ui.soundModelingFinished.currentIndex()

    def run(self):
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop
        self.logger.info('audio started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.setupAudioSignals()
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
        self.logger.info('audio stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.signalDestruct.disconnect(self.destruct)
        self.cycleTimer.stop()

    def doCommand(self):
        if not self.app.audioCommandQueue.empty():
            command = self.app.audioCommandQueue.get()
            self.playAudioSignal(command)

    def prepareGui(self):
        self.guiAudioList = dict()
        # adding the possible sounds to drop down menu
        self.guiAudioList['MountSlew'] = self.app.ui.soundMountSlewFinished
        self.guiAudioList['DomeSlew'] = self.app.ui.soundDomeSlewFinished
        self.guiAudioList['MountAlert'] = self.app.ui.soundMountAlert
        self.guiAudioList['ModelingFinished'] = self.app.ui.soundModelingFinished
        for itemKey, itemValue in self.guiAudioList.items():
            self.guiAudioList[itemKey].addItem('None')
            self.guiAudioList[itemKey].addItem('Beep')
            self.guiAudioList[itemKey].addItem('Horn')
            self.guiAudioList[itemKey].addItem('Beep1')
            self.guiAudioList[itemKey].addItem('Alarm')
            self.guiAudioList[itemKey].addItem('Alert')

    def setupAudioSignals(self):
        # define audio signals
        self.audioSignalsSet = dict()
        # load the sounds available
        self.audioSignalsSet['Beep'] = PyQt5.QtMultimedia.QSound(':/beep.wav')
        self.audioSignalsSet['Alert'] = PyQt5.QtMultimedia.QSound(':/alert.wav')
        self.audioSignalsSet['Horn'] = PyQt5.QtMultimedia.QSound(':/horn.wav')
        self.audioSignalsSet['Beep1'] = PyQt5.QtMultimedia.QSound(':/beep1.wav')
        self.audioSignalsSet['Alarm'] = PyQt5.QtMultimedia.QSound(':/alarm.wav')

    def playAudioSignal(self, value):
        if value in self.guiAudioList:
            sound = self.guiAudioList[value].currentText()
            if sound in self.audioSignalsSet:
                self.audioSignalsSet[sound].play()
