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
import indi.indi_xml as indiXML


class INDIDome:
    logger = logging.getLogger(__name__)
    START_DOME_TIMEOUT = 3

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.application = dict()
        self.application['Available'] = False
        self.application['Name'] = 'INDI Dome'
        self.application['Status'] = ''

    def start(self):
        self.connect()

    def stop(self):
        pass

    def connect(self):
        timeStart = time.time()
        while True:
            if time.time() - timeStart > self.START_DOME_TIMEOUT:
                self.app.messageQueue.put('Timeout connect environment device\n')
                break
            if self.app.workerINDI.domeDevice:
                if 'CONNECTION' in self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]:
                    break
            time.sleep(0.1)
        if self.app.workerINDI.domeDevice != '':
            if self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]['CONNECTION']['CONNECT'] == 'Off':
                self.app.INDICommandQueue.put(indiXML.newSwitchVector([indiXML.oneSwitch('On', indi_attr={'name': 'CONNECT'})], indi_attr={'name': 'CONNECTION', 'device': self.app.workerINDI.domeDevice}))

    def slewToAzimuth(self, azimuth):
        self.app.INDICommandQueue.put(
            indiXML.newNumberVector([indiXML.oneNumber(azimuth, indi_attr={'name': 'DOME_ABSOLUTE_POSITION'})],
                                    indi_attr={'name': 'ABS_DOME_POSITION', 'device': self.app.workerINDI.domeDevice}))

    def getStatus(self):
        if self.app.workerINDI.domeDevice != '':
            self.application['Available'] = True
        else:
            self.application['Available'] = False
        self.app.sharedDomeDataLock.lockForWrite()
        if self.app.workerINDI.domeDevice in self.app.workerINDI.data['Device']:
            self.application['Status'] = 'OK'
            self.data['Connected'] = self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]['CONNECTION']['CONNECT'] == 'On'
        else:
            self.data['Connected'] = False
            self.application['Status'] = 'ERROR'
        self.app.sharedDomeDataLock.unlock()

    def getData(self):
        # check if client has device found
        if self.app.workerINDI.domeDevice != '':
            # and device is connected
            if self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]['CONNECTION']['CONNECT'] == 'On':
                # than get the data
                self.app.sharedDomeDataLock.lockForWrite()
                self.data['Azimuth'] = float(self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]['ABS_DOME_POSITION']['DOME_ABSOLUTE_POSITION'])
                if self.app.workerINDI.data['Device'][self.app.workerINDI.domeDevice]['DOME_MOTION']['state'] == 'Busy':
                    self.data['Slewing'] = True
                else:
                    if self.data['Slewing']:
                        self.main.signalSlewFinished.emit()
                        self.app.audioCommandQueue.put('DomeSlew')
                    self.data['Slewing'] = False
                self.app.sharedDomeDataLock.unlock()
