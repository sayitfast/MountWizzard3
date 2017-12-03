############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
import logging


class MountModelHandling:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app

    def saveModel(self, target):
        self.app.mount.mountIpDirect.sendCommand(':modeldel0{0}#'.format(target))
        reply = self.app.mount.mountIpDirect.sendCommand(':modelsv0{0}#'.format(target))
        if reply == '1':
            self.app.messageQueue.put('Actual Mount Model saved to file {0}\n'.format(target))
            return True
        else:
            self.logger.warning('Model {0} could not be saved'.format(target))
            return False

    def loadModel(self, target):
        reply = self.app.mount.mountIpDirect.sendCommand(':modelld0{0}#'.format(target))
        if reply == '1':
            self.app.messageQueue.put('Mount Model loaded from file {0}\n'.format(target))
            self.app.mount.workerMountGetAlignmentModel.getAlignmentModel()
            return True
        else:
            self.app.messageQueue.put('#BRThere is no modeling named {0} or error while loading\n'.format(target))
            self.logger.warning('Model {0} could not be loaded'.format(target))
            return False

    def saveBackupModel(self):
        if self.saveModel('BACKUP'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'backup.dat')

    def loadBackupModel(self):
        if self.loadModel('BACKUP'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('backup.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for BACKUP\n')

    def saveBaseModel(self):
        if self.saveModel('BASE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'base.dat')
            else:
                self.app.messageQueue.put('#BRNo data for BASE\n')

    def loadBaseModel(self):
        if self.loadModel('BASE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('base.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for BASE\n')

    def saveRefinementModel(self):
        if self.saveModel('REFINE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'refine.dat')
            else:
                self.app.messageQueue.put('#BRNo data for REFINE\n')

    def loadRefinementModel(self):
        if self.loadModel('REFINE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('refine.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for REFINE\n')

    def saveActualModel(self):
        if self.saveModel('ACTUAL'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                if 'Index' in self.app.workerModelingDispatcher.modelingRunner.modelData[0].keys():
                    self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'actual.dat')
            else:
                self.app.messageQueue.put('#BRNo data for ACTUAL\n')

    def loadActualModel(self):
        if self.loadModel('ACTUAL'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('actual.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for ACTUAL\n')

    def saveSimpleModel(self):
        if self.saveModel('SIMPLE'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'simple.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for SIMPLE\n')

    def loadSimpleModel(self):
        if self.loadModel('SIMPLE'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('simple.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for SIMPLE\n')

    def saveDSO1Model(self):
        if self.saveModel('DSO1'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'DSO1.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for DSO1\n')

    def loadDSO1Model(self):
        if self.loadModel('DSO1'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('DSO1.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for DSO1\n')

    def saveDSO2Model(self):
        if self.saveModel('DSO2'):
            if self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.mount.analyse.saveData(self.app.workerModelingDispatcher.modelingRunner.modelData, 'DSO2.dat')
            else:
                self.app.messageQueue.put('#BRNo data file for DSO2\n')

    def loadDSO2Model(self):
        if self.loadModel('DSO2'):
            self.app.workerModelingDispatcher.modelingRunner.modelData = self.app.mount.analyse.loadDataRaw('dso2.dat')
            if not self.app.workerModelingDispatcher.modelingRunner.modelData:
                self.app.messageQueue.put('#BRNo data file for DSO2\n')

