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
# standard libraries
import unittest
# external packages
import skyfield.api
# local imports
from mount_new.mountData import AlignStar
from mount_new.mountData import AlignModel
from mount_new.mountData import Data
from mount_new.mountData import stringToDegree
from mount_new.mountData import stringToDegreeDEC
from mount_new.mountData import ProgSet
from test import configTest


class TestConfigData(unittest.TestCase):

    TS = configTest.TS
    CONNECTED = configTest.CONNECTED

    def setUp(self):
        pass

    #
    #
    # testing the conversion functions
    #
    #

    def test_stringToDegree(self):
        parameter = '12:45:33.01'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, 12.759169444444444, 6)

    def test_stringToDegree_bad1(self):
        parameter = '12:45'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_stringToDegree_bad2(self):
        parameter = ''
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_stringToDegree_bad3(self):
        parameter = '12:45:33:01.01'
        value = stringToDegree(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_stringToDegreeDEC_pos(self):
        parameter = '+56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_stringToDegreeDEC_neg(self):
        parameter = '-56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, -56.5, 6)

    def test_stringToDegreeDEC_without(self):
        parameter = ' 56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_stringToDegreeDEC_bad1(self):
        parameter = '++56*30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_stringToDegreeDEC_bad2(self):
        parameter = '+56*30*00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_stringToDegreeDEC_bad3(self):
        parameter = '+56:30:00.0'
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    def test_stringToDegreeDEC_bad4(self):
        parameter = ''
        value = stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, None, 6)

    #
    #
    # testing the timescale reference
    #
    #

    @unittest.skipIf(not TS, 'mount should be connected for this test')
    def test_data_without_ts(self):
        data = Data()
        self.assertEqual(isinstance(data.ts, skyfield.api.Timescale), True)

    def test_data_with_ts(self):
        pathToTS = '~/PycharmProjects/MountWizzard3/config'
        data = Data(pathToTS=pathToTS)
        self.assertEqual(isinstance(data.ts, skyfield.api.Timescale), True)

    #
    #
    # testing the class Model and it's attribute setters
    #
    #

    def test_add_del_Star(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        p3 = '1234.5'
        p4 = '90'
        modelStar1 = AlignStar(coord=(p1, p2), errorRMS=p3, errorAngle=p4, number=1)
        modelStar2 = AlignStar(coord=(p1, p2), errorRMS=p3, errorAngle=p4, number=2)
        modelStar3 = AlignStar(coord=(p1, p2), errorRMS=p3, errorAngle=p4, number=3)
        modelStar4 = AlignStar(coord=(p1, p2), errorRMS=p3, errorAngle=p4, number=4)

        model = AlignModel()

        self.assertEqual(len(model.starList), 0)
        model.addStar(modelStar1)
        self.assertEqual(len(model.starList), 1)
        model.addStar(modelStar2)
        self.assertEqual(len(model.starList), 2)
        model.addStar(modelStar3)
        self.assertEqual(len(model.starList), 3)
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

    def test_StarList_iteration(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        model = AlignModel()

        for i in range(0, 10):
            model.addStar(AlignStar(coord=(p1, p2),
                                    errorRMS=str(i*i),
                                    errorAngle=str(i*i),
                                    number=str(i)))

        self.assertEqual(len(model.starList), 10)
        for i, star in enumerate(model.starList):
            self.assertEqual(i,
                             star.number)
            self.assertEqual(i*i,
                             star.errorRMS)

    def test_add_del_Name(self):
        model = AlignModel()

        self.assertEqual(len(model.nameList), 0)
        model.addName('the first one')
        self.assertEqual(len(model.nameList), 1)
        model.addName('the second one')
        self.assertEqual(len(model.nameList), 2)
        model.addName('the third one')
        self.assertEqual(len(model.nameList), 3)
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

    def test_NameList_iteration(self):
        model = AlignModel()

        for i in range(0, 10):
            model.addName('this is the {0}.th name'.format(i))
        self.assertEqual(len(model.nameList), 10)
        for i, name in enumerate(model.nameList):
            self.assertEqual('this is the {0}.th name'.format(i),
                             name)

    #
    #
    # testing the specific QCI behaviour in Model class attributes
    #
    #

    def test_errorRMS_HPS(self):
        model = AlignModel()
        model.errorRMS = '36.8'
        self.assertAlmostEqual(model.errorRMS, 36.8)

    def test_errorRMS_HPS_empty(self):
        model = AlignModel()
        model.errorRMS = 'E'
        self.assertAlmostEqual(model.errorRMS, 0)

    def test_errorRMS_HPS_float(self):
        model = AlignModel()
        model.errorRMS = 36.8
        self.assertAlmostEqual(model.errorRMS, 36.8)

    def test_errorRMS_HPS_int(self):
        model = AlignModel()
        model.errorRMS = 36
        self.assertAlmostEqual(model.errorRMS, 36.0)

    def test_errorRMS_HPS_tuple(self):
        model = AlignModel()
        model.errorRMS = (36.8, 1.0)
        self.assertAlmostEqual(model.errorRMS, 0)

    def test_errorRMS_QCI(self):
        model = AlignModel()
        model.errorRMS = ''
        self.assertAlmostEqual(model.errorRMS, 0)

    #
    #
    # testing the class AlignStar and it's attribute setters
    #
    #

    def test_AlignStar_create1(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        p3 = '1234.5'
        p4 = '90'
        alignStar = AlignStar(coord=(p1, p2), errorRMS=p3, errorAngle=p4, number=1)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[1], 45, 6)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[2], 33.01, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[1], 30, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[2], 0.5, 6)

    def test_AlignStar_create2(self):
        star = skyfield.api.Star(ra_hours=12.55, dec_degrees=56.55)
        p3 = '1234.5'
        p4 = '90'
        alignStar = AlignStar(coord=star, errorRMS=p3, errorAngle=p4, number=1)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[1], 33, 6)
        self.assertAlmostEqual(alignStar.coord.ra.hms()[2], 0, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[1], 33, 6)
        self.assertAlmostEqual(alignStar.coord.dec.dms()[2], 0, 6)

    #
    #
    # testing the conversion functions
    #
    #

    def test_ProgSet_create1(self):
        p1 = '12:45:33.01'
        p2 = '+56*30:00.5'
        progSet = ProgSet(mCoord=(p1, p2),
                          pierside='W',
                          sCoord=(p1, p2),
                          sidereal=p1,
                          )
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[1], 45, 6)
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[2], 33.01, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[1], 30, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[2], 0.5, 6)

        self.assertAlmostEqual(progSet.sCoord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(progSet.sCoord.ra.hms()[1], 45, 6)
        self.assertAlmostEqual(progSet.sCoord.ra.hms()[2], 33.01, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[1], 30, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[2], 0.5, 6)

    def test_ProgSet_create2(self):
        p1 = '12:45:33.01'
        star = skyfield.api.Star(ra_hours=12.55, dec_degrees=56.55)
        progSet = ProgSet(mCoord=star,
                          pierside='W',
                          sCoord=star,
                          sidereal=p1,
                          )
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[1], 33, 6)
        self.assertAlmostEqual(progSet.mCoord.ra.hms()[2], 0, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[1], 33, 6)
        self.assertAlmostEqual(progSet.mCoord.dec.dms()[2], 0, 6)

        self.assertAlmostEqual(progSet.sCoord.ra.hms()[0], 12, 6)
        self.assertAlmostEqual(progSet.sCoord.ra.hms()[1], 33, 6)
        self.assertAlmostEqual(progSet.sCoord.ra.hms()[2], 0, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[0], 56, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[1], 33, 6)
        self.assertAlmostEqual(progSet.sCoord.dec.dms()[2], 0, 6)


if __name__ == '__main__':
    unittest.main()
