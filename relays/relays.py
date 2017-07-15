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

    def __init__(self, app):
        self.app = app
        self.stat = [False, False, False, False, False, False, False, False]
        self.connected = self.checkConnection()
        if self.connected:
            self.requestStatus()

    def initConfig(self):
        try:
            pass
        except Exception as e:
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        pass

    def relayIP(self):
        value = self.app.ui.le_relayIP.text().split('.')
        if len(value) != 4:
            self.logger.error('formatIP       -> wrong input value:{0}'.format(value))
            self.app.messageQueue.put('Wrong IP configuration for relay, please check!')
            return
        v = []
        for i in range(0, 4):
            v.append(int(value[i]))
        ip = '{0:d}.{1:d}.{2:d}.{3:d}'.format(v[0], v[1], v[2], v[3])
        return ip

    def checkConnection(self):
        connected = False
        try:
            request.urlopen('http://' + self.relayIP(), None, .5).getcode()
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
        if self.stat[1]:
            self.app.ui.btn_switchHeater.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_switchHeater.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[3]:
            self.app.ui.btn_switchMount.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_switchMount.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[4]:
            self.app.ui.btn_switchCCD.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_switchCCD.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[5]:
            self.app.ui.btn_switchPC.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_switchPC.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def bootMount(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/FF0801')
            time.sleep(1)
            request.urlopen('http://' + self.relayIP() + '/FF0800')
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass

    def requestStatus(self):
        try:
            f = request.urlopen('http://' + self.relayIP() + '/status.xml', None, .5)
            self.setStatus(f.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('requestStatus -> error {0}'.format(e))
        finally:
            pass

    def switchAllOff(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/FFE000', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchAllOff -> error {0}'.format(e))
        finally:
            pass

    def switchCCD(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/relays.cgi?relay=5', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchCCD -> error {0}'.format(e))
        finally:
            pass

    def switchMount(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/relays.cgi?relay=4', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchCCD -> error {0}'.format(e))
        finally:
            pass

    def switchPC(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/relays.cgi?relay=6', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchCCD -> error {0}'.format(e))
        finally:
            pass

    def switchHeater(self):
        try:
            request.urlopen('http://' + self.relayIP() + '/relays.cgi?relay=2', None, .5)
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchHeater -> error {0}'.format(e))
        finally:
            pass
