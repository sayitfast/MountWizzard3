############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################

import logging
import time
from urllib import request


class Relays:
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, ui):
        self.ui = ui
        self.stat = [False, False, False, False, False, False, False, False]
        self.connected = self.checkConnection()
        if self.connected:
            self.requestStatus()

    def checkConnection(self):
        connected = False
        try:
            request.urlopen('http://' + self.ui.le_ipRelaybox.text(), None, .5).getcode()
            connected = True
        except Exception as e:
            connected = False
            self.logger.error('checkConnection-> connection error:{0}'.format(e))
        finally:
            return connected

    def setStatus(self, response):
        lines = response.splitlines()                                                                                       # read over all the lines
        if lines[0] == '<response>':                                                                                        # here are the values of the relay stats
            self.stat[0] = (lines[2][8] == '1')
            self.stat[1] = (lines[3][8] == '1')
            self.stat[2] = (lines[4][8] == '1')
            self.stat[3] = (lines[5][8] == '1')
            self.stat[4] = (lines[6][8] == '1')
            self.stat[5] = (lines[7][8] == '1')
            self.stat[6] = (lines[8][8] == '1')
            self.stat[7] = (lines[9][8] == '1')
            self.logger.debug('relay setStatus-> status: {0}'.format(self.stat))
        if self.stat[0]:
            self.ui.btn_switchCCD.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.ui.btn_switchCCD.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[1]:
            self.ui.btn_switchHeater.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.ui.btn_switchHeater.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def bootMount(self):
        try:
            request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FF0801')
            time.sleep(1)
            request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FF0800')
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass

    def requestStatus(self):
        try:
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/status.xml', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('requestStatus -> error {0}'.format(e))
        finally:
            pass

    def switchAllOff(self):
        try:
            request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FFE000', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchAllOff -> error {0}'.format(e))
        finally:
            pass

    def switchCCD(self):
        try:
            request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/relays.cgi?relay=1', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchCCD -> error {0}'.format(e))
        finally:
            pass

    def switchHeater(self):
        try:
            request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/relays.cgi?relay=2', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass
