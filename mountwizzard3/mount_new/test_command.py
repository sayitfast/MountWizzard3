import unittest
import os

import skyfield.api

from mount_new.connection import Connection
from mount_new.configData import Data


class TestCommand(unittest.TestCase):

    def setUp(self):
        pathToTimescaleData = '~/PycharmProjects/Mountwizzard3/config'
        self.data = Data(pathToTimescaleData)

    def test_workaroundAlign(self):
        conn = Connection(host='192.168.2.15', port=3492)
        ok, mes = conn.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollSlow(self):
        conn = Connection(host='192.168.2.15',
                          port=3492,
                          data=self.data,
                          )
        ok, mes = conn.pollSlow()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual(21514, mount.firmware.fw)
        self.assertEqual('2.15.14', mount.firmware.fwNumber)
        self.assertEqual('10micron GM1000HPS', mount.firmware.productName)
        self.assertEqual('Q-TYPE2012', mount.firmware.hwVersion)
        self.assertEqual('Mar 19 2018', mount.firmware.fwDate)
        self.assertEqual('15:56:53', mount.firmware.fwTime)

    def test_pollMed(self):
        conn = Connection(host='192.168.2.15',
                          port=3492,
                          data=self.data,
                          )
        ok, mes = conn.pollMed(21514)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollFast(self):
        conn = Connection(host='192.168.2.15',
                          port=3492,
                          data=self.data,
                          )
        ok, mes = conn.pollFast()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    # testing parsing against valid and invalid data
    def test_parseWorkaroundAlign_good(self):
        conn = Connection()
        suc, message = conn._parseWorkaroundAlign(['V', 'E'])
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseWorkaroundAlign_bad1(self):
        conn = Connection()
        suc, message = conn._parseWorkaroundAlign(['E', 'V'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad2(self):
        conn = Connection()
        suc, message = conn._parseWorkaroundAlign(['V'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad3(self):
        conn = Connection()
        suc, message = conn._parseWorkaroundAlign(['E'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad4(self):
        conn = Connection()
        suc, message = conn._parseWorkaroundAlign([])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseSlow_good(self):
        conn = Connection(data=self.data,
                          )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']
        suc, message = conn._parseSlow(response)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad1(self):
        conn = Connection(data=self.data,
                          )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53']
        suc, message = conn._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertEqual('wrong number of chunks from conn', message)

    def test_parseSlow_bad2(self):
        conn = Connection(data=self.data,
                          )
        response = []
        suc, message = conn._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertEqual('wrong number of chunks from conn', message)

    def test_parseSlow_bad3(self):
        conn = Connection(data=self.data,
                          )
        response = ['+EEEEE', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = conn._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad4(self):
        conn = Connection(data=self.data,
                          )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.1514',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = conn._parseSlow(response)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad5(self):
        conn = Connection(data=self.data,
                          )
        response = ['+0585.2', '-011:35:00.0', '+48:sdj.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = conn._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad6(self):
        conn = Connection(data=self.data,
                          )
        response = ['+0585.2', '-011:EE:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = conn._parseSlow(response)
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
