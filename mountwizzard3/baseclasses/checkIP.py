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
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import socket


class CheckIP:
    logger = logging.getLogger(__name__)

    def __init__(self):
        pass

    def checkIPAvailable(self, Host, Port):
        returnValue = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.connect_ex((Host, Port))
            if result == 0:
                returnValue = True
            else:
                returnValue = False
        except socket.gaierror:
            self.logger.info('Host address could not be resolved: host {0}:{1}'.format(Host, Port))
        except Exception as e:
            self.logger.error('Error checking host {0}:{1}, error: {2}'.format(Host, Port, e))
        finally:
            sock.close()
        return returnValue
