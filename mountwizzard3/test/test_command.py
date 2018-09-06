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
from mount_new.command import Command
from mount_new.mountData import Data
from test import configTest


class TestCommand(unittest.TestCase):
    CONNECTED = configTest.CONNECTED
    SLEW = configTest.SLEW

    def setUp(self):
        pathToTimescaleData = '~/PycharmProjects/MountWizzard3/config'
        self.data = Data(pathToTimescaleData)

    #
    #
    # testing response parsers
    #
    #

    def test_parseWorkaround_good(self):
        comm = Command()
        suc = comm._parseWorkaround(['V', 'E'], 2)
        self.assertEqual(True, suc)

    def test_parseWorkaround_bad1(self):
        comm = Command()
        suc = comm._parseWorkaround(['E', 'V'], 2)
        self.assertEqual(False, suc)

    def test_parseWorkaround_bad2(self):
        comm = Command()
        suc = comm._parseWorkaround(['V'], 2)
        self.assertEqual(False, suc)

    def test_parseWorkaround_bad3(self):
        comm = Command()
        suc = comm._parseWorkaround(['E'], 2)
        self.assertEqual(False, suc)

    def test_parseWorkaround_bad4(self):
        comm = Command()
        suc = comm._parseWorkaround([], 2)
        self.assertEqual(False, suc)

    def test_parseSlow_good(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']
        suc = comm._parseSlow(response, 8)
        self.assertEqual(True, suc)

    def test_parseSlow_bad1(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53']
        suc = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)

    def test_parseSlow_bad2(self):
        comm = Command(data=self.data,
                       )
        response = []
        suc = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)

    def test_parseSlow_bad3(self):
        comm = Command(data=self.data,
                       )
        response = ['+master', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)

    def test_parseSlow_bad4(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.1514',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc = comm._parseSlow(response, 8)
        self.assertEqual(True, suc)

    def test_parseSlow_bad5(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:sdj.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc = comm._parseSlow(response, 8)
        self.assertEqual(True, suc)

    def test_parseSlow_bad6(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:EE:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)

    def test_parseMed_good(self):
        comm = Command(data=self.data,
                       )
        response = ['15', '0426', '05', '03', '+010.0', '0950.0', '60.2', '+033.0', '101+90*',
                    '+00*', '8', '34', 'E,2018-08-11']
        suc = comm._parseMed(response, 13)
        self.assertEqual(True, suc)

    def test_parseMed_bad1(self):
        comm = Command(data=self.data,
                       )
        response = ['15', '0426', '05', '03', '+010.0', '0EEE.0', '60.2', '+033.0', '101+90*',
                    '+00*', '8', '34', 'E,2018-08-11']

        with self. assertRaises(ValueError) as context:
            suc = comm._parseMed(response, 13)
            self.assertIn('could not convert string to float', context.exception)
            self.assertEqual(False, suc)

    def test_parseMed_bad2(self):
        comm = Command(data=self.data,
                       )
        response = ['15', '0426', '05', '03', '+010.0', '0950.0', '60.2', '+033.0', '+90*',
                    '+00*', '8', '34', 'E,2018-08-11']

        with self. assertRaises(ValueError) as context:
            suc = comm._parseMed(response, 13)
            self.assertIn('could not convert string to float', context.exception)
            self.assertEqual(False, suc)

    def test_parseMed_bad3(self):
        comm = Command(data=self.data,
                       )
        response = ['15', '0426', '05', '03', '+010.0', '0950.0', '60.2', '+033.0', '101+90*',
                    '+00', '8', '34', 'E,2018-08-11']

        suc = comm._parseMed(response, 13)
        self.assertEqual(True, suc)

    def test_parseMed_bad4(self):
        comm = Command(data=self.data,
                       )
        response = ['15', '0426', '05', '03', '+010.0', '0950.0', '60.2', '+033.0', '101+90*',
                    '+00*', '8', '34', ',2018-08-11']

        suc = comm._parseMed(response, 13)

        self.assertEqual(True, suc)

    def test_parseFast_good(self):
        comm = Command(data=self.data,
                       )
        response = ['13:15:35.68',
                    '19.44591,+88.0032,W,002.9803,+47.9945,2458352.10403639,5,0']
        suc = comm._parseFast(response, 2)
        self.assertEqual(True, suc)

    def test_parseNumberName_good(self):
        comm = Command(data=self.data,
                       )
        response = ['5']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(True, suc)

    def test_parseNumberName_bad1(self):
        comm = Command(data=self.data,
                       )
        response = ['df']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(True, suc)

    def test_parseNumberName_bad2(self):
        comm = Command(data=self.data,
                       )
        response = ['']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(True, suc)

    def test_parseNumberName_bad3(self):
        comm = Command(data=self.data,
                       )
        response = ['5a']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(True, suc)

    def test_parseNumberName_bad4(self):
        comm = Command(data=self.data,
                       )
        response = ['5', '4']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(False, suc)

    def test_parseNumberName_bad5(self):
        comm = Command(data=self.data,
                       )
        response = ['5', 'g']
        suc = comm._parseNumberNames(response, 1)
        self.assertEqual(False, suc)

    # testing stars fast
    def test_parseNumberStars_good(self):
        comm = Command(data=self.data,
                       )
        response = ['5']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(True, suc)

    def test_parseNumberStars_bad1(self):
        comm = Command(data=self.data,
                       )
        response = ['sd']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(True, suc)

    def test_parseNumberStars_bad2(self):
        comm = Command(data=self.data,
                       )
        response = ['']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(True, suc)

    def test_parseNumberStars_bad3(self):
        comm = Command(data=self.data,
                       )
        response = ['4t']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(True, suc)

    def test_parseNumberStars_bad4(self):
        comm = Command(data=self.data,
                       )
        response = ['4', '5']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(False, suc)

    def test_parseNumberStars_bad5(self):
        comm = Command(data=self.data,
                       )
        response = ['4', 'r']
        suc = comm._parseNumberStars(response, 1, False)
        self.assertEqual(False, suc)

    def test_parseNumberStars_getain(self):
        comm = Command(data=self.data,
                       )
        response = ['4', 'E']
        suc = comm._parseNumberStars(response, 1, True)
        self.assertEqual(False, suc)

    def test_parseModelStars_good(self):
        comm = Command(data=self.data,
                       )
        response = [
            '21:52:58.95,+08*56:10.1,   5.7,201',
            '21:06:10.79,+45*20:52.8,  12.1,329',
            '23:13:58.02,+38*48:18.8,  31.0,162',
            '17:43:41.26,+59*15:30.7,   8.4,005',
            '20:36:01.52,+62*39:32.4,  19.5,138',
            '03:43:11.04,+19*06:30.3,  22.6,199',
            '05:03:10.81,+38*14:22.2,  20.1,340',
            '04:12:55.39,+49*14:00.2,  17.1,119',
            '06:57:55.11,+61*40:26.8,   9.8,038',
            '22:32:24.00,+28*00:23.6,  42.1,347',
            '13:09:03.49,+66*24:40.5,  13.9,177',
        ]
        suc = comm._parseModelStars(response, 11)
        self.assertEqual(True, suc)
        self.assertEqual(len(comm.data.model.starList), 11)

    def test_parseModelStars_bad1(self):
        comm = Command(data=self.data,
                       )
        response = [
            '21:52:58.95,+08*56:10.1,   5.7,201',
            '21:06:10.79,+45*20:52.8,  12.1,329',
            '23:13:58.02,+38*48:18.8,  31.0,162',
            '06:57:55.11,+61*40:26.8,   9.8,038',
            '22:32:24.00,+28*00:23.6,  42.1,347',
            '13:09:03.49,+66*24:40.5,  13.9,177',
        ]
        suc = comm._parseModelStars(response, 4)
        self.assertEqual(False, suc)
        self.assertEqual(len(comm.data.model.starList), 0)


if __name__ == '__main__':
    unittest.main()
