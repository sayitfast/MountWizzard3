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

    def __init__(self, parent, messageQueue):
        self.parent = parent
        self.messageQueue = messageQueue

    def saveModel(self, target):
        num = self.parent.numberModelStars()
        if num == -1:
            self.messageQueue.put('#BWSave Model not available in simulation\n')
            return False
        self.parent.mountHandler.sendCommand('modeldel0' + target)
        reply = self.parent.mountHandler.sendCommand('modelsv0' + target)
        if reply == '1':
            self.messageQueue.put('Actual Mount Model saved to file {0}\n'.format(target))
            return True
        else:
            self.logger.warning('Model {0} could not be saved'.format(target))
            return False

    def loadModel(self, target):
        num = self.parent.numberModelStars()
        if num == -1:
            self.messageQueue.put('#BWLoad Model not available in simulation\n')
            return False
        reply = self.parent.mountHandler.sendCommand('modelld0' + target)
        if reply == '1':
            self.messageQueue.put('Mount Model loaded from file {0}\n'.format(target))
            return True
        else:
            self.messageQueue.put('#BRThere is no modeling named {0} or error while loading\n'.format(target))
            self.logger.warning('Model {0} could not be loaded'.format(target))
            return False

    def saveBackupModel(self):
        if self.saveModel('BACKUP'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'backup.dat')

    def loadBackupModel(self):
        if self.loadModel('BACKUP'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('backup.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for BACKUP\n')

    def saveBaseModel(self):
        if self.saveModel('BASE'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'base.dat')
            else:
                self.messageQueue.put('#BRNo data for BASE\n')

    def loadBaseModel(self):
        if self.loadModel('BASE'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('base.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for BASE\n')

    def saveRefinementModel(self):
        if self.saveModel('REFINE'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'refine.dat')
            else:
                self.messageQueue.put('#BRNo data for REFINE\n')

    def loadRefinementModel(self):
        if self.loadModel('REFINE'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('refine.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for REFINE\n')

    def saveActualModel(self):
        if self.saveModel('ACTUAL'):
            if self.parent.modelData:
                if 'Index' in self.parent.modelData[0].keys():
                    self.parent.analyse.saveData(self.parent.modelData, 'actual.dat')
            else:
                self.messageQueue.put('#BRNo data for ACTUAL\n')

    def loadActualModel(self):
        if self.loadModel('ACTUAL'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('actual.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for ACTUAL\n')

    def saveSimpleModel(self):
        if self.saveModel('SIMPLE'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'simple.dat')
            else:
                self.messageQueue.put('#BRNo data file for SIMPLE\n')

    def loadSimpleModel(self):
        if self.loadModel('SIMPLE'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('simple.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for SIMPLE\n')

    def saveDSO1Model(self):
        if self.saveModel('DSO1'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'DSO1.dat')
            else:
                self.messageQueue.put('#BRNo data file for DSO1\n')

    def loadDSO1Model(self):
        if self.loadModel('DSO1'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('DSO1.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for DSO1\n')

    def saveDSO2Model(self):
        if self.saveModel('DSO2'):
            if self.parent.modelData:
                self.parent.analyse.saveData(self.parent.modelData, 'DSO2.dat')
            else:
                self.messageQueue.put('#BRNo data file for DSO2\n')

    def loadDSO2Model(self):
        if self.loadModel('DSO2'):
            self.parent.modelData = self.parent.analyse.loadDataRaw('dso2.dat')
            if not self.parent.modelData:
                self.messageQueue.put('#BRNo data file for DSO2\n')

