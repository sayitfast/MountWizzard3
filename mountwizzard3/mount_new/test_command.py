import unittest
import os

import skyfield.api

from mount_new.command import Command
from mount_new.configData import Data


class TestCommand(unittest.TestCase):

    def setUp(self):
        pathToTimescaleData = '~/PycharmProjects/Mountwizzard3/config'
        self.data = Data(pathToTimescaleData)

    def test_workaroundAlign(self):
        comm = Command(host='192.168.2.15', port=3492)
        ok, mes = comm.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollSlow(self):
        comm = Command(host='192.168.2.15',
                       port=3492,
                       data=self.data,
                       )
        ok, mes = comm.pollSlow()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual(21514, comm.data.fw.number)
        self.assertEqual('2.15.14', comm.data.fw.numberString)
        self.assertEqual('10micron GM1000HPS', comm.data.fw.productName)
        self.assertEqual('Q-TYPE2012', comm.data.fw.hwVersion)
        self.assertEqual('Mar 19 2018', comm.data.fw.fwdate)
        self.assertEqual('15:56:53', comm.data.fw.fwtime)

    def test_pollMed(self):
        comm = Command(host='192.168.2.15',
                       port=3492,
                       data=self.data,
                       )
        ok, mes = comm.pollMed()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollFast(self):
        comm = Command(host='192.168.2.15',
                       port=3492,
                       data=self.data,
                       )
        ok, mes = comm.pollFast()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    # testing parsing against valid and invalid data
    def test_parseWorkaroundAlign_good(self):
        comm = Command()
        suc, message = comm._parseWorkaroundAlign(['V', 'E'], 2)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseWorkaroundAlign_bad1(self):
        comm = Command()
        suc, message = comm._parseWorkaroundAlign(['E', 'V'], 2)
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad2(self):
        comm = Command()
        suc, message = comm._parseWorkaroundAlign(['V'], 2)
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad3(self):
        comm = Command()
        suc, message = comm._parseWorkaroundAlign(['E'], 2)
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad4(self):
        comm = Command()
        suc, message = comm._parseWorkaroundAlign([], 2)
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    # testing parsing Slow
    def test_parseSlow_good(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']
        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad1(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53']
        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)
        self.assertIn('wrong number of chunks', message)

    def test_parseSlow_bad2(self):
        comm = Command(data=self.data,
                       )
        response = []
        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)
        self.assertIn('wrong number of chunks', message)

    def test_parseSlow_bad3(self):
        comm = Command(data=self.data,
                       )
        response = ['+master', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad4(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.1514',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad5(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:35:00.0', '+48:sdj.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad6(self):
        comm = Command(data=self.data,
                       )
        response = ['+0585.2', '-011:EE:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = comm._parseSlow(response, 8)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

        """

        response = ['15', '0426', '05', '03', '+010.0', '0950.0', '60.2', '+033.0', '101+90*',
                    '+00*', '8', '34', 'E,2018-08-11']
        response = ['13:15:35.68',
                    '19.44591,+88.0032,W,002.9803,+47.9945,2458352.10403639,5,0']
    """


if __name__ == '__main__':
    unittest.main()
