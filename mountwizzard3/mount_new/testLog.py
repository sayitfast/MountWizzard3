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
import logging
# external packages
# local imports

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d]'
                           + '[%(levelname)7s]'
                           + '[%(filename)22s]'
                           + '[%(lineno)5s]'
                           + '[%(funcName)20s]'
                           + '[%(threadName)10s]'
                           + '>>> %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )

