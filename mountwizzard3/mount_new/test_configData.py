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

    def test_ModelStar_create(self):
        p1 = '12:45:33:01'
        p2 = '+56*30:00.0'
        p3 = '1234.5'
        modelStar = ModelStar(point=(p1, p2), errorRMS=p3, number=1)

        print(modelStar.point.ra.hms(), modelStar.point.dec.dms())


if __name__ == '__main__':
    unittest.main()
