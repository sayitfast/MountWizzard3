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


class Weather(QtCore.QThread):
    logger = logging.getLogger('weather_thread:')                                                                           # get logger for  problems
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
                    self.messageQueue.put('Driver win32com error in connectWeather: {0}'.format(e.args[2][0]))              # write to gui
                    self.logger.error('run -> win32com error in connectWeather: {0}'.format(e))                             # write to log
            else:
                try:
                    self.ascom = Dispatch('ASCOM.OpenWeatherMap.Observingconditions')                                       # load driver
                    self.connected = True                                                                                   # set connected
                    self.messageQueue.put('Weather Driver Connected')                                                       # message to gui
                except pythoncom.com_error as e:                                                                            # win32com problem
                    self.messageQueue.put('Driver COM Error in dispatchWeather: {0}'.format(e.args[2][0]))                  # write to gui
                    self.logger.error('run ->  win32com error in connectWeather: {0}'.format(e))                            # write to log
                    self.connected = False                                                                                  # set to disconnected
                except Exception as e:                                                                                      # general exception
                    self.messageQueue.put('Driver COM Error in dispatchWeather: {0}'.format(e))                             # write to gui
                    self.logger.error('run -> general exception in connectWeather: {0}'.format(e))                          # write to log
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
            self.ascom.SetupDialog()                                                                                        # rund ascom setup Dialog
        except pythoncom.com_error as e:                                                                                    # exception handling
            self.messageQueue.put('Driver COM Error in setupWeather: {0}'.format(e.args[2][0]))                             # write to gui
            self.logger.error('setupDriver -> win32com error:{0}'.format(e))                                                # write to log
            self.connected = False                                                                                          # set to disconnected
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupWeather: {0}'.format(e))                                        # write to gui
            self.logger.error('setupDriver -> general exception:{0}'.format(e))                                             # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # continiou working
            return
