import unittest
import os

import skyfield.api

from mount_new.command import Command
from mount_new.configData import Firmware
from mount_new.configData import Setting
from mount_new.configData import Site


class TestMount(unittest.TestCase):

    def setUp(self):
        load = skyfield.api.Loader('~/PycharmProjects/Mountwizzard3/config',
                                   verbose=True,
                                   expire=True,
                                   )
        self.timeScale = load.timescale()
        self.firmware = Firmware()
        self.setting = Setting()
        self.site = Site(self.timeScale)

    def test_no_host(self):
        mount = Command(host='192.168.2.250', port=3492)
        commandSet = ':U2#:Gev#:'
        ok, mes, response = mount._transfer(commandSet)
        self.assertEqual(False, ok)
        self.assertIn('socket error', mes)
        self.assertEqual('', response)

    def test_speed(self):
        mount = Command(host='192.168.2.15', port=3492)
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        ok, mes, response = mount._transfer(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual('10micron GM1000HPS', response[5])

    def test_unknown_command(self):
        mount = Command(host='192.168.2.15', port=3492)
        commandSet = ':U2#:NotKnown#'
        ok, mes, response = mount._transfer(commandSet)
        self.assertEqual(False, ok)
        self.assertIn('socket error', mes)
        self.assertEqual('', response)

    def test_workaroundAlign(self):
        mount = Command(host='192.168.2.15', port=3492)
        ok, mes = mount.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollSlow(self):
        mount = Command(host='192.168.2.15',
                        port=3492,
                        firmware=self.firmware,
                        site=self.site,
                        )
        ok, mes = mount.pollSlow()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual(21514, mount.firmware.fw)
        self.assertEqual('2.15.14', mount.firmware.fwNumber)
        self.assertEqual('10micron GM1000HPS', mount.firmware.productName)
        self.assertEqual('Q-TYPE2012', mount.firmware.hwVersion)
        self.assertEqual('Mar 19 2018', mount.firmware.fwDate)
        self.assertEqual('15:56:53', mount.firmware.fwTime)

    def test_pollMed(self):
        mount = Command(host='192.168.2.15',
                        port=3492,
                        firmware=self.firmware,
                        site=self.site,
                        setting=self.setting,
                        )
        ok, mes = mount.pollMed(21514)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pollFast(self):
        mount = Command(host='192.168.2.15',
                        port=3492,
                        firmware=self.firmware,
                        site=self.site,
                        setting=self.setting,
                        )
        ok, mes = mount.pollFast()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    # testing the command analyses against structural faults
    def test_responses_typeA_analyseCommand(self):
        mount = Command()
        number, response = mount._analyseCommand(':AP#:AL#')
        self.assertEqual(True, response)
        self.assertEqual(0, number)

    def test_responses_typeAB_analyseCommand(self):
        mount = Command()
        number, response = mount._analyseCommand(':AP#:AL#:FLIP#')
        self.assertEqual(False, response)
        self.assertEqual(0, number)

    def test_responses_typeABC_analyseCommand(self):
        mount = Command()
        number, response = mount._analyseCommand(':AP#:AL#:FLIP#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)

    def test_responses_typeAC_analyseCommand(self):
        mount = Command()
        number, response = mount._analyseCommand(':AP#:AL#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)

    def test_responses_typeBC_analyseCommand(self):
        mount = Command()
        number, response = mount._analyseCommand(':FLIP#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)

    # testing parsing against valid and invalid data
    def test_parseWorkaroundAlign_good(self):
        mount = Command()
        suc, message = mount._parseWorkaroundAlign(['V', 'E'])
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseWorkaroundAlign_bad1(self):
        mount = Command()
        suc, message = mount._parseWorkaroundAlign(['E', 'V'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad2(self):
        mount = Command()
        suc, message = mount._parseWorkaroundAlign(['V'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad3(self):
        mount = Command()
        suc, message = mount._parseWorkaroundAlign(['E'])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseWorkaroundAlign_bad4(self):
        mount = Command()
        suc, message = mount._parseWorkaroundAlign([])
        self.assertEqual(False, suc)
        self.assertEqual('workaround command failed', message)

    def test_parseSlow_good(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']
        suc, message = mount._parseSlow(response)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad1(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53']
        suc, message = mount._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertEqual('wrong number of chunks from mount', message)

    def test_parseSlow_bad2(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = []
        suc, message = mount._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertEqual('wrong number of chunks from mount', message)

    def test_parseSlow_bad3(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+EEEEE', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = mount._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad4(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+0585.2', '-011:35:00.0', '+48:07:00.0', 'Mar 19 2018', '2.1514',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = mount._parseSlow(response)
        self.assertEqual(True, suc)
        self.assertEqual('ok', message)

    def test_parseSlow_bad5(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+0585.2', '-011:35:00.0', '+48:sdj.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = mount._parseSlow(response)
        self.assertEqual(False, suc)
        self.assertIn('could not convert string to float', str(message))

    def test_parseSlow_bad6(self):
        mount = Command(firmware=self.firmware,
                        site=self.site,
                        )
        response = ['+0585.2', '-011:EE:00.0', '+48:07:00.0', 'Mar 19 2018', '2.15.14',
                    '10micron GM1000HPS', '15:56:53', 'Q-TYPE2012']

        suc, message = mount._parseSlow(response)
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
