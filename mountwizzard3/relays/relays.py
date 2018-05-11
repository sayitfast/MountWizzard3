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
import time
import PyQt5
import queue
import requests
from baseclasses import checkIP


class Relays(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CYCLE = 200
    CYCLE_STATUS = 500
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.app = app
        self.thread = thread
        self.statusTimer = None
        self.cycleTimer = None
        self.relayCommandQueue = queue.Queue()
        self.mutexIsRunning = PyQt5.QtCore.QMutex()
        self.mutexIPChange = PyQt5.QtCore.QMutex()

        self.stat = [False, False, False, False, False, False, False, False, False]
        self.username = ''
        self.password = ''
        self.relayIP = ''
        self.connected = False
        self.checkIP = checkIP.CheckIP()
        self.app.ui.btn_relay1.clicked.connect(lambda: self.relayCommandQueue.put(1))
        self.app.ui.btn_relay2.clicked.connect(lambda: self.relayCommandQueue.put(2))
        self.app.ui.btn_relay3.clicked.connect(lambda: self.relayCommandQueue.put(3))
        self.app.ui.btn_relay4.clicked.connect(lambda: self.relayCommandQueue.put(4))
        self.app.ui.btn_relay5.clicked.connect(lambda: self.relayCommandQueue.put(5))
        self.app.ui.btn_relay6.clicked.connect(lambda: self.relayCommandQueue.put(6))
        self.app.ui.btn_relay7.clicked.connect(lambda: self.relayCommandQueue.put(7))
        self.app.ui.btn_relay8.clicked.connect(lambda: self.relayCommandQueue.put(8))
        # signal slot
        self.app.ui.relay1Text.textEdited.connect(lambda: self.app.ui.btn_relay1.setText(self.app.ui.relay1Text.text()))
        self.app.ui.relay2Text.textEdited.connect(lambda: self.app.ui.btn_relay2.setText(self.app.ui.relay2Text.text()))
        self.app.ui.relay3Text.textEdited.connect(lambda: self.app.ui.btn_relay3.setText(self.app.ui.relay3Text.text()))
        self.app.ui.relay4Text.textEdited.connect(lambda: self.app.ui.btn_relay4.setText(self.app.ui.relay4Text.text()))
        self.app.ui.relay5Text.textEdited.connect(lambda: self.app.ui.btn_relay5.setText(self.app.ui.relay5Text.text()))
        self.app.ui.relay6Text.textEdited.connect(lambda: self.app.ui.btn_relay6.setText(self.app.ui.relay6Text.text()))
        self.app.ui.relay7Text.textEdited.connect(lambda: self.app.ui.btn_relay7.setText(self.app.ui.relay7Text.text()))
        self.app.ui.relay8Text.textEdited.connect(lambda: self.app.ui.btn_relay8.setText(self.app.ui.relay8Text.text()))
        self.app.ui.le_relayIP.editingFinished.connect(self.changedRelayClientConnectionSettings)
        self.app.ui.checkEnableRelay.stateChanged.connect(self.enableDisableRelay)

    def initConfig(self):
        view1 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay1Function.setView(view1)
        self.app.ui.relay1Function.addItem('Switch - Toggle')
        self.app.ui.relay1Function.addItem('Pulse 1 sec')
        view2 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay2Function.setView(view2)
        self.app.ui.relay2Function.addItem('Switch - Toggle')
        self.app.ui.relay2Function.addItem('Pulse 1 sec')
        view3 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay3Function.setView(view3)
        self.app.ui.relay3Function.addItem('Switch - Toggle')
        self.app.ui.relay3Function.addItem('Pulse 1 sec')
        view4 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay4Function.setView(view4)
        self.app.ui.relay4Function.addItem('Switch - Toggle')
        self.app.ui.relay4Function.addItem('Pulse 1 sec')
        view5 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay5Function.setView(view5)
        self.app.ui.relay5Function.addItem('Switch - Toggle')
        self.app.ui.relay5Function.addItem('Pulse 1 sec')
        view6 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay6Function.setView(view6)
        self.app.ui.relay6Function.addItem('Switch - Toggle')
        self.app.ui.relay6Function.addItem('Pulse 1 sec')
        view7 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay7Function.setView(view7)
        self.app.ui.relay7Function.addItem('Switch - Toggle')
        self.app.ui.relay7Function.addItem('Pulse 1 sec')
        view8 = PyQt5.QtWidgets.QListView()
        self.app.ui.relay8Function.setView(view8)
        self.app.ui.relay8Function.addItem('Switch - Toggle')
        self.app.ui.relay8Function.addItem('Pulse 1 sec')
        try:
            if 'Relay1Function' in self.app.config:
                self.app.ui.relay1Function.setCurrentIndex(self.app.config['Relay1Function'])
            if 'Relay2Function' in self.app.config:
                self.app.ui.relay2Function.setCurrentIndex(self.app.config['Relay2Function'])
            if 'Relay3Function' in self.app.config:
                self.app.ui.relay3Function.setCurrentIndex(self.app.config['Relay3Function'])
            if 'Relay4Function' in self.app.config:
                self.app.ui.relay4Function.setCurrentIndex(self.app.config['Relay4Function'])
            if 'Relay5Function' in self.app.config:
                self.app.ui.relay5Function.setCurrentIndex(self.app.config['Relay5Function'])
            if 'Relay6Function' in self.app.config:
                self.app.ui.relay6Function.setCurrentIndex(self.app.config['Relay6Function'])
            if 'Relay7Function' in self.app.config:
                self.app.ui.relay7Function.setCurrentIndex(self.app.config['Relay7Function'])
            if 'Relay8Function' in self.app.config:
                self.app.ui.relay8Function.setCurrentIndex(self.app.config['Relay8Function'])
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
            if 'RelayIP' in self.app.config:
                self.app.ui.le_relayIP.setText(self.app.config['RelayIP'])
                self.relayIP = self.app.config['RelayIP']
            if 'RelayUsername' in self.app.config:
                self.app.ui.le_relayUsername.setText(self.app.config['RelayUsername'])
            if 'RelayPassword' in self.app.config:
                self.app.ui.le_relayPassword.setText(self.app.config['RelayPassword'])
            if 'CheckEnableRelay' in self.app.config:
                self.app.ui.checkEnableRelay.setChecked(self.app.config['CheckEnableRelay'])
        except Exception as e:
            self.logger.error('Item in config.cfg for relay could not be initialized, error:{0}'.format(e))
        finally:
            pass
        self.changedRelayClientConnectionSettings()
        self.enableDisableRelay()

    def storeConfig(self):
        self.app.config['RelayIP'] = self.app.ui.le_relayIP.text()
        self.app.config['Relay1Function'] = self.app.ui.relay1Function.currentIndex()
        self.app.config['Relay2Function'] = self.app.ui.relay2Function.currentIndex()
        self.app.config['Relay3Function'] = self.app.ui.relay3Function.currentIndex()
        self.app.config['Relay4Function'] = self.app.ui.relay4Function.currentIndex()
        self.app.config['Relay5Function'] = self.app.ui.relay5Function.currentIndex()
        self.app.config['Relay6Function'] = self.app.ui.relay6Function.currentIndex()
        self.app.config['Relay7Function'] = self.app.ui.relay7Function.currentIndex()
        self.app.config['Relay8Function'] = self.app.ui.relay8Function.currentIndex()
        self.app.config['Relay1Text'] = self.app.ui.relay1Text.text()
        self.app.config['Relay2Text'] = self.app.ui.relay2Text.text()
        self.app.config['Relay3Text'] = self.app.ui.relay3Text.text()
        self.app.config['Relay4Text'] = self.app.ui.relay4Text.text()
        self.app.config['Relay5Text'] = self.app.ui.relay5Text.text()
        self.app.config['Relay6Text'] = self.app.ui.relay6Text.text()
        self.app.config['Relay7Text'] = self.app.ui.relay7Text.text()
        self.app.config['Relay8Text'] = self.app.ui.relay8Text.text()
        self.app.config['RelayUsername'] = self.app.ui.le_relayUsername.text()
        self.app.config['RelayPassword'] = self.app.ui.le_relayPassword.text()
        self.app.config['CheckEnableRelay'] = self.app.ui.checkEnableRelay.isChecked()

    def changedRelayClientConnectionSettings(self):
        if self.isRunning:
            self.mutexIPChange.lock()
            self.stop()
            self.relayIP = self.app.ui.le_relayIP.text()
            self.thread.start()
            self.mutexIPChange.unlock()
        else:
            self.mutexIPChange.lock()
            self.relayIP = self.app.ui.le_relayIP.text()
            self.mutexIPChange.unlock()
        self.app.messageQueue.put('Setting IP address for relay to: {0}\n'.format(self.relayIP))

    def enableDisableRelay(self):
        # get relay tab index:
        index = self.app.ui.mainTabWidget.indexOf(self.app.ui.mainTabWidget.findChild(PyQt5.QtWidgets.QWidget, 'Relay'))
        if self.app.ui.checkEnableRelay.isChecked():
            if not self.isRunning:
                self.thread.start()
            self.app.ui.mainTabWidget.setTabEnabled(index, True)
            self.app.messageQueue.put('Relay enabled\n')
        else:
            self.connected = False
            if self.isRunning:
                self.stop()
            self.app.ui.mainTabWidget.setTabEnabled(index, False)
            self.app.messageQueue.put('Relay disabled\n')
            self.logger.info('Relay is disabled')
        self.app.ui.mainTabWidget.style().unpolish(self.app.ui.mainTabWidget)
        self.app.ui.mainTabWidget.style().polish(self.app.ui.mainTabWidget)

    def run(self):
        self.logger.info('relay started')
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        # timers
        self.statusTimer = PyQt5.QtCore.QTimer(self)
        self.statusTimer.setSingleShot(False)
        self.statusTimer.timeout.connect(self.getStatus)
        self.statusTimer.start(self.CYCLE_STATUS)
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        # when the worker thread finished, it emit the finished signal to the parent to clean up
        self.logger.info('relay stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.statusTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.relayCommandQueue.empty():
            value = self.relayCommandQueue.get()
            self.runRelay(value)

    @PyQt5.QtCore.pyqtSlot()
    def getStatus(self):
        if self.checkIP.checkIPAvailable(self.relayIP, 80):
            try:
                result = self.geturl('http://' + self.relayIP + '/status.xml')
                self.setStatusGUI(result.content.decode())
            except Exception as e:
                self.logger.error('Status error {0}'.format(e))
            finally:
                pass

    def setStatusGUI(self, response):
        lines = response.splitlines()
        if lines[0] == '<response>':
            self.stat[1] = (lines[2][8] == '1')
            self.stat[2] = (lines[3][8] == '1')
            self.stat[3] = (lines[4][8] == '1')
            self.stat[4] = (lines[5][8] == '1')
            self.stat[5] = (lines[6][8] == '1')
            self.stat[6] = (lines[7][8] == '1')
            self.stat[7] = (lines[8][8] == '1')
            self.stat[8] = (lines[9][8] == '1')
            self.logger.debug('status: {0}'.format(self.stat))
        if self.stat[1]:
            self.app.ui.btn_relay1.setProperty('running', True)
            self.app.ui.btn_relay1.style().unpolish(self.app.ui.btn_relay1)
            self.app.ui.btn_relay1.style().polish(self.app.ui.btn_relay1)
        else:
            self.app.ui.btn_relay1.setProperty('running', False)
            self.app.ui.btn_relay1.style().unpolish(self.app.ui.btn_relay1)
            self.app.ui.btn_relay1.style().polish(self.app.ui.btn_relay1)
        if self.stat[2]:
            self.app.ui.btn_relay2.setProperty('running', True)
            self.app.ui.btn_relay2.style().unpolish(self.app.ui.btn_relay2)
            self.app.ui.btn_relay2.style().polish(self.app.ui.btn_relay2)
        else:
            self.app.ui.btn_relay2.setProperty('running', False)
            self.app.ui.btn_relay2.style().unpolish(self.app.ui.btn_relay2)
            self.app.ui.btn_relay2.style().polish(self.app.ui.btn_relay2)
        if self.stat[3]:
            self.app.ui.btn_relay3.setProperty('running', True)
            self.app.ui.btn_relay3.style().unpolish(self.app.ui.btn_relay3)
            self.app.ui.btn_relay3.style().polish(self.app.ui.btn_relay3)
        else:
            self.app.ui.btn_relay3.setProperty('running', False)
            self.app.ui.btn_relay3.style().unpolish(self.app.ui.btn_relay3)
            self.app.ui.btn_relay3.style().polish(self.app.ui.btn_relay3)
        if self.stat[4]:
            self.app.ui.btn_relay4.setProperty('running', True)
            self.app.ui.btn_relay4.style().unpolish(self.app.ui.btn_relay4)
            self.app.ui.btn_relay4.style().polish(self.app.ui.btn_relay4)
        else:
            self.app.ui.btn_relay4.setProperty('running', False)
            self.app.ui.btn_relay4.style().unpolish(self.app.ui.btn_relay4)
            self.app.ui.btn_relay4.style().polish(self.app.ui.btn_relay4)
        if self.stat[5]:
            self.app.ui.btn_relay5.setProperty('running', True)
            self.app.ui.btn_relay5.style().unpolish(self.app.ui.btn_relay5)
            self.app.ui.btn_relay5.style().polish(self.app.ui.btn_relay5)
        else:
            self.app.ui.btn_relay5.setProperty('running', False)
            self.app.ui.btn_relay5.style().unpolish(self.app.ui.btn_relay5)
            self.app.ui.btn_relay5.style().polish(self.app.ui.btn_relay5)
        if self.stat[6]:
            self.app.ui.btn_relay6.setProperty('running', True)
            self.app.ui.btn_relay6.style().unpolish(self.app.ui.btn_relay6)
            self.app.ui.btn_relay6.style().polish(self.app.ui.btn_relay6)
        else:
            self.app.ui.btn_relay6.setProperty('running', False)
            self.app.ui.btn_relay6.style().unpolish(self.app.ui.btn_relay6)
            self.app.ui.btn_relay6.style().polish(self.app.ui.btn_relay6)
        if self.stat[7]:
            self.app.ui.btn_relay7.setProperty('running', True)
            self.app.ui.btn_relay7.style().unpolish(self.app.ui.btn_relay7)
            self.app.ui.btn_relay7.style().polish(self.app.ui.btn_relay7)
        else:
            self.app.ui.btn_relay7.setProperty('running', False)
            self.app.ui.btn_relay7.style().unpolish(self.app.ui.btn_relay7)
            self.app.ui.btn_relay7.style().polish(self.app.ui.btn_relay7)
        if self.stat[8]:
            self.app.ui.btn_relay8.setProperty('running', True)
            self.app.ui.btn_relay8.style().unpolish(self.app.ui.btn_relay8)
            self.app.ui.btn_relay8.style().polish(self.app.ui.btn_relay8)
        else:
            self.app.ui.btn_relay8.setProperty('running', False)
            self.app.ui.btn_relay8.style().unpolish(self.app.ui.btn_relay8)
            self.app.ui.btn_relay8.style().polish(self.app.ui.btn_relay8)

    def geturl(self, url):
        result = requests.get(url, auth=requests.auth.HTTPBasicAuth(self.app.ui.le_relayUsername.text(), self.app.ui.le_relayPassword.text()))
        return result

    def runRelay(self, relayNumber):
        if self.checkIP.checkIPAvailable(self.relayIP, 80):
            if relayNumber == 1:
                if self.app.ui.relay1Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 2:
                if self.app.ui.relay2Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 3:
                if self.app.ui.relay3Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 4:
                if self.app.ui.relay4Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 5:
                if self.app.ui.relay5Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 6:
                if self.app.ui.relay6Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 7:
                if self.app.ui.relay7Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)
            if relayNumber == 8:
                if self.app.ui.relay8Function.currentIndex() == 0:
                    self.switch(relayNumber)
                else:
                    self.pulse(relayNumber)

    def pulse(self, relayNumber):
        try:
            self.geturl('http://' + self.relayIP + '/FF0{0:1d}01'.format(relayNumber))
            time.sleep(1)
            self.geturl('http://' + self.relayIP + '/FF0{0:1d}00'.format(relayNumber))
        except Exception as e:
            self.logger.error('Relay:{0}, error:{1}'.format(relayNumber, e))
        finally:
            pass

    def switch(self, relayNumber):
        try:
            self.geturl('http://' + self.relayIP + '/relays.cgi?relay={0:1d}'.format(relayNumber))
        except Exception as e:
            self.logger.error('Relay:{0}, error:{1}'.format(relayNumber, e))
        finally:
            pass
