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
import time
import math
# import PyQT5 for threading purpose
from PyQt5 import QtCore
from win32com.client.dynamic import Dispatch
import pythoncom
# for the sorting
from operator import itemgetter
# testing refraction capability
from support.sgpro import SGPro


class Mount(QtCore.QThread):
    logger = logging.getLogger('Mount')                                                                                     # enable logging
    signalMountConnected = QtCore.pyqtSignal([bool], name='mountConnected')                                                 # signal for connection status
    signalMountAzAltPointer = QtCore.pyqtSignal([float, float], name='mountAzAltPointer')

    def __init__(self, ui, messageQueue, commandQueue, mountDataQueue):
        super().__init__()                                                                                                  # init of the class parent with super
        self.ui = ui                                                                                                        # accessing ui object from mount class
        self.commandQueue = commandQueue                                                                                    # getting mount commands from gui
        self.mountDataQueue = mountDataQueue                                                                                # moving data to gui
        self.messageQueue = messageQueue                                                                                    # message to Gui for errors
        self.SGPro = SGPro()                                                                                                # class SGPro for getting the Cam status
        self.statusReference = {'0': 'Tracking',
                                '1': 'Stopped after STOP',
                                '2': 'Slewing to park position',
                                '3': 'Unparking',
                                '4': 'Slewing to home position',
                                '5': 'Parked',
                                '6': 'Slewing or going to stop',
                                '7': 'Tracking Off no move',
                                '8': 'Motor low temperature',
                                '9': 'Tracking outside limits',
                                '10': 'Following Satellite',
                                '11': 'User OK Needed',
                                '98': 'Unknown Status',
                                '99': 'Error'
                                }                                                                                           # conversion list Gstat to text
        self.ra = 0                                                                                                         # mount reported ra to J2000 converted
        self.dec = 0                                                                                                        # mount reported dec to J2000 converted
        self.az = 0                                                                                                         # mount reported azimuth
        self.alt = 0                                                                                                        # mount reported altitude
        self.stat = 0                                                                                                       # mount status (from Gstat command)
        self.slewing = False                                                                                                # from *D' command
        self.site_lat = 49                                                                                                  # site lat
        self.site_lon = 0                                                                                                   # site lon
        self.site_height = 0                                                                                                # site height
        self.jd = 2451544.5                                                                                                 # julian date
        self.pierside = 0                                                                                                   # side of pier (E/W)
        self.transform = None                                                                                               # ascom novas library entry point
        self.ascom = None                                                                                                   # ascom mount driver entry point
        self.mountAlignRMSsum = 0                                                                                           # variable for counting RMS over stars
        self.mountAlignmentPoints = []                                                                                      # alignment point for modeling
        self.mountAlignNumberStars = 0                                                                                      # number of stars
        self.counter = 0                                                                                                    # counter im main loop
        self.connected = False                                                                                              # connection status
        self.driverName = 'ASCOM.FrejvallGM.Telescope'
        self.chooser = None
        self.driver_real = False
        self.value_azimuth = 0.0
        self.value_altitude = 0.0

    def run(self):                                                                                                          # runnable of the thread
        pythoncom.CoInitialize()                                                                                            # needed for doing COM objects in threads
        try:                                                                                                                # start accessing a com object
            self.transform = Dispatch('ASCOM.Astrometry.Transform.Transform')                                               # novas library for Jnow J2000 conversion through ASCOM
        except Exception as e:                                                                                              # exception handling
            self.messageQueue.put('Error loading ASCOM transform Driver')                                                   # write to gui
            self.logger.error('run Mount      -> loading ASCOM transform error:{0}'.format(e))                              # write logfile
        finally:                                                                                                            # we don't stop on error the wizzard
            pass                                                                                                            # python specific
        self.connected = False                                                                                              # init of connection status
        self.counter = 0                                                                                                    # init count for managing different cycle times
        while True:                                                                                                         # main loop in thread
            self.signalMountConnected.emit(self.connected)                                                                  # sending the connection status
            if self.connected:                                                                                              # when connected, starting the work
                if not self.commandQueue.empty():                                                                           # checking if in queue is something to do
                    data = self.commandQueue.get()                                                                          # if yes, getting the work command
                    if data == 'GetAlignmentModel':                                                                         # checking which command was sent
                        self.ui.btn_getActualModel.setStyleSheet('background-color: rgb(42, 130, 218)')
                        self.getAlignmentModel(self.driver_real)                                                            # running the appropriate method
                        self.ui.btn_getActualModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
                    elif data == 'ClearAlign':                                                                              #
                        self.sendCommand('delalig', self.driver_real)                                                       #
                    elif data == 'RunTargetRMSAlignment':
                        self.ui.btn_runTargetRMSAlignment.setStyleSheet('background-color: rgb(42, 130, 218)')
                        self.runTargetRMSAlignment(self.driver_real)
                        self.ui.btn_runTargetRMSAlignment.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
                    elif data == 'BackupModel':
                        self.ui.btn_backupModel.setStyleSheet('background-color: rgb(42, 130, 218)')  # button blue
                        self.backupModel(self.driver_real)
                        self.ui.btn_backupModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')  # button to default back
                    elif data == 'RestoreModel':
                        self.ui.btn_restoreModel.setStyleSheet('background-color: rgb(42, 130, 218)')
                        self.restoreModel(self.driver_real)
                        self.ui.btn_restoreModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
                    elif data == 'LoadSimpleModel':
                        self.ui.btn_loadSimpleModel.setStyleSheet('background-color: rgb(42, 130, 218)')
                        self.loadSimpleModel(self.driver_real)
                        self.ui.btn_loadSimpleModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
                    elif data == 'SaveSimpleModel':
                        self.ui.btn_saveSimpleModel.setStyleSheet('background-color: rgb(42, 130, 218)')
                        self.saveSimpleModel(self.driver_real)
                        self.ui.btn_saveSimpleModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
                    elif data == 'SetRefractionParameter':
                        self.setRefractionParameter(self.driver_real)
                    elif data == 'FLIP':
                        self.flipMount(self.driver_real)
                    else:
                        self.sendCommand(data, self.driver_real)                                                            # doing the command directly to mount (no method necessary)
                else:                                                                                                       # if not connected, the we should do this
                    if self.counter == 0:                                                                                   # jobs once done at the beginning
                        self.getStatusOnce(self.driver_real)                                                                # task once
                    if self.counter % 2 == 0:                                                                               # all tasks with 200 ms
                        self.getStatusFast(self.driver_real)                                                                # polling the mount status Ginfo
                    if self.counter % 20 == 0:                                                                              # all tasks with 3 s
                        self.getStatusMedium(self.driver_real)                                                              # polling the mount
                    if self.counter % 300 == 0:                                                                             # all task with 1 minute
                        self.getStatusSlow(self.driver_real)                                                                # slow ones
                time.sleep(0.2)                                                                                             # time base is 200 ms
                self.counter += 1                                                                                           # increasing counter for selection
            else:                                                                                                           # when not connected try to connect
                try:
                    self.ascom = Dispatch(self.driverName)                                                                  # select win32 driver
                    self.ascom.connected = True                                                                             # connect to mount
                    self.connected = True                                                                                   # setting connection status from driver
                except Exception as e:                                                                                      # error handling
                    if self.driverName != '':
                        self.logger.error('run Mount      -> Driver COM Error in dispatchMount: {0}'.format(e))             # to logger
                    self.connected = False                                                                                  # connection broken
                finally:                                                                                                    # we don't stop, but try it again
                    time.sleep(1)                                                                                           # try it every second, not more
        self.ascom.Quit()
        self.transform.Quit()
        pythoncom.CoUninitialize()                                                                                          # needed for doing COM objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         # wait for stop of thread

    def sendCommand(self, command, real):                                                                                   # core routine for sending commands to mount
        reply = ''                                                                                                          # reply is empty
        if real:
            try:                                                                                                            # all with error handling
                if command in ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']:                                 # these are the commands, which do not expect a return value
                    self.ascom.CommandBlind(command)                                                                        # than do blind command
                else:                                                                                                       #
                    reply = self.ascom.CommandString(command)                                                               # with return value do regular command
            except pythoncom.com_error as e:                                                                                # error handling
                self.messageQueue.put('Driver COM Error in sendCommand')                                                    # gui
                self.logger.error('sendCommand Mount -> error: {0} command:{1}  reply:{2} '.format(e, command, reply))      # logger
                self.connected = False                                                                                      # in case of error, the connection might be broken
            finally:                                                                                                        # we don't stop
                if len(reply) > 0:                                                                                          # if there is a reply
                    return reply.rstrip('#').strip()                                                                        # return the value
                else:                                                                                                       #
                    return ''                                                                                               # nothing
        else:
            if command == 'Gev':
                return str(self.ascom.SiteElevation)
            elif command == 'Gt':
                h, m, s, sign = self.decimalToDegree(self.ascom.SiteLatitude)
                return '{0}{1:02}:{2:02}:{3:02}'.format(sign, h, m, s)
            elif command == 'Gg':
                h, m, s, sign = self.decimalToDegree(self.ascom.SiteLongitude)
                return '{0}{1:02}:{2:02}:{3:02}'.format(sign, h, m, s)
            elif command.startswith('Sz'):
                self.value_azimuth = float(command[2:5])
            elif command.startswith('Sa'):
                self.value_altitude = float(command[2:5])
            elif command == 'MS':
                self.ascom.Tracking = False
                self.ascom.SlewToAltAzAsync(self.value_azimuth, self.value_altitude)
                self.ascom.Tracking = True
            elif command == 'MA':
                self.ascom.Tracking = False
                self.ascom.SlewToAltAzAsync(self.value_azimuth, self.value_altitude)
                self.ascom.Tracking = False
            elif command == 'Ginfo':
                ra = self.ascom.RightAscension
                dec = self.ascom.Declination
                az = self.ascom.Azimuth
                alt = self.ascom.Altitude
                if self.ascom.Slewing:
                    stat = 6
                else:
                    if self.ascom.Tracking:
                        stat = 0
                    else:
                        stat = 7
                jd = self.ascom.SiderealTime
                pierside = self.ascom.SideOfPier
                if self.ascom.Slewing:
                    slew = 1
                else:
                    slew = 0
                return '{0},{1},{2},{3},{4},{5},{6},{7}#'.format(ra, dec, pierside, az, alt, jd, stat, slew)
            elif command == 'PO':
                self.ascom.Unpark()
            elif command == 'hP':
                self.ascom.Park()
            elif command == 'AP':
                self.ascom.Tracking = True
            elif command == 'RT9':
                self.ascom.Tracking = False
            else:
                return ''

    def flipMount(self, real):                                                                                              # doing the flip of the mount
        reply = self.sendCommand('FLIP', real).rstrip('#').strip()
        if reply == '0':                                                                                                    # error handling if not successful
            self.messageQueue.put('Flip Mount could not be executed !')                                                     # write to gui
            self.logger.debug('flipMount      -> error: {0}'.format(reply))                                                 # write to logger

    @staticmethod
    def degStringToDecimal(value, splitter=':'):
        sign = 1
        if '-' in value:
            value = value.replace('-', '')
            sign = -1
        elif '+' in value:
            value = value.replace('+', '')
        hour, minute, second = value.split(splitter)
        return (float(hour) + float(minute) / 60 + float(second) / 3600) * sign

    @staticmethod
    def decimalToDegree(value):
        if value >= 0:
            sign = '+'
        else:
            sign = '-'
        value = abs(value)
        hour = int(value)
        minute = int((value - hour) * 60)
        second = int(((value - hour) * 60 - minute) * 60)
        return hour, minute, second, sign

    def getAlignmentModel(self, real):
        self.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'delete'})
        self.mountAlignRMSsum = 0
        self.mountAlignmentPoints = []
        self.mountAlignNumberStars = int(self.sendCommand('getalst', real).rstrip('#').strip())
        if self.mountAlignNumberStars == 0:
            return
        for i in range(1, self.mountAlignNumberStars+1):
            try:
                reply = self.sendCommand('getalp{0:d}'.format(i), real).split(',')
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
                return 0, 0
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            errorRMS = float(reply[2].strip())
            errorAngle = reply[3].strip().rstrip('#')
            self.mountAlignRMSsum += errorRMS ** 2
            self.mountAlignmentPoints.append((i, errorRMS))
            dec = dec.replace('*', ':')
            dec_digit = self.degStringToDecimal(dec)
            ha_digit = self.degStringToDecimal(ha)
            self.transform.SetJ2000(ha_digit, dec_digit)
            az = int(float(self.transform.AzimuthTopocentric))
            alt = int(float(self.transform.ElevationTopocentric))
            self.mountDataQueue.put({'Name': 'ModelStarError', 'Value': '#{0:02d} Az: {1:3d} Alt: {2:2d} Err: {3:4.1f}\x22 EA: {4:3s}\xb0\n'.format(i, az, alt, errorRMS, errorAngle)})
        self.mountDataQueue.put({'Name': 'NumberAlignmentStars', 'Value': self.mountAlignNumberStars})
        self.mountDataQueue.put({'Name': 'ModelRMSError', 'Value': '{0:3.1f}'.format(math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars))})

    def runTargetRMSAlignment(self, real):
        self.mountAlignRMSsum = 999.9
        self.mountAlignNumberStars = 4
        while math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars) > float(self.ui.targetRMS.value()) and self.mountAlignNumberStars > 3:
            a = sorted(self.mountAlignmentPoints, key=itemgetter(1), reverse=True)                                          # index 0 ist the worst star
            try:                                                                                                            # delete the worst star
                self.sendCommand('delalst{0:d}'.format(a[0][0]), real)
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
            self.getAlignmentModel(real)

    def backupModel(self, real):
        self.sendCommand('modeldel0BACKUP', real)                                                                                 # send delete command store in hand controller
        reply = self.sendCommand('modelsv0BACKUP', real)                                                                          # send store command for hand controller
        if reply == '1':                                                                                                    # if stored, than OK
            self.messageQueue.put('Actual Model saved as BACKUP')                                                           # do message to gui
        self.logger.debug('backupModel    -> Reply: {0}'.format(reply))                                                     # log it

    def restoreModel(self, real):
        reply = self.sendCommand('modelld0BACKUP', real)
        if reply == '1':
            self.messageQueue.put('Actual Model loaded from BACKUP')
        else:
            self.messageQueue.put('There is no model named BACKUP or error while loading')
        self.logger.debug('restoreModel   -> Reply: {0}'.format(reply))

    def saveSimpleModel(self, real):
        self.sendCommand('modeldel0SIMPLE', real)
        reply = self.sendCommand('modelsv0SIMPLE', real)
        if reply == '1':
            self.messageQueue.put('Actual Model save as SIMPLE')
        self.logger.debug('saveSimpleModel -> Reply: {0}'.format(reply))

    def loadSimpleModel(self, real):
        reply = self.sendCommand('modelld0SIMPLE', real)
        if reply == '1':
            self.messageQueue.put('Actual Model loaded from SIMPLE')
        else:
            self.messageQueue.put('There is no model named SIMPLE or error while loading')
        self.logger.debug('loadSimpleModel -> Reply: {0}'.format(reply))

    def setRefractionParameter(self, real):
        if self.ui.le_pressureStick.text() != '':                                                                           # value must be there
            self.sendCommand('SRPRS{0:04.1f}'.format(float(self.ui.le_pressureStick.text())), real)
            if float(self.ui.le_temperatureStick.text()) > 0:
                self.sendCommand('SRTMP+{0:03.1f}'.format(float(self.ui.le_temperatureStick.text())), real)
            else:
                self.sendCommand('SRTMP-{0:3.1f}'.format(-float(self.ui.le_temperatureStick.text())), real)
            self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.sendCommand('GRTMP', real)})
            self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.sendCommand('GRPRS', real)})

    def getStatusFast(self, real):                                                                                          # fast status item like pointing
        reply = self.sendCommand('Ginfo', real)                                                                             # use command "Ginfo" for fast topics
        if reply:                                                                                                           # if reply is there
            ra, dec, self.pierside, az, alt, self.jd, stat, slew = reply.rstrip('#').strip().split(',')                     # split the response to its parts
            self.jd = self.jd.rstrip('#')                                                                                   # needed for 2.14.8 beta firmware
            self.az = float(az)                                                                                             # same to azimuth
            self.alt = float(alt)                                                                                           # and altitude
            self.stat = int(stat)                                                                                           # status should be int for referencing list
            self.slewing = (slew == '1')                                                                                    # set status slewing
            if len(self.ui.le_refractionTemperature.text()) > 0:                                                            # if refraction temp available, then set it to converter as well
                self.transform.SiteTemperature = float(self.ui.le_refractionTemperature.text())                             # exactly the numbers from mount
            else:                                                                                                           # otherwise
                self.transform.SiteTemperature = 20.0                                                                       # set it to 20 degree as default
            self.transform.SetTopocentric(float(ra), float(dec))                                                            # set Jnow data
            self.ra = self.transform.RAJ2000                                                                                # convert to float decimal
            self.dec = self.transform.DecJ2000                                                                              # convert to float decimal
            h, m, s, sign = self.decimalToDegree(self.ra)
            ra_show = '{0:02}:{1:02}:{2:02}'.format(h, m, s)
            h, m, s, sign = self.decimalToDegree(self.dec)
            dec_show = '{0}{1:02}:{2:02}:{3:02}'.format(sign, h, m, s)
            self.mountDataQueue.put({'Name': 'GetTelescopeDEC', 'Value': '{0}'.format(dec_show)})                           # put dec to gui
            self.mountDataQueue.put({'Name': 'GetTelescopeRA', 'Value': '{0}'.format(ra_show)})                             # put ra to gui
            self.mountDataQueue.put({'Name': 'GetTelescopeAltitude', 'Value': '{0:03.2f}'.format(self.alt)})                # Altitude
            self.mountDataQueue.put({'Name': 'GetTelescopeAzimuth', 'Value': '{0:03.2f}'.format(self.az)})                  # Azimuth
            self.mountDataQueue.put({'Name': 'GetMountStatus', 'Value': '{0}'.format(self.stat)})                           # Mount status -> slew to stop
            self.mountDataQueue.put({'Name': 'GetLocalTime', 'Value': '{0:6.6f}'.format(float(self.jd))})                   # Sideral time in julian format
            if str(self.pierside) == str('W'):                                                                              # pier side
                self.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'WEST'})                                  # Transfer to test in GUI
            else:                                                                                                           #
                self.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'EAST'})                                  # Transfer to Text for GUI
            self.signalMountAzAltPointer.emit(self.az, self.alt)                                                            # set azalt Pointer in diagrams to actual pos

    def getStatusMedium(self, real):                                                                                        # medium status items like refraction
        if self.ui.checkAutoRefraction.isChecked():                                                                         # check if autorefraction is set
            if self.stat != 0:                                                                                              # if no tracking, than autorefraction is good
                self.setRefractionParameter(real)                                                                           # transfer refraction from to mount
            else:                                                                                                           #
                success, message = self.SGPro.SgGetDeviceStatus('Camera')                                                   # getting the Camera status
                if success and message in ['IDLE', 'DOWNLOADING']:                                                          # if tracking, when camera is idle or downloading
                    self.setRefractionParameter(real)                                                                       # transfer refraction to mount
                else:                                                                                                       # otherwise
                    self.logger.debug('getStatusMedium -> no autorefraction: {0}'.format(message))                          # no autorefraction is possible

    def getStatusSlow(self, real):                                                                                          # slow update item like temps
        self.mountDataQueue.put({'Name': 'GetTimeToTrackingLimit', 'Value': self.sendCommand('Gmte', real)})                # Flip time
        self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.sendCommand('GRTMP', real)})             # refraction temp out of mount
        self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.sendCommand('GRPRS', real)})                # refraction pressure out of mount
        self.mountDataQueue.put({'Name': 'GetTelescopeTempRA', 'Value': self.sendCommand('GTMP1', real)})                   # temp of RA motor
        self.mountDataQueue.put({'Name': 'GetTelescopeTempDEC', 'Value': self.sendCommand('GTMP2', real)})                  # temp of dec motor
        self.mountDataQueue.put({'Name': 'GetSlewRate', 'Value': self.sendCommand('GMs', real)})                            # get actual slew rate
        self.mountDataQueue.put({'Name': 'GetRefractionStatus', 'Value': self.sendCommand('GREF', real)})                   #

    def getStatusOnce(self, real):                                                                                          # one time updates for settings
        self.site_height = self.sendCommand('Gev', real)                                                                    # site height
        lon1 = self.sendCommand('Gg', real)                                                                                 # get site lon
        if lon1[0] == '-':                                                                                                  # due to compatibility to LX200 protocol east is negative
            self.site_lon = lon1.replace('-', '+')                                                                          # change that
        else:
            self.site_lon = lon1.replace('+', '-')                                                                          # and vice versa
        self.site_lat = self.sendCommand('Gt', real)                                                                        # get site latitude
        self.transform.Refraction = False                                                                                   # set parameter for ascom nova library
        self.transform.SiteElevation = float(self.site_height)                                                              # height
        self.transform.SiteLatitude = self.degStringToDecimal(self.site_lat)                                                # site lat
        self.transform.SiteLongitude = self.degStringToDecimal(self.site_lon)                                               # site lon
        self.mountDataQueue.put({'Name': 'GetCurrentSiteElevation', 'Value': self.site_height})                             # write data to GUI
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLongitude', 'Value': lon1})                                         #
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLatitude', 'Value': self.site_lat})                                 #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitHigh', 'Value': self.sendCommand('Gh', real)})              #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitLow', 'Value': self.sendCommand('Go', real)})               #
        self.mountDataQueue.put({'Name': 'GetUnattendedFlip', 'Value': self.sendCommand('Guaf', real)})                     #
        self.mountDataQueue.put({'Name': 'GetDualAxisTracking', 'Value': self.sendCommand('Gdat', real)})                   #
        self.mountDataQueue.put({'Name': 'GetFirmwareDate', 'Value': self.sendCommand('GVD', real)})                        #
        self.mountDataQueue.put({'Name': 'GetFirmwareNumber', 'Value': self.sendCommand('GVN', real)})                      #
        self.mountDataQueue.put({'Name': 'GetFirmwareProductName', 'Value': self.sendCommand('GVP', real)})                 #
        self.mountDataQueue.put({'Name': 'GetFirmwareTime', 'Value': self.sendCommand('GVT', real)})                        #
        self.mountDataQueue.put({'Name': 'GetHardwareVersion', 'Value': self.sendCommand('GVZ', real)})                     #

    def setupDriver(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Telescope'
            self.driverName = self.chooser.Choose(self.driverName)
            if self.driverName == 'ASCOM.FrejvallGM.Telescope':
                self.driver_real = True
            else:
                self.driver_real = False
            self.connected = False                                                                                          # run the driver setup dialog
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupMount')                                                         # write to gui
            self.logger.error('setupDriver Mount -> general exception:{0}'.format(e))                                       # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # won't stop the program, continue
            return
