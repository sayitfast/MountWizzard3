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
import unittest

from mount_new.connection import Connection


class TestConnection(unittest.TestCase):

    def setUp(self):
        pass

    def test_no_host(self):
        mount = Connection(host='192.168.2.250', port=3492)
        commandSet = ':U2#:Gev#:'
        ok, mes, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertIn('socket error', mes)
        self.assertEqual('', response)

    def test_known(self):
        mount = Connection(host='192.168.2.15', port=3492)
        commandSet = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        ok, mes, response, chunks = mount.communicate(commandSet)
        self.assertEqual(True, ok)
        self.assertEqual('ok', mes)
        self.assertEqual('10micron GM1000HPS', response[5])

    def test_unknown(self):
        mount = Connection(host='192.168.2.15', port=3492)
        commandSet = ':U2#:NotKnown#'
        ok, mes, response, chunks = mount.communicate(commandSet)
        self.assertEqual(False, ok)
        self.assertIn('socket error', mes)
        self.assertEqual('', response)

    # testing the command analyses against structural faults
    def test_responses_typeA_analyseCommand(self):
        mount = Connection()
        number, response = mount._analyseCommand(':AP#:AL#')
        self.assertEqual(True, response)
        self.assertEqual(0, number)

    def test_responses_typeAB_analyseCommand(self):
        mount = Connection()
        number, response = mount._analyseCommand(':AP#:AL#:FLIP#')
        self.assertEqual(False, response)
        self.assertEqual(0, number)

    def test_responses_typeABC_analyseCommand(self):
        mount = Connection()
        number, response = mount._analyseCommand(':AP#:AL#:FLIP#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)

    def test_responses_typeAC_analyseCommand(self):
        mount = Connection()
        number, response = mount._analyseCommand(':AP#:AL#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)

    def test_responses_typeBC_analyseCommand(self):
        mount = Connection()
        number, response = mount._analyseCommand(':FLIP#:GTMP1#')
        self.assertEqual(False, response)
        self.assertEqual(1, number)


if __name__ == '__main__':
    unittest.main()
