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
import time


class MountModelHandling:
    logger = logging.getLogger(__name__)

    def __init__(self, app, data):
        self.app = app
        self.data = data

    def saveModel(self, target):
        print('Save: ', target)
        return
        self.app.mountCommandQueue.put(':modeldel0{0}#'.format(target))
        commandSet = {'command': ':modelsv0{0}#'.format(target), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'].endswith('1'):
            self.app.messageQueue.put('Mount Model {0} saved\n'.format(target))
            return True
        else:
            self.logger.warning('Mount Model {0} could not be saved. Error code: {1}'.format(target, commandSet['reply']))
            return False

    def loadModel(self, target):
        print('Load: ', target)
        return
        commandSet = {'command': ':modelld0{0}#'.format(target), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'].endswith('1'):
            self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
            while self.data['ModelLoading']:
                time.sleep(0.2)
            self.app.messageQueue.put('Mount Model {0} loaded\n'.format(target))
            return True
        else:
            self.app.messageQueue.put('#BRMount Model {0} could not be loaded\n'.format(target))
            self.logger.warning('Mount Model {0} could not be loaded. Error code: {1}'.format(target, commandSet['reply']))
            return False

    def deleteModel(self, target):
        print('Delete: ', target)
        return
        commandSet = {'command': ':modeldel0{0}#'.format(target), 'reply': ''}
        self.app.mountCommandQueue.put(commandSet)
        while len(commandSet['reply']) == 0:
            time.sleep(0.1)
        if commandSet['reply'].endswith('1'):
            self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
            while self.data['ModelLoading']:
                time.sleep(0.2)
            self.app.messageQueue.put('Mount Model {0} deleted\n'.format(target))
            return True
        else:
            self.app.messageQueue.put('#BRMount Model {0} could not be deleted\n'.format(target))
            self.logger.warning('Mount Model {0} could not be deleted. Error code: {1}'.format(target, commandSet['reply']))
            return False

    def clearAlign(self):
        self.app.mountCommandQueue.put(':delalig#')
        time.sleep(1)
        self.app.workerMountDispatcher.workerMountGetAlignmentModel.getAlignmentModel()
        while self.data['ModelLoading']:
            time.sleep(0.2)
        self.app.messageQueue.put('Mount Model cleared\n')
