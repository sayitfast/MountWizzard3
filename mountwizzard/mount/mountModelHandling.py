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
import time


class MountModelHandling:
    logger = logging.getLogger(__name__)

    def __init__(self, app, data):
        self.app = app
        self.data = data

    def saveModel(self, target):
        self.app.workerMountDispatcher.workerMountCommandRunner.sendCommand(':modeldel0{0}#'.format(target))
        reply = self.app.workerMountDispatcher.workerMountCommandRunner.sendCommand(':modelsv0{0}#'.format(target))
        if reply == '1':
            self.app.messageQueue.put('Mount Model {0} saved\n'.format(target))
            return True
        else:
            self.logger.warning('Mount Model {0} could not be saved'.format(target))
            return False

    def loadModel(self, target):
        reply = self.app.workerMountDispatcher.workerMountCommandRunner.sendCommand(':modelld0{0}#'.format(target))
        if reply == '1':
            self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
            while self.data['ModelLoading']:
                time.sleep(0.2)
            self.app.messageQueue.put('Mount Model {0} loaded\n'.format(target))
            return True
        else:
            self.app.messageQueue.put('#BRMount Model {0} could not be loaded\n'.format(target))
            self.logger.warning('Model {0} could not be loaded. Error code: {1}'.format(target, reply))
            return False
