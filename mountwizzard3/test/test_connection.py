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
# local imports
from mount_new.connection import Connection
from test import configTest


class TestConnection(unittest.TestCase):

    CONNECTED = configTest.CONNECTED

    def setUp(self):
        pass
    #
    #
    # testing the connection against host presence
    #
    #

    def test_no_host_defined(self):
        mount = Connection()
        commandSet = ':U2#:Gev#:'
        ok, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('', response)

    def test_no_port_defined(self):
        mount = Connection(host='192.168.2.15')
        commandSet = ':U2#:Gev#:'
        ok, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('', response)

    def test_no_host_up(self):
        # according to RFC5737 we use the address ranges from
        # 192.0.2.0 - 192.0.2.255
        # 198.51.100.0 - 198.51.100.255
        # 203.0.113.0 - 203.0.113.255
        # for testing
        mount = Connection(host=('192.0.2.0', 3492))
        commandSet = ''
        ok, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('', response)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_host_ok(self):
        mount = Connection(host=('192.168.2.15', 3492))
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        ok, response, chunks = mount.communicate(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('10micron GM1000HPS', response[5])

    def test_unknown(self):
        mount = Connection(host=('192.168.2.15', 3492))
        commandSet = ':U2#:NotKnown#'
        ok, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertEqual('', response)

    #
    #
    # testing the command analyses against structural faults
    #
    #

    def test_responses_withoutCommand_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand('')
        self.assertEqual(True, noResponse)
        self.assertEqual(0, chunksToReceive)

    def test_responses_typeA_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':AP#:AL#')
        self.assertEqual(True, noResponse)
        self.assertEqual(0, chunksToReceive)

    def test_responses_typeB_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':FLIP#:')
        self.assertEqual(False, noResponse)
        self.assertEqual(0, chunksToReceive)

    def test_responses_typeC_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':GTMP1#')
        self.assertEqual(False, noResponse)
        self.assertEqual(1, chunksToReceive)

    def test_responses_typeAB_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':AP#:AL#:FLIP#')
        self.assertEqual(False, noResponse)
        self.assertEqual(0, chunksToReceive)

    def test_responses_typeAC_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':AP#:AL#:GTMP1#')
        self.assertEqual(False, noResponse)
        self.assertEqual(1, chunksToReceive)

    def test_responses_typeBC_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':FLIP#:GTMP1#')
        self.assertEqual(False, noResponse)
        self.assertEqual(1, chunksToReceive)

    def test_responses_typeABC_analyseCommand(self):
        mount = Connection()
        chunksToReceive, noResponse = mount._analyseCommand(':AP#:AL#:FLIP#:GTMP1#')
        self.assertEqual(False, noResponse)
        self.assertEqual(1, chunksToReceive)


if __name__ == '__main__':
    unittest.main()
