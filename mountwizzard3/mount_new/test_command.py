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
                                   verbose=False,
                                   expire=False,
                                   )
        self.timeScale = load.timescale()
        self.firmware = Firmware()
        self.setting = Setting()
        self.site = Site(self.timeScale)

    """
    def test_no_host(self):
        mount = Command(host='192.168.2.250', port=3492)
        commandSet = ':U2#:Gev#:'
        ok, mes, response = mount.transfer(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('socket timeout connect', mes)
        self.assertEqual('', response)

    def test_speed(self):
        mount = Command(host='192.168.2.15', port=3492)
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        ok, mes, response = mount.transfer(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual('10micron GM1000HPS', response[5])

    def test_unknown_command(self):
        mount = Command(host='192.168.2.15', port=3492)
        commandSet = ':U2#:NotKnown#'
        ok, mes, response = mount.transfer(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('socket timeout response', mes)
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
   """
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


if __name__ == '__main__':
    unittest.main()
