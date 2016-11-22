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

# import basic stuff
import logging
from PyQt5 import QtCore
import time
from win32com.client.dynamic import Dispatch
import pythoncom


class Dome(QtCore.QThread):
    # signals for communication to main Thread / GUI
    logger = logging.getLogger('dome_thread:')
    signalDomeConnected = QtCore.pyqtSignal([bool], name='domeConnected')

    def __init__(self, messageQueue):
        super().__init__()
        self.messageQueue = messageQueue
        self.connected = False
        self.ascom = None                                                                                                   # placeholder for ascom driver object
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverName = 'DomeSim.Dome'                                                                                    # driver object name

    def run(self):                                                                                                          # runnable for doing the work
        pythoncom.CoInitialize()                                                                                            # needed for doing COm objects in threads
        self.connected = False                                                                                              # set connection flag for stick itself
        while True:                                                                                                         # main loop for stick thread
            self.signalDomeConnected.emit(self.connected)                                                                   # send status to GUI
            if self.connected:                                                                                              # differentiate between dome connected or not
                pass
            else:
                try:
                    self.ascom = Dispatch(self.driverName)                                                                  # load driver
                    self.ascom.connected = True
                    self.connected = True                                                                                   # set status to connected
                except pythoncom.com_error as e:                                                                            # If win32com failure
                    self.messageQueue.put('Driver COM Error in dispatchDome')                                               # write message to gui
                    self.logger.error('run Dome -> connect win32com error: {0}'.format(e))                                  # write to logger
                    self.connected = False                                                                                  # set to disconnected
                except Exception as e:                                                                                      # if general exception
                    self.messageQueue.put('Driver COM Error in dispatchDome')                                               # write to gui
                    self.logger.error('run Dome -> general exception: {0}'.format(e))                                       # write to logger
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
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Dome'
            self.driverName = self.chooser.Choose(self.driverName)
            self.connected = False                                                                                          # run the driver setup dialog
        except pythoncom.com_error as e:                                                                                    # exception handling
            self.messageQueue.put('Driver COM Error in setupDome')                                                          # write to gui
            self.logger.error('setupDriver Dome -> win32com error:{0}'.format(e))                                           # write to log
            self.connected = False                                                                                          # set to disconnected
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupDome')                                                          # write to gui
            self.logger.error('setupDriver Dome -> general exception:{0}'.format(e))                                        # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary

if __name__ == "__main__":
    pass
