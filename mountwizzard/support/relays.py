############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016
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
            request.urlopen(self.ipSGProBase, None, .5).getcode()
            connected = True
        except Exception:
            connected = False
        finally:
            return connected

    def setStatus(self, response):
        lines = response.splitlines()                                                                                       # read over all the lines
        for i in range(len(lines)):                                                                                         # convert from text to array of floats
            if lines[i][0:7] == 'Status:':                                                                                  # here are the values of the relay stats
                self.stat[0] = (lines[i][8] == '1')
                self.stat[1] = (lines[i][10] == '1')
                self.stat[2] = (lines[i][13] == '1')
                self.stat[3] = (lines[i][15] == '1')
                self.stat[4] = (lines[i][18] == '1')
                self.stat[5] = (lines[i][20] == '1')
                self.stat[6] = (lines[i][23] == '1')
                self.stat[7] = (lines[i][25] == '1')
                self.logger.debug('setStatus -> status: {0}'.format(self.stat))
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
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FF0800')
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass

    def requestStatus(self):
        try:
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FF0700', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('requestStatus -> error {0}'.format(e))
        finally:
            pass

    def switchAllOff(self):
        try:
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/FFE000', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('switchAllOff -> error {0}'.format(e))
        finally:
            pass

    def switchCCD(self):
        try:
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/relays.cgi?relay=1', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('switchCCD -> error {0}'.format(e))
        finally:
            pass

    def switchHeater(self):
        try:
            f = request.urlopen('http://' + self.ui.le_ipRelaybox.text() + '/relays.cgi?relay=2', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass
