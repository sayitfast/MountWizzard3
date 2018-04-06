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
import PyQt5
import time
import indi.indi_xml as indiXML


class INDIEnvironment:
    logger = logging.getLogger(__name__)
    START_ENVIRONMENT_TIMEOUT = 4

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = 'INDI Environment'
        self.application['Status'] = ''

    def start(self):
        self.connect()

    def stop(self):
        pass

    def connect(self):
        timeStart = time.time()
        while True:
            if time.time() - timeStart > self.START_ENVIRONMENT_TIMEOUT:
                self.app.messageQueue.put('Timeout connect environment device\n')
                break
            if self.app.workerINDI.environmentDevice:
                if 'CONNECTION' in self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]:
                    break
            time.sleep(0.1)
        if self.app.workerINDI.environmentDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.environmentDevice}))

    def getStatus(self):
        if self.app.workerINDI.environmentDevice != '':
            self.application['Available'] = True
        else:
            self.application['Available'] = False
        self.app.sharedEnvironmentDataLock.lockForWrite()
        if self.app.workerINDI.environmentDevice in self.app.workerINDI.data['Device']:
            self.application['Status'] = 'OK'
            self.data['Connected'] = self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'On'
        else:
            self.data['Connected'] = False
            self.application['Status'] = 'ERROR'
        self.app.sharedEnvironmentDataLock.unlock()

    def getData(self):
        # check if client has device found
        if self.app.workerINDI.environmentDevice != '':
            # and device is connected
            if self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['CONNECTION']['CONNECT'] == 'On':
                # than get the data
                self.app.sharedEnvironmentDataLock.lockForWrite()
                self.data['DewPoint'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_DEWPOINT'])
                self.data['Temperature'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_TEMPERATURE'])
                self.data['Humidity'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_HUMIDITY'])
                self.data['Pressure'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.environmentDevice]['WEATHER_PARAMETERS']['WEATHER_BAROMETER'])
                self.app.sharedEnvironmentDataLock.unlock()
