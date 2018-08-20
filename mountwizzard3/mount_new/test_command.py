import time
import unittest
from mount_new import command


class TestMount(unittest.TestCase):

    def setUp(self):
        pass

    """
    def test_no_host(self):
        mount = command.MountCommand(host='192.168.2.250', port=3492)
        commandSet = ':U2#:Gev#:'
        ok, mes, response = mount.commandSend(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('socket timeout connect', mes)
        self.assertEqual(None, response)

    def test_no_server(self):
        mount = command.MountCommand(host='192.168.2.15', port=22)
        commandSet = ':U2#:Gev#:'
        ok, mes, response = mount.commandSend(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual('SSH-2.0-OpenSSH_5.4', response)

    def test_speed(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        timeStart = time.time()
        ok, mes, response = mount.commandSend(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual('10micron GM1000HPS', response.split('#')[5])
        timeEnd = time.time()
        print(timeEnd - timeStart)

    def test_unknown_command(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        commandSet = ':U2#:NotKnown#'
        ok, mes, response = mount.commandSend(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('socket timeout response', mes)
        self.assertEqual('', response)

    def test_workaroundAlign(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        ok, mes = mount.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_pull_slow(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        ok, mes = mount.pullSlow()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)

    def test_workaroundAlign(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        ok, mes = mount.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
    """
    def test_workaroundAlign(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        ok, mes = mount.workaroundAlign()
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)


if __name__ == '__main__':
    unittest.main()
