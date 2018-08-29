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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import unittest
import logging


import skyfield.api

from mount_new.configData import Data
from mount_new.configData import Firmware
from mount_new.configData import Setting
from mount_new.configData import ModelStar
from mount_new.configData import Model
from mount_new.configData import Site
from mount_new.configData import stringToDegree
from mount_new.configData import stringToDegreeDEC

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d][%(levelname)7s][%(filename)22s][%(lineno)5s][%(funcName)20s][%(threadName)10s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )


class TestConfigData(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger(__name__)
        pass

    def test_ModelStars_stringToDegree(self):
        parameter = '12:45:33.01'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, 12.759169444444444, 6)

    def test_ModelStars_stringToDegree_bad1(self):
        parameter = '12:45'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStars_stringToDegree_bad2(self):
        parameter = ''
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStars_stringToDegree_bad3(self):
        parameter = '12:45:33:01.01'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStars_stringToDegreeDEC_pos(self):
        parameter = '+56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_neg(self):
        parameter = '-56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, -56.5, 6)

    def test_ModelStars_stringToDegreeDEC_without(self):
        parameter = ' 56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_bad1(self):
        parameter = '++56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_bad2(self):
        parameter = '+56*30*00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStars_stringToDegreeDEC_bad3(self):
        parameter = '+56:30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStars_stringToDegreeDEC_bad4(self):
        parameter = ''
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_ModelStar_create(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        p3 = '1234.5'
        p4 = '90'
        modelStar = ModelStar(point=(p1, p2), errorRMS=p3, errorAngle=p4, number=1)
        self.assertAlmostEqual(modelStar.point.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(modelStar.point.ra.hms()[1], 45, 6)
        self.assertAlmostEqual(modelStar.point.ra.hms()[2], 33.01, 6)
        self.assertAlmostEqual(modelStar.point.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(modelStar.point.dec.dms()[1], 30, 6)
        self.assertAlmostEqual(modelStar.point.dec.dms()[2], 0.5, 6)

    def test_StarList_create(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        p3 = '1234.5'
        p4 = '90'
        modelStar1 = ModelStar(point=(p1, p2), errorRMS=p3, errorAngle=p4, number=1)
        modelStar2 = ModelStar(point=(p1, p2), errorRMS=p3, errorAngle=p4, number=2)
        modelStar3 = ModelStar(point=(p1, p2), errorRMS=p3, errorAngle=p4, number=3)
        modelStar4 = ModelStar(point=(p1, p2), errorRMS=p3, errorAngle=p4, number=4)

        model = Model()

        model.addStar(modelStar1)
        model.addStar(modelStar2)
        model.addStar(modelStar3)
        model.addStar(modelStar4)

        self.assertEqual(len(model.starList), 4)
        model.delStar(3)
        self.assertEqual(len(model.starList), 3)
        model.delStar(3)
        self.assertEqual(len(model.starList), 3)
        model.delStar(-1)
        self.assertEqual(len(model.starList), 3)
        model.delStar(1)
        self.assertEqual(len(model.starList), 2)

    def test_NameList_create(self):
        model = Model()

        model.addName('the first one')
        model.addName('the second one')
        model.addName('the third one')
        model.addName('the fourth one')

        self.assertEqual(len(model.nameList), 4)
        model.delName(3)
        self.assertEqual(len(model.nameList), 3)
        model.delName(3)
        self.assertEqual(len(model.nameList), 3)
        model.delName(-1)
        self.assertEqual(len(model.nameList), 3)
        model.delName(1)
        self.assertEqual(len(model.nameList), 2)

    def test_StarList_iteration(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        p3 = '1234.5'
        p4 = '90'

        model = Model()

        for i in range(0, 10):
            model.addStar(ModelStar(point=(p1, p2),
                                    errorRMS=i*i,
                                    errorAngle=i*i,
                                    number=i))

        self.assertEqual(len(model.starList), 10)

        for star in model.starList:
            print(star)

    def test_NameList_iteration(self):

        model = Model()

        for i in range(0, 10):
            model.addName('this is the {0}.th name'.format(i))

        self.assertEqual(len(model.nameList), 10)

        for name in model.nameList:
            print(name)


if __name__ == '__main__':
    unittest.main()
