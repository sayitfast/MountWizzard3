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

# import basic stuff
import logging
import PyQt5
import time
from win32com.client.dynamic import Dispatch
import pythoncom


class Stick(PyQt5.QtCore.QThread):
    # signals for communication to main Thread / GUI
    logger = logging.getLogger(__name__)
    signalStickData = PyQt5.QtCore.pyqtSignal([dict], name='stickData')
    signalStickConnected = PyQt5.QtCore.pyqtSignal([int], name='stickConnected')

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.connected = 2
        self.ascom = None                                                                                                   # placeholder for ascom driver object
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverName = ''                                                                                                # driver object name
        self.slewing = False
        self.counter = 0
        self.initConfig()

    def initConfig(self):
        try:
            if 'ASCOMStickDriverName' in self.app.config:
                self.driverName = self.app.config['ASCOMStickDriverName']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ASCOMStickDriverName'] = self.driverName

    def run(self):                                                                                                          # runnable for doing the work
        pythoncom.CoInitialize()                                                                                            # needed for doing CO objects in threads
        self.connected = 0                                                                                                  # set connection flag for stick itself
        self.counter = 0
        while True:                                                                                                         # main loop for stick thread
            self.signalStickConnected.emit(self.connected)                                                                  # send status to GUI
            if self.connected == 1:                                                                                         # differentiate between dome connected or not
                if self.counter == 0:                                                                                       # jobs once done at the beginning
                    self.getStatusOnce()                                                                                    # task once
                if self.counter % 2 == 0:                                                                                   # all tasks with 200 ms
                    self.getStatusFast()                                                                                    # polling the mount status Ginfo
                if self.counter % 20 == 0:                                                                                  # all tasks with 3 s
                    self.getStatusMedium()                                                                                  # polling the mount
                if self.counter % 300 == 0:                                                                                 # all task with 1 minute
                    self.getStatusSlow()                                                                                    # slow ones
                self.counter += 1                                                                                           # increasing counter for selection
                time.sleep(.1)
            else:
                try:
                    if self.driverName == '':
                        self.connected = 2
                    else:
                        self.ascom = Dispatch(self.driverName)                                                              # load driver
                        self.ascom.connected = True
                        self.connected = 1                                                                                  # set status to connected
                        self.logger.info('driver chosen:{0}'.format(self.driverName))
                except AttributeError as e:
                    if self.driverName != '':
                        self.logger.warning('stick physically not connected {0}'.format(e))
                except Exception as e:                                                                                      # if general exception
                    if self.driverName != '':
                        self.logger.error('general exception: {0}'.format(e))
                    if self.driverName == '':
                        self.connected = 2
                    else:
                        self.connected = 0                                                                                  # run the driver setup dialog
                finally:                                                                                                    # still continua and try it again
                    pass                                                                                                    # needed for continue
                time.sleep(5)                                                                                               # wait for the next cycle
        self.ascom.Quit()
        pythoncom.CoUninitialize()                                                                                          # needed for doing COm objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         #

    def getStatusFast(self):
        pass

    def getStatusMedium(self):
        data = dict()
        try:
            data['DewPoint'] = self.ascom.DewPoint                                                                              # storing data in the signal object
            data['Temperature'] = self.ascom.Temperature                                                                        # actually there is single based communication
            data['Humidity'] = self.ascom.Humidity                                                                              # target should be queue
            data['Pressure'] = self.ascom.Pressure
            self.signalStickData.emit(data)                                                                                     # sending the data via signal
            if self.ascom.DewPoint == 0 and self.ascom.Humidity == 0:
                self.logger.error('error accessing stick, driver {0} status:{1}'.format(self.ascom, self.ascom.connected))
                self.connected = 0
            if self.ascom.TimeSinceLastUpdate('DewPoint') > 20:
                self.logger.error('stick hardware connection lost')
                self.connected = 0
        except Exception as e:
            self.logger.error('error accessing stick ascom data: {0}'.format(e))
            self.connected = 0

    def getStatusSlow(self):
        pass

    def getStatusOnce(self):
        pass

    def setupDriver(self):                                                                                                  #
        try:
            if self.ascom:
                self.ascom.connected = False
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'ObservingConditions'
            self.driverName = self.chooser.Choose(self.driverName)
            self.logger.info('driver chosen:{0}'.format(self.driverName))
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.app.messageQueue.put('Driver Exception in setupStick')                                                     # write to gui
            self.logger.error('general exception:{0}'.format(e))                                         # write to log
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary
