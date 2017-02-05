############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016
#
# Licence APL2.0
#
############################################################

import unittest
from mountwizzard.support.model_thread import Model


class TestModel(unittest.TestCase):

    def setUp(self):
        ui = None
        mount = None
        dome = None
        messageQueue = None
        commandQueue = None
        dataQueue = None
        logQueue = None
        self.model = Model(ui, mount, dome, messageQueue, commandQueue, dataQueue, logQueue)

    def test_prepareCaptureImageSubframes_cannotSubframe1(self):
        modelData = {}
        sizeX = 100
        sizeY = 100
        scale = 1
        modelData['sizeX'] = 0
        modelData['sizeY'] = 0
        modelData['offX'] = 0
        modelData['offY'] = 0
        modelData['canSubframe'] = False
        self.assertEquals(modelData, self.model.prepareCaptureImageSubframes(scale, sizeX, sizeY, False, {}))

    def test_prepareCaptureImageSubframes_cannotSubframe2(self):
        modelData = {}
        sizeX = 100
        sizeY = 100
        scale = 1
        modelData['sizeX'] = 0
        modelData['sizeY'] = 0
        modelData['offX'] = 0
        modelData['offY'] = 0
        modelData['canSubframe'] = False
        self.assertNotEquals(modelData, self.model.prepareCaptureImageSubframes(scale, sizeX, sizeY, True, {}))

    def test_prepareCaptureImageSubframes_canSubframe1(self):
        modelData = {}
        sizeX = 100
        sizeY = 100
        scale = 1
        modelData['sizeX'] = 0
        modelData['sizeY'] = 0
        modelData['offX'] = 0
        modelData['offY'] = 0
        modelData['canSubframe'] = True
        modelData['sizeX'] = int(sizeX * scale)
        modelData['sizeY'] = int(sizeY * scale)
        modelData['offX'] = int((sizeX - sizeX) / 2)
        modelData['offY'] = int((sizeY - sizeY) / 2)
        self.assertEquals(modelData, self.model.prepareCaptureImageSubframes(scale, sizeX, sizeY, True, {}))

    def test_prepareCaptureImageSubframes_canSubframe2(self):
        modelData = {}
        sizeX = 100
        sizeY = 100
        scale = 1
        modelData['sizeX'] = 0
        modelData['sizeY'] = 0
        modelData['offX'] = 0
        modelData['offY'] = 0
        modelData['canSubframe'] = True
        modelData['sizeX'] = int(sizeX * scale)
        modelData['sizeY'] = int(sizeY * scale)
        modelData['offX'] = int((sizeX - sizeX) / 2)
        modelData['offY'] = int((sizeY - sizeY) / 2)
        self.assertNotEquals(modelData, self.model.prepareCaptureImageSubframes(scale, sizeX, sizeY, False, {}))

if __name__ == '__main__':
    unittest.main()
