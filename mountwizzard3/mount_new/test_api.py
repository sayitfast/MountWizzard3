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
import logging
# external packages
# local imports
from mount_new.command import Command
from mount_new.configData import Data
from mount_new.api import Mount
from mount_new import logConfigTest


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.pathToTS = '~/PycharmProjects/MountWizzard3/config'

    def test_mount_class_instance_host_ip(self):
        host = '192.168.2.15'
        mount = Mount(host=host,
                      pathToTS=self.pathToTS,
                      )

    def test_mount_class_instance_host_name(self):
        host = '015-GM1000HPS.fritz.box'
        mount = Mount(host=host,
                      pathToTS=self.pathToTS,
                      )

    def test_mount_class_poll_slow(self):
        host = '015-GM1000HPS.fritz.box'
        mount = Mount(host=host,
                      pathToTS=self.pathToTS,
                      )
        mount.command.pollSlow()
        print(mount.data.fw)


if __name__ == '__main__':
    unittest.main()
