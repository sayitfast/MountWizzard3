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

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d]'
                           + '[%(levelname)7s]'
                           + '[%(filename)22s]'
                           + '[%(lineno)5s]'
                           + '[%(funcName)20s]'
                           + '[%(threadName)10s]'
                           + '>>> %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.pathToTimescaleData = '~/PycharmProjects/MountWizzard3/config'

    def test_mount_class_instance_host_ip(self):
        host = '192.168.2.15'
        mount = Mount(host=host,
                      pathToTimescaleData=self.pathToTimescaleData,
                      )

    def test_mount_class_instance_host_name(self):
        host = '015-GM1000HPS.fritz.box'
        mount = Mount(host=host,
                      pathToTimescaleData=self.pathToTimescaleData,
                      )


if __name__ == '__main__':
    unittest.main()
