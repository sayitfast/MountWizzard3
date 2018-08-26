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

    def test_ModelStars_stringToDegreeHA(self):
        modelStar = ModelStar()
        parameter = '12:45:33.01'
        value = modelStar._stringToDegreeHA(parameter)
        self.assertAlmostEqual(value, 12.759169444444444)

    def test_ModelStars_stringToDegreeDEC_pos(self):
        modelStar = ModelStar()
        parameter = '+56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5)

    def test_ModelStars_stringToDegreeDEC_neg(self):
        modelStar = ModelStar()
        parameter = '-56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5)

    def test_ModelStars_stringToDegreeDEC_without(self):
        modelStar = ModelStar()
        parameter = ' 56*30:00.0'
        value = modelStar._stringToDegreeDEC(parameter)
        self.assertAlmostEqual(value, 56.5)


if __name__ == '__main__':
    unittest.main()
