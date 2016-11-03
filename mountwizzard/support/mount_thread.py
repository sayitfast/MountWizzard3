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
from win32com.client import Dispatch
import pythoncom
# for coordinate transformation
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, Angle
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
        self.stat = 0                                                                                                       # mount status (from Gstat command(
        self.location = EarthLocation(lat=0, lon=0, height=0, ellipsoid='WGS84')                                            # site location for astropy
        self.site_lat = 49                                                                                                  # site lat
        self.site_lon = 0                                                                                                   # site lon
        self.site_height = 0                                                                                                # site height
        self.jd = 2451544.5                                                                                                 # julian date
        self.slew = 0                                                                                                       # slewing status
        self.pierside = 0                                                                                                   # side of pier (E/W)
        self.transform = None                                                                                               # ascom novas library entry point
        self.ascom = None                                                                                                   # ascom mount driver entry point
        self.mountAlignRMSsum = 0                                                                                           # variable for counting RMS over stars
        self.mountAlignmentPoints = []                                                                                      # alignment point for modeling
        self.mountAlignNumberStars = 0                                                                                      # number of stars
        self.counter = 0                                                                                                    # counter im main loop
        self.connected = False                                                                                              # connection status

    def run(self):                                                                                                          # runnable of the thread
        pythoncom.CoInitialize()                                                                                            # needed for doing COM objects in threads
        try:                                                                                                                # start accessing a com object
            self.transform = Dispatch('ASCOM.Astrometry.Transform.Transform')                                               # novas library for Jnow J2000 conversion through ASCOM
        except Exception as e:                                                                                              # exception handling
            self.messageQueue.put('Error load ASCOM transform Driver: {0}'.format(e))                                       # write to gui
            self.logger.error('run -> load ASCOM transform error:{0}'.format(e))                                            # write logfile
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
                        self.getAlignmentModel()                                                                            # running the appropriate method
                    elif data == 'ClearAlign':                                                                              #
                        self.sendCommand('delalig')                                                                         #
                    elif data == 'RunTargetRMSAlignment':
                        self.runTargetRMSAlignment()
                    elif data == 'BackupModel':
                        self.backupModel()
                    elif data == 'RestoreModel':
                        self.restoreModel()
                    elif data == 'LoadSimpleModel':
                        self.loadSimpleModel()
                    elif data == 'SaveSimpleModel':
                        self.saveSimpleModel()
                    elif data == 'SetRefractionParameter':
                        self.setRefractionParameter()
                    elif data == 'FLIP':
                        self.flipMount()
                    else:
                        self.sendCommand(data)                                                                              # doing the command directly to mount (no method necessary)
                else:                                                                                                       # if not connected, the we should do this
                    if self.counter == 0:                                                                                   # jobs once done at the beginning
                        self.getStatusOnce()                                                                                # task once
                    if self.counter % 2 == 0:                                                                               # all tasks with 200 ms
                        self.getStatusFast()                                                                                # polling the mount status Ginfo
                    if self.counter % 20 == 0:                                                                              # all tasks with 3 s
                        self.getStatusMedium()                                                                              # polling the mount
                    if self.counter % 300 == 0:                                                                             # all task with 1 minute
                        self.getStatusSlow()                                                                                # slow ones
                time.sleep(0.2)                                                                                             # time base is 200 ms
                self.counter += 1                                                                                           # increasing counter for selection
            else:                                                                                                           # when not connected try to connect
                try:
                    self.ascom = Dispatch('ASCOM.FrejvallGM.Telescope')                                                     # select win32 driver
                    self.ascom.connected = True                                                                             # connect to mount
                    self.connected = True                                                                                   # setting connection status from driver
                    self.messageQueue.put('Mount Driver Connected')                                                         # status to gui
                except pythoncom.com_error as e:                                                                            # error handling
                    self.messageQueue.put('Driver COM Error in dispatchMount: {0}'.format(e.args[2][0]))                    # gui
                    self.logger.error('run-> Driver COM Error in dispatchMount: {0}'.format(e))                             # logfile
                    self.connected = False                                                                                  # after error connection might be broken
                except Exception as e:                                                                                      # error handling part 2
                    self.messageQueue.put('Driver COM Error in dispatchMount: {0}'.format(e.args[2][0]))                    # to gui
                    self.logger.error('run-> Driver COM Error in dispatchMount: {0}'.format(e))                             # to logger
                    self.connected = False                                                                                  # connection broken
                finally:                                                                                                    # we don't stop, but try it again
                    time.sleep(1)                                                                                           # try it every second, not more
        pythoncom.CoUninitialize()                                                                                          # needed for doing COM objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         # wait for stop of thread

    def sendCommand(self, command):                                                                                         # core routine for sending commands to mount
        reply = ''                                                                                                          # reply is empty
        try:                                                                                                                # all with error handling
            if command in ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']:                                     # these are the commands, which do not expect a return value
                self.ascom.CommandBlind(command)                                                                            # than do blind command
            else:                                                                                                           #
                reply = self.ascom.CommandString(command)                                                                   # with return value do regular command
        except pythoncom.com_error as e:                                                                                    # error handling
            self.messageQueue.put('Driver COM Error in sendCommand: {0} reply: {1} error :{2}'.format(command, reply, e))   # gui
            self.logger.error('sendCommand -> error: {0}'.format(e))                                                        # logger
            self.connected = False                                                                                          # in case of error, the connection might be broken
        finally:                                                                                                            # we don't stop
            if len(reply) > 0:                                                                                              # if there is a reply
                return reply.rstrip('#').strip()                                                                            # return the value
            else:                                                                                                           #
                return ''                                                                                                   # nothing

    def flipMount(self):                                                                                                    # doing the flip of the mount
        reply = self.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':                                                                                                    # error handling if not successful
            self.messageQueue.put('Flip Mount could not be executed !')                                                     # write to gui
            self.logger.debug('flipMount-> error: {0}'.format(reply))                                                       # write to logger

    def transformCelestialHorizontal(self, ha, dec):
        a = SkyCoord(ra=ha, dec=dec, unit=(u.hour, u.degree), location=self.location, frame='fk5')
        b = a.transform_to('altaz')
        return float(b.az.to_string(unit='deg', decimal=True)), float(b.alt.to_string(unit='deg', decimal=True))

    def getAlignmentModel(self):
        self.ui.btn_getActualModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        self.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'delete'})
        self.mountAlignRMSsum = 0
        self.mountAlignmentPoints = []
        self.mountAlignNumberStars = int(self.ascom.CommandString('getalst').rstrip('#').strip())
        if self.mountAlignNumberStars == 0:
            self.ui.btn_getActualModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            return
        for i in range(1, self.mountAlignNumberStars+1):
            try:
                reply = self.ascom.CommandString('getalp{0:d}'.format(i)).split(',')
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
            a = SkyCoord(ra=Angle(ha, unit=u.hour), dec=Angle(dec, unit=u.degree), location=self.location, frame='fk5')
            b = a.transform_to('altaz')
            az = int(float(b.az.to_string(unit='deg', decimal=True)))
            alt = int(float(b.alt.to_string(unit='deg', decimal=True)))
            self.mountDataQueue.put({'Name': 'ModelStarError', 'Value': '#{0:02d} Az: {1:3d} Alt: {2:2d} Err: {3:4.1f}\x22 EA: {4:3s}\xb0\n'.format(i, az, alt, errorRMS, errorAngle)})
        self.mountDataQueue.put({'Name': 'NumberAlignmentStars', 'Value': self.mountAlignNumberStars})
        self.mountDataQueue.put({'Name': 'ModelRMSError', 'Value': '{0:3.1f}'.format(math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars))})
        self.ui.btn_getActualModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def runTargetRMSAlignment(self):
        self.ui.btn_runTargetRMSAlignment.setStyleSheet('background-color: rgb(42, 130, 218)')
        self.mountAlignRMSsum = 999.9
        self.mountAlignNumberStars = 4
        while math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars) > float(self.ui.targetRMS.value()) and self.mountAlignNumberStars > 3:
            a = sorted(self.mountAlignmentPoints, key=itemgetter(1), reverse=True)                                          # index 0 ist the worst star
            try:                                                                                                            # delete the worst star
                self.ascom.CommandString('delalst{0:d}'.format(a[0][0]))
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
            self.getAlignmentModel()
        self.ui.btn_runTargetRMSAlignment.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def backupModel(self):
        self.ui.btn_backupModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        self.sendCommand('modeldel0BACKUP')
        reply = self.sendCommand('modelsv0BACKUP')
        if reply == '1':
            self.messageQueue.put('Actual Model saved as BACKUP')
        self.logger.debug('backupModel -> Reply: {0}'.format(reply))
        self.ui.btn_backupModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def restoreModel(self):
        self.ui.btn_restoreModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        reply = self.sendCommand('modelld0BACKUP')
        if reply == '1':
            self.messageQueue.put('Actual Model loaded from BACKUP')
        else:
            self.messageQueue.put('There is no model named BACKUP or error while loading')
        self.logger.debug('restoreModel -> Reply: {0}'.format(reply))
        self.ui.btn_restoreModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def saveSimpleModel(self):
        self.ui.btn_saveSimpleModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        self.sendCommand('modeldel0SIMPLE')
        reply = self.sendCommand('modelsv0SIMPLE')
        if reply == '1':
            self.messageQueue.put('Actual Model save as SIMPLE')
        self.logger.debug('saveSimpleModel -> Reply: {0}'.format(reply))
        self.ui.btn_saveSimpleModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def loadSimpleModel(self):
        self.ui.btn_loadSimpleModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        reply = self.sendCommand('modelld0SIMPLE')
        if reply == '1':
            self.messageQueue.put('Actual Model loaded from SIMPLE')
        else:
            self.messageQueue.put('There is no model named SIMPLE or error while loading')
        self.logger.debug('loadSimpleModel -> Reply: {0}'.format(reply))
        self.ui.btn_loadSimpleModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def setRefractionParameter(self):
        if self.ui.le_pressureStick.text() != '':                       # value must be there
            self.sendCommand('SRPRS{0:04.1f}'.format(float(self.ui.le_pressureStick.text())))
            if float(self.ui.le_temperatureStick.text()) > 0:
                self.sendCommand('SRTMP+{0:03.1f}'.format(float(self.ui.le_temperatureStick.text())))
            else:
                self.sendCommand('SRTMP-{0:3.1f}'.format(-float(self.ui.le_temperatureStick.text())))
            self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.sendCommand('GRTMP')})
            self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.sendCommand('GRPRS')})

    def getStatusFast(self):                                                                                                # fast status item like pointing
        reply = self.sendCommand('Ginfo')                                                                                   # use command "Ginfo" for fast topics
        if reply:                                                                                                           # if reply is there
            ra, dec, self.pierside, az, alt, self.jd, stat, self.slew = reply.rstrip('#').strip().split(',')                # split the response to its parts
            # self.jd = self.jd.rstrip('#')                                                                                 # was necessary for 2.14.8 beta due to bug
            self.az = float(az)                                                                                             # same to azimuth
            self.alt = float(alt)                                                                                           # and altitude
            self.stat = int(stat)                                                                                           # status should be int for referencing list
            self.transform.Refraction = False
            self.transform.SiteElevation = self.location.height.value
            self.transform.SiteLatitude = self.location.latitude.value
            self.transform.SiteLongitude = self.location.longitude.value
            if len(self.ui.le_refractionTemperature.text()) > 0:
                self.transform.SiteTemperature = float(self.ui.le_refractionTemperature.text())
            else:
                self.transform.SiteTemperature = 20.0
            self.transform.SetTopocentric(float(ra), float(dec))
            self.ra = self.transform.RAJ2000                                                                                # convert to float decimal
            self.dec = self.transform.DecJ2000                                                                              # convert to float decimal
            show = SkyCoord(ra=self.ra * u.hour, dec=self.dec * u.degree)
            dec_show = show.dec.to_string(sep='::', precision=0, alwayssign=True, unit=u.degree)                            # format dec string
            ra_show = show.ra.to_string(sep='::', precision=0, unit=u.hour)                                                 # format ra string
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

    def getStatusMedium(self):                                                                                              # medium status items like refraction
        if self.ui.checkAutoRefraction.isChecked():                                                                         # check if autorefraction is set
            if self.stat != 0:                                                                                              # if no tracking, than autorefraction is good
                self.setRefractionParameter()                                                                               # transfer refraction from to mount
            else:                                                                                                           #
                success, message = self.SGPro.SgGetDeviceStatus('Camera')                                                   # getting the Camera status
                if success and message in ['IDLE', 'DOWNLOADING']:                                                          # if tracking, when camera is idle or downloading
                    self.setRefractionParameter()                                                                           # transfer refraction to mount
                else:                                                                                                       # otherwise
                    self.logger.debug('getStatusMedium -> no autorefraction: {0}'.format(message))                          # no autorefraction is possible

    def getStatusSlow(self):                                                                                                # slow update item like temps
        self.mountDataQueue.put({'Name': 'GetTimeToTrackingLimit', 'Value': self.sendCommand('Gmte')})                      # Flip time
        self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.sendCommand('GRTMP')})                   # refraction temp out of mount
        self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.sendCommand('GRPRS')})                      # refraction pressure out of mount
        self.mountDataQueue.put({'Name': 'GetTelescopeTempRA', 'Value': self.sendCommand('GTMP1')})                         # temp of RA motor
        self.mountDataQueue.put({'Name': 'GetTelescopeTempDEC', 'Value': self.sendCommand('GTMP2')})                        # temp of dec motor
        self.mountDataQueue.put({'Name': 'GetSlewRate', 'Value': self.sendCommand('GMs')})                                  # get actual slew rate
        self.mountDataQueue.put({'Name': 'GetRefractionStatus', 'Value': self.sendCommand('GREF')})                         #

    def getStatusOnce(self):                                                                                                # one time updates for settings
        self.site_height = self.sendCommand('Gev')                                                                          # site height
        lon1 = self.sendCommand('Gg')                                                                                       # get site lon
        if lon1[0] == '-':                                                                                                  # due to compatibility to LX200 protocol east is negative
            self.site_lon = lon1.replace('-', '+')                                                                          # change that
        else:
            self.site_lon = lon1.replace('+', '-')                                                                          # and vice versa
        self.site_lat = self.sendCommand('Gt')                                                                              # get site latitude
        self.location = EarthLocation(lat=self.site_lat, lon=self.site_lon, height=float(self.site_height), ellipsoid='WGS84')  # calculation location for transformations once
        self.mountDataQueue.put({'Name': 'GetCurrentSiteElevation', 'Value': self.site_height})                             # write data to GUI
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLongitude', 'Value': lon1})                                         #
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLatitude', 'Value': self.site_lat})                                 #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitHigh', 'Value': self.sendCommand('Gh')})                    #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitLow', 'Value': self.sendCommand('Go')})                     #
        self.mountDataQueue.put({'Name': 'GetUnattendedFlip', 'Value': self.sendCommand('Guaf')})                           #
        self.mountDataQueue.put({'Name': 'GetDualAxisTracking', 'Value': self.sendCommand('Gdat')})                         #
        self.mountDataQueue.put({'Name': 'GetFirmwareDate', 'Value': self.sendCommand('GVD')})                              #
        self.mountDataQueue.put({'Name': 'GetFirmwareNumber', 'Value': self.sendCommand('GVN')})                            #
        self.mountDataQueue.put({'Name': 'GetFirmwareProductName', 'Value': self.sendCommand('GVP')})                       #
        self.mountDataQueue.put({'Name': 'GetFirmwareTime', 'Value': self.sendCommand('GVT')})                              #
        self.mountDataQueue.put({'Name': 'GetHardwareVersion', 'Value': self.sendCommand('GVZ')})                           #

    def setupDriver(self):
        try:
            self.ascom.SetupDialog()                                                                                        # rise ascom driver setting dialog
#            self.chooser.DeviceType = 'ObservingConditions'
#            self.chooser.Choose('ASCOM.FrejvallGM.Telescope')
        except pythoncom.com_error as e:                                                                                    # error handling, happens sometimes
            self.connected = False                                                                                          # set to disconnected -> reconnect necessary
            self.messageQueue.put('Driver Exception in setupDriverMount: {0}'.format(e))                                    # debug output to Gui
            self.logger.debug('setupDriver -> win32com error: {0}'.format(e))                                               # write to log
        except Exception as e:                                                                                              # general exception
            self.messageQueue.put('Driver Exception in setupMount: {0}'.format(e))                                          # write to gui
            self.logger.error('setupDriver -> general exception:{0}'.format(e))                                             # write to log
            self.connected = False                                                                                          # set to disconnected
        finally:                                                                                                            # won't stop the program, continue
            return
