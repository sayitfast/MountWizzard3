import unittest

import skyfield.api

from mount_new.configData import Data
from mount_new.configData import Firmware
from mount_new.configData import Setting
from mount_new.configData import ModelStar
from mount_new.configData import Model
from mount_new.configData import Site


class TestConfigData(unittest.TestCase):

    def setUp(self):
        pass

    def test_ModelStars_stringToHourHA(self):
        modelStar = ModelStar()
        parameter = '12:45:33.01'
        value = modelStar._stringToHourHA(parameter)
        self.assertAlmostEqual(value, 12.759169444444444, 6)

    def test_ModelStars_stringToHourHA_bad1(self):
        modelStar = ModelStar()
        parameter = '12:45'
        value = modelStar._stringToHourHA(parameter)
        self.assertAlmostEqual(value, 0, 6)

    def test_ModelStars_stringToHourHA_bad2(self):
        modelStar = ModelStar()
        parameter = ''
        value = modelStar._stringToHourHA(parameter)
        self.assertAlmostEqual(value, 0, 6)

    def test_ModelStars_stringToHourHA_bad3(self):
        modelStar = ModelStar()
        parameter = '12:45:33:01.01'
        value = modelStar._stringToHourHA(parameter)
        self.assertAlmostEqual(value, 0, 6)

    def test_ModelStars_stringToDegreeDEC_pos(self):
        modelStar = ModelStar()
        parameter = '+56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_neg(self):
        modelStar = ModelStar()
        parameter = '-56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, -56.5, 6)

    def test_ModelStars_stringToDegreeDEC_without(self):
        modelStar = ModelStar()
        parameter = ' 56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_bad1(self):
        modelStar = ModelStar()
        parameter = '++56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5, 6)

    def test_ModelStars_stringToDegreeDEC_bad2(self):
        modelStar = ModelStar()
        parameter = '+56*30*00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 0, 6)

    def test_ModelStars_stringToDegreeDEC_bad3(self):
        modelStar = ModelStar()
        parameter = '+56:30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 0, 6)

    def test_ModelStars_stringToDegreeDEC_bad4(self):
        modelStar = ModelStar()
        parameter = ''
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 0, 6)

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
