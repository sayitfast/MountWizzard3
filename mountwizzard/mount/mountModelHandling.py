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
        self.app.mountCommandQueue.put(':modeldel0{0}#'.format(target))
        self.app.mountCommandQueue.put(':modelsv0{0}#'.format(target))
        self.app.messageQueue.put('Mount Model {0} saved\n'.format(target))

    def loadModel(self, target):
        self.app.mountCommandQueue.put(':modelld0{0}#'.format(target))
        self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
        while self.data['ModelLoading']:
            time.sleep(0.2)
        self.app.messageQueue.put('Mount Model {0} loaded\n'.format(target))

    def clearAlign(self):
        self.app.mountCommandQueue.put(':delalig#')
        self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
        while self.data['ModelLoading']:
            time.sleep(0.2)
        self.app.messageQueue.put('Mount Model cleared\n')
