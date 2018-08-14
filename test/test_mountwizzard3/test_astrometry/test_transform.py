import unittest

import os

import skyfield.api
import astrometry.transform

WorkDir = '~/PycharmProjects/MountWizzard3/config'

load = skyfield.api.Loader(WorkDir, expire=False)


class TestTransformations(unittest.TestCase):

    def setUp(self):
        global load
        ts = load.timescale()
        pass

    def test_JnowToJ2000(self):
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()