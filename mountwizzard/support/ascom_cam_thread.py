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
import time
import logging
import os
# library for fits file handling
import pyfits
# lib for numeric
import numpy
# import PyQt5
from PyQt5 import QtCore
# import .NET / COM Handling
from win32com.client.dynamic import Dispatch
import pythoncom


class Camera(QtCore.QThread):
    logger = logging.getLogger(__name__)
    def __init__(self):
        super().__init__()
        self.connected = 2
        self.chooser = None                                                                                                 # placeholder for ascom chooser object
        self.driverName = ''                                                                                                # driver object name
        self.ascom = None                                                                                                   # placeholder for ascom driver object

    def run(self):                                                                                                          # runnable for doing the work
        pythoncom.CoInitialize()                                                                                            # needed for doing COm objects in threads
        self.connected = 0                                                                                                  # set connection flag for stick itself
        while True:                                                                                                         # main loop for stick thread
            self.signalStickConnected.emit(self.connected)                                                                  # send status to GUI
            if self.connected == 1:                                                                                         # differentiate between dome connected or not
                try:
                    pass
                except pythoncom.com_error as e:                                                                            # if error, than put it to queue
                    self.connected = False                                                                                  # if error occurs, set to disconnected
                    self.messageQueue.put('Driver COM Error in connectCamera')                                              # write to gui
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
                    self.messageQueue.put('Driver COM Error in dispatchCamera')                                             # write to gui
                    self.logger.error('run Camera     -> general exception in dispatchStick: {0}'.format(e))                # write to logger
                finally:                                                                                                    # still continua and try it again
                    pass                                                                                                    # needed for continue
            time.sleep(1)                                                                                                   # wait for the next cycle
        self.ascom.Quit()
        pythoncom.CoUninitialize()                                                                                          # needed for doing COm objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         #

    def take_image(self, exposure):
        pass

    def setupDriver(self):                                                                                                  #
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Camera'
            self.driverName = self.chooser.Choose(self.driverName)
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupCamera')                                                        # write to gui
            self.logger.error('setupDriverCame-> general exception:{0}'.format(e))                                          # write to log
            if self.driverName == '':
                self.connected = 2
            else:
                self.connected = 0                                                                                          # run the driver setup dialog
        finally:                                                                                                            # continue to work
            pass                                                                                                            # python necessary

if __name__ == "__main__":

    cam = Camera()
    cam.driverName = 'QSICamera.CCDCamera'
    #cam.setupDriver()
    ascom = Dispatch(cam.driverName)
    print(cam.driverName)
    print('try to connect')
    ascom.Connected = True
    print('connected')
    print('description: ', ascom.Description)
    #print('interface version: ', ascom.InterfaceVersion)
    #print('fast readout ', ascom.CanFastReadout)
    print('cooler on: ', ascom.CoolerOn)
    print('cooler power: ',ascom.CoolerPower)
    print('ccdtemp: ', ascom.CCDTemperature)
    ascom.StartExposure(3, True)
    print('started exposure')
    while not ascom.ImageReady:
        time.sleep(0.1)
        print('camera state: ', ascom.CameraState)
        #print('percentage: ', ascom.PercentCompleted)
    print('download image')
    image = numpy.array(ascom.ImageArray, dtype=numpy.int16).T
    print('image downloaded')
    #fitsFileHandle = pyfits.open('test.fit', mode='update')
    if os.path.isfile('C:/Users/mw/Projects/mountwizzard/mountwizzard/testimages/test.fit'):
        os.remove('C:/Users/mw/Projects/mountwizzard/mountwizzard/testimages/test.fit')
    pyfits.writeto('C:/Users/mw/Projects/mountwizzard/mountwizzard/testimages/test.fit', image)
    print('image saved to file')
    #fitsFileHandle.flush()  # write all to disk
    #fitsFileHandle.close()  # close FIT file


