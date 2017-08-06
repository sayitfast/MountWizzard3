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
import requests


class Relays:
    logger = logging.getLogger(__name__)                                                                                    # logging enabling

    def __init__(self, app):
        self.app = app
        self.stat = [False, False, False, False, False, False, False, False, False]
        self.username = ''
        self.password = ''
        self.connected = self.checkConnection()
        if self.connected:
            self.requestStatus()
        self.initConfig()
        self.app.ui.btn_relay1.clicked.connect(lambda: self.runRelay(1))
        self.app.ui.btn_relay2.clicked.connect(lambda: self.runRelay(2))
        self.app.ui.btn_relay3.clicked.connect(lambda: self.runRelay(3))
        self.app.ui.btn_relay4.clicked.connect(lambda: self.runRelay(4))
        self.app.ui.btn_relay5.clicked.connect(lambda: self.runRelay(5))
        self.app.ui.btn_relay6.clicked.connect(lambda: self.runRelay(6))
        self.app.ui.btn_relay7.clicked.connect(lambda: self.runRelay(7))
        self.app.ui.btn_relay8.clicked.connect(lambda: self.runRelay(8))
        self.app.ui.relay1Text.textChanged.connect(lambda: self.app.ui.btn_relay1.setText(self.app.ui.relay1Text.text()))
        self.app.ui.relay2Text.textChanged.connect(lambda: self.app.ui.btn_relay2.setText(self.app.ui.relay2Text.text()))
        self.app.ui.relay3Text.textChanged.connect(lambda: self.app.ui.btn_relay3.setText(self.app.ui.relay3Text.text()))
        self.app.ui.relay4Text.textChanged.connect(lambda: self.app.ui.btn_relay4.setText(self.app.ui.relay4Text.text()))
        self.app.ui.relay5Text.textChanged.connect(lambda: self.app.ui.btn_relay5.setText(self.app.ui.relay5Text.text()))
        self.app.ui.relay6Text.textChanged.connect(lambda: self.app.ui.btn_relay6.setText(self.app.ui.relay6Text.text()))
        self.app.ui.relay7Text.textChanged.connect(lambda: self.app.ui.btn_relay7.setText(self.app.ui.relay7Text.text()))
        self.app.ui.relay8Text.textChanged.connect(lambda: self.app.ui.btn_relay8.setText(self.app.ui.relay8Text.text()))

    def initConfig(self):
        try:
            if 'RelayIP' in self.app.config:
                self.app.ui.le_relayIP.setText(self.app.config['RelayIP'])
            if 'Relay1Switch' in self.app.config:
                self.app.ui.relay1Switch.setChecked(self.app.config['Relay1Switch'])
            if 'Relay2Switch' in self.app.config:
                self.app.ui.relay2Switch.setChecked(self.app.config['Relay2Switch'])
            if 'Relay3Switch' in self.app.config:
                self.app.ui.relay3Switch.setChecked(self.app.config['Relay3Switch'])
            if 'Relay4Switch' in self.app.config:
                self.app.ui.relay4Switch.setChecked(self.app.config['Relay4Switch'])
            if 'Relay5Switch' in self.app.config:
                self.app.ui.relay5Switch.setChecked(self.app.config['Relay5Switch'])
            if 'Relay6Switch' in self.app.config:
                self.app.ui.relay6Switch.setChecked(self.app.config['Relay6Switch'])
            if 'Relay7Switch' in self.app.config:
                self.app.ui.relay7Switch.setChecked(self.app.config['Relay7Switch'])
            if 'Relay8Switch' in self.app.config:
                self.app.ui.relay8Switch.setChecked(self.app.config['Relay8Switch'])
            if 'Relay1Text' in self.app.config:
                self.app.ui.relay1Text.setText(self.app.config['Relay1Text'])
                self.app.ui.btn_relay1.setText(self.app.config['Relay1Text'])
            if 'Relay2Text' in self.app.config:
                self.app.ui.relay2Text.setText(self.app.config['Relay2Text'])
                self.app.ui.btn_relay2.setText(self.app.config['Relay2Text'])
            if 'Relay3Text' in self.app.config:
                self.app.ui.relay3Text.setText(self.app.config['Relay3Text'])
                self.app.ui.btn_relay3.setText(self.app.config['Relay3Text'])
            if 'Relay4Text' in self.app.config:
                self.app.ui.relay4Text.setText(self.app.config['Relay4Text'])
                self.app.ui.btn_relay4.setText(self.app.config['Relay4Text'])
            if 'Relay5Text' in self.app.config:
                self.app.ui.relay5Text.setText(self.app.config['Relay5Text'])
                self.app.ui.btn_relay5.setText(self.app.config['Relay5Text'])
            if 'Relay6Text' in self.app.config:
                self.app.ui.relay6Text.setText(self.app.config['Relay6Text'])
                self.app.ui.btn_relay6.setText(self.app.config['Relay6Text'])
            if 'Relay7Text' in self.app.config:
                self.app.ui.relay7Text.setText(self.app.config['Relay7Text'])
                self.app.ui.btn_relay7.setText(self.app.config['Relay7Text'])
            if 'Relay8Text' in self.app.config:
                self.app.ui.relay8Text.setText(self.app.config['Relay8Text'])
                self.app.ui.btn_relay8.setText(self.app.config['Relay8Text'])
            if 'Relay1Pulse' in self.app.config:
                self.app.ui.relay1Pulse.setChecked(self.app.config['Relay1Pulse'])
            if 'Relay2Pulse' in self.app.config:
                self.app.ui.relay2Pulse.setChecked(self.app.config['Relay2Pulse'])
            if 'Relay3Pulse' in self.app.config:
                self.app.ui.relay3Pulse.setChecked(self.app.config['Relay3Pulse'])
            if 'Relay4Pulse' in self.app.config:
                self.app.ui.relay4Pulse.setChecked(self.app.config['Relay4Pulse'])
            if 'Relay5Pulse' in self.app.config:
                self.app.ui.relay5Pulse.setChecked(self.app.config['Relay5Pulse'])
            if 'Relay6Pulse' in self.app.config:
                self.app.ui.relay6Pulse.setChecked(self.app.config['Relay6Pulse'])
            if 'Relay7Pulse' in self.app.config:
                self.app.ui.relay7Pulse.setChecked(self.app.config['Relay7Pulse'])
            if 'Relay8Pulse' in self.app.config:
                self.app.ui.relay8Pulse.setChecked(self.app.config['Relay8Pulse'])
            if 'KMUsername' in self.app.config:
                self.app.ui.KMUsername.setText(self.app.config['KMUsername'])
            if 'KMPassword' in self.app.config:
                self.app.ui.KMPassword.setText(self.app.config['KMPassword'])
        except Exception as e:
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['RelayIP'] = self.app.ui.le_relayIP.text()
        self.app.config['Relay1Switch'] = self.app.ui.relay1Switch.isChecked()
        self.app.config['Relay2Switch'] = self.app.ui.relay2Switch.isChecked()
        self.app.config['Relay3Switch'] = self.app.ui.relay3Switch.isChecked()
        self.app.config['Relay4Switch'] = self.app.ui.relay4Switch.isChecked()
        self.app.config['Relay5Switch'] = self.app.ui.relay5Switch.isChecked()
        self.app.config['Relay6Switch'] = self.app.ui.relay6Switch.isChecked()
        self.app.config['Relay7Switch'] = self.app.ui.relay7Switch.isChecked()
        self.app.config['Relay8Switch'] = self.app.ui.relay8Switch.isChecked()
        self.app.config['Relay1Text'] = self.app.ui.relay1Text.text()
        self.app.config['Relay2Text'] = self.app.ui.relay2Text.text()
        self.app.config['Relay3Text'] = self.app.ui.relay3Text.text()
        self.app.config['Relay4Text'] = self.app.ui.relay4Text.text()
        self.app.config['Relay5Text'] = self.app.ui.relay5Text.text()
        self.app.config['Relay6Text'] = self.app.ui.relay6Text.text()
        self.app.config['Relay7Text'] = self.app.ui.relay7Text.text()
        self.app.config['Relay8Text'] = self.app.ui.relay8Text.text()
        self.app.config['Relay1Pulse'] = self.app.ui.relay1Pulse.isChecked()
        self.app.config['Relay2Pulse'] = self.app.ui.relay2Pulse.isChecked()
        self.app.config['Relay3Pulse'] = self.app.ui.relay3Pulse.isChecked()
        self.app.config['Relay4Pulse'] = self.app.ui.relay4Pulse.isChecked()
        self.app.config['Relay5Pulse'] = self.app.ui.relay5Pulse.isChecked()
        self.app.config['Relay6Pulse'] = self.app.ui.relay6Pulse.isChecked()
        self.app.config['Relay7Pulse'] = self.app.ui.relay7Pulse.isChecked()
        self.app.config['Relay8Pulse'] = self.app.ui.relay8Pulse.isChecked()
        self.app.config['KMUsername'] = self.app.ui.KMUsername.text()
        self.app.config['KMPassword'] = self.app.ui.KMPassword.text()

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
            result = self.geturl('http://' + self.relayIP())
            result.getcode()
            connected = True
        except Exception as e:
            connected = False
            self.logger.error('checkConnection-> connection error:{0}'.format(e))
        finally:
            return connected

    def setStatus(self, response):
        lines = response.splitlines()                                                                                       # read over all the lines
        if lines[0] == '<response>':                                                                                        # here are the values of the relay stats
            self.stat[1] = (lines[2][8] == '1')
            self.stat[2] = (lines[3][8] == '1')
            self.stat[3] = (lines[4][8] == '1')
            self.stat[4] = (lines[5][8] == '1')
            self.stat[5] = (lines[6][8] == '1')
            self.stat[6] = (lines[7][8] == '1')
            self.stat[7] = (lines[8][8] == '1')
            self.stat[8] = (lines[9][8] == '1')
            self.logger.debug('relay setStatus-> status: {0}'.format(self.stat))
        if self.stat[1]:
            self.app.ui.btn_relay1.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay1.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[2]:
            self.app.ui.btn_relay2.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay2.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[3]:
            self.app.ui.btn_relay3.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay3.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[4]:
            self.app.ui.btn_relay4.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay4.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[5]:
            self.app.ui.btn_relay5.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay5.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[6]:
            self.app.ui.btn_relay6.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay6.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[7]:
            self.app.ui.btn_relay7.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay7.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
        if self.stat[8]:
            self.app.ui.btn_relay8.setStyleSheet('background-color: rgb(42, 130, 218)')
        else:
            self.app.ui.btn_relay8.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def runRelay(self, relayNumber):
        if relayNumber == 1:
            if self.app.ui.relay1Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 2:
            if self.app.ui.relay2Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 3:
            if self.app.ui.relay3Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 4:
            if self.app.ui.relay4Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 5:
            if self.app.ui.relay5Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 6:
            if self.app.ui.relay6Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 7:
            if self.app.ui.relay7Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)
        if relayNumber == 8:
            if self.app.ui.relay8Switch.isChecked():
                self.switch(relayNumber)
            else:
                self.pulse(relayNumber)

    def geturl(self, url):
        result = requests.get(url, auth=requests.auth.HTTPBasicAuth(self.app.ui.KMUsername.text(), self.app.ui.KMPassword.text()))
        return result

    def pulse(self, relayNumber):
        try:
            self.geturl('http://' + self.relayIP() + '/FF0{0:1d}01'.format(relayNumber))
            time.sleep(1)
            self.geturl('http://' + self.relayIP() + '/FF0{0:1d}00'.format(relayNumber))
            self.requestStatus()
        except Exception as e:
            self.logger.error('pulse          -> relay:{0}, error:{1}'.format(relayNumber, e))
        finally:
            pass

    def switch(self, relayNumber):
        try:
            self.geturl('http://' + self.relayIP() + '/relays.cgi?relay={0:1d}'.format(relayNumber))
            self.requestStatus()
        except Exception as e:
            self.logger.error('switch         -> relay:{0}, error:{1}'.format(relayNumber, e))
        finally:
            pass

    def requestStatus(self):
        try:
            result = self.geturl('http://' + self.relayIP() + '/status.xml')
            self.setStatus(result.read().decode('utf-8'))
        except Exception as e:
            self.logger.error('requestStatus -> error {0}'.format(e))
        finally:
            pass

    def switchAllOff(self):
        try:
            self.geturl('http://' + self.relayIP() + '/FFE000')
            self.requestStatus()
        except Exception as e:
            self.logger.error('switchAllOff -> error {0}'.format(e))
        finally:
            pass
