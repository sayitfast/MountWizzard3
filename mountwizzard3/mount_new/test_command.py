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
    """

    def test_speed(self):
        mount = command.MountCommand(host='192.168.2.15', port=3492)
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#:newalig#:endalig#'
        timeStart = time.time()
        ok, mes, response = mount.commandSend(commandSet)
        print('Success:', ok, '   Message:', mes, '   Response values:', response)
        # self.assertEqual(True, ok)
        # self.assertEqual('ok', mes)
        # self.assertEqual(None, response)
        timeEnd = time.time()
        print(timeEnd - timeStart)


if __name__ == '__main__':
    unittest.main()
