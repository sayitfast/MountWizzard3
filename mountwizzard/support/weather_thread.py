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


class Weather(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems
    signalWeatherData = QtCore.pyqtSignal([dict], name='weatherData')                                                       # single for data transfer to gui
    signalWeatherConnected = QtCore.pyqtSignal([bool], name='weatherConnected')                                             # signal for connection status

    def __init__(self, messageQueue):                                                                                       # inti for thread
        super().__init__()                                                                                                  #
        self.messageQueue = messageQueue                                                                                    # get message queue for error to gui
        self.ascom = None                                                                                                   # place for ascom driver
        self.connected = False                                                                                              # set to no connection

    def run(self):                                                                                                          # main loop
        pythoncom.CoInitialize()                                                                                            # needed for threading and win32com
        data = dict()                                                                                                       # set data type for transfer
        self.connected = False                                                                                              # no connection
        while True:                                                                                                         # run main loop
            self.signalWeatherConnected.emit(self.connected)                                                                # send status
            if self.connected:                                                                                              # if connected transmit the data through signals
                try:                                                                                                        # target should be queue
                    data['DewPoint'] = self.ascom.DewPoint                                                                  #
                    data['Temperature'] = self.ascom.Temperature                                                            #
                    data['Humidity'] = self.ascom.Humidity                                                                  #
                    data['Pressure'] = self.ascom.Pressure                                                                  #
                    data['CloudCover'] = self.ascom.CloudCover                                                              #
                    data['RainRate'] = self.ascom.RainRate                                                                  #
                    data['WindSpeed'] = self.ascom.WindSpeed                                                                #
                    data['WindDirection'] = self.ascom.WindDirection                                                        #
                    self.signalWeatherData.emit(data)                                                                       # send data
                except pythoncom.com_error as e:                                                                            # error handling
                    self.messageQueue.put('Driver win32com error in connectWeather')                                        # write to gui
                    self.logger.error('run Weather    -> win32com error in connectWeather: {0}'.format(e))                  # write to log
            else:
                try:
                    self.ascom = Dispatch('ASCOM.OpenWeatherMap.Observingconditions')                                       # load driver
                    self.connected = True                                                                                   # set connected
                    self.ascom.connected = True                                                                             # enables data connection
                except Exception as e:                                                                                      # general exception
                    self.messageQueue.put('Driver COM Error in dispatchWeather')                                            # write to gui
                    self.logger.error('run Weather    -> general exception in connectWeather: {0}'.format(e))               # write to log
                    self.connected = False                                                                                  # set to disconnected
                finally:                                                                                                    # continue to work
                    pass
            time.sleep(1)                                                                                                   # time loop
        self.ascom.Quit()
        pythoncom.CoUninitialize()                                                                                          # destruct driver
        self.terminate()                                                                                                    # shutdown task

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         #

    def setupDriver(self):                                                                                                  # ascom driver dialog
        try:
            self.ascom.SetupDialog()                                                                                        # run ascom setup Dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupWeather')                                                       # write to gui
            self.logger.error('setupDriverWeather -> general exception:{0}'.format(e))                                      # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # continue working
            return
