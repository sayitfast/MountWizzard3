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
    signalStickConnected = QtCore.pyqtSignal([bool], name='stickConnected')

    def __init__(self, messageQueue):
        super().__init__()
        self.messageQueue = messageQueue
        self.connected = False
        self.ascom = None                                                                                                   # placeholder for ascom driver object

    def run(self):                                                                                                          # runnable for doing the work
        pythoncom.CoInitialize()                                                                                            # needed for doing COm objects in threads
        data = dict()                                                                                                       # data type reservation
        self.connected = False                                                                                              # set connection flag for stick itself
        while True:                                                                                                         # main loop for stick thread
            self.signalStickConnected.emit(self.connected)                                                                  # send status to GUI
            if self.connected:                                                                                              # differentiate between stick connected or not
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
                    self.ascom = Dispatch('ASCOM.Stickstation.Observingconditions')                                         # load driver
                    self.ascom.connected = True                                                                             # enables data transfer
                    self.connected = True                                                                                   # set status to connected
                except Exception as e:                                                                                      # if general exception
                    self.messageQueue.put('Driver COM Error in dispatchStick')                                              # write to gui
                    self.logger.error('run Stick      -> general exception in dispatchStick: {0}'.format(e))                # write to logger
                    self.connected = False                                                                                  # set to disconnected
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
            if self.connected:
                self.ascom.SetupDialog()                                                                                    # run the driver setup dialog
            else:
                self.messageQueue.put('Driver Stick not connected')
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupDriverStick')                                                   # write to gui
            self.logger.error('setupDriverStick -> general exception in setup:{0}'.format(e))                              # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary
