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
from PyQt5 import QtCore
import time
from win32com.client.dynamic import Dispatch
import pythoncom


class Stick(QtCore.QThread):
    # signals for communication to main Thread / GUI
    logger = logging.getLogger(__name__)
    signalStickData = QtCore.pyqtSignal([dict], name='stickData')
    signalStickConnected = QtCore.pyqtSignal([float], name='stickConnected')

    def __init__(self, messageQueue):
        super().__init__()
        self.messageQueue = messageQueue
        self.connected = 2
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverName = ''                                                                                                # driver object name
        self.ascom = None                                                                                                   # placeholder for ascom driver object

    def run(self):                                                                                                          # runnable for doing the work
        pythoncom.CoInitialize()                                                                                            # needed for doing COm objects in threads
        data = dict()                                                                                                       # data type reservation
        self.connected = 0                                                                                                  # set connection flag for stick itself
        while True:                                                                                                         # main loop for stick thread
            self.signalStickConnected.emit(self.connected)                                                                  # send status to GUI
            if self.connected == 1:                                                                                         # differentiate between dome connected or not
                try:
                    data['DewPoint'] = self.ascom.DewPoint                                                                  # storing data in the signal object
                    data['Temperature'] = self.ascom.Temperature                                                            # actually there is single based communication
                    data['Humidity'] = self.ascom.Humidity                                                                  # target should be queue
                    data['Pressure'] = self.ascom.Pressure                                                                  #
                    self.signalStickData.emit(data)                                                                         # sending the data via signal
                except pythoncom.com_error as e:                                                                            # if error, than put it to queue
                    self.connected = False                                                                                  # if error occurs, set to disconnected
                    self.messageQueue.put('Driver COM Error in connectStick')                                               # write to gui
                    self.logger.error('run Stick      -> get data error: {0}'.format(e))                                    # write to logfile
            else:                                                                                                           # otherwise try to connect
                try:
                    if self.driverName == '':
                        self.connected = 2
                    else:
                        self.ascom = Dispatch(self.driverName)                                                              # load driver
                        self.ascom.connected = True
                        self.connected = 1                                                                                  # set status to connected
                except Exception as e:                                                                                      # if general exception
                    if self.driverName != '':
                        self.logger.error('run Stick      -> general exception: {0}'.format(e))                             # write to logger
                    if self.driverName == '':
                        self.connected = 2
                    else:
                        self.connected = 0                                                                                  # run the driver setup dialog
                    self.messageQueue.put('Driver COM Error in dispatchStick')                                              # write to gui
                    self.logger.error('run Stick      -> general exception in dispatchStick: {0}'.format(e))                # write to logger
                finally:                                                                                                    # still continua and try it again
                    pass                                                                                                    # needed for continue
            time.sleep(1)                                                                                                   # wait for the next cycle
        self.ascom.Quit()
        pythoncom.CoUninitialize()                                                                                          # needed for doing COm objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         #

    def setupDriver(self):                                                                                                  #
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'ObservingConditions'
            self.driverName = self.chooser.Choose(self.driverName)
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupStick')                                                          # write to gui
            self.logger.error('setupDriverStick-> general exception:{0}'.format(e))                                         # write to log
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary
