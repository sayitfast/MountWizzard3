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
import time
import math
import threading
# import PyQT5 for threading purpose
from PyQt5 import QtCore
from win32com.client.dynamic import Dispatch
import pythoncom
# for the sorting
from operator import itemgetter
# testing refraction capability
from support.sgpro import SGPro


class Mount(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # enable logging
    signalMountConnected = QtCore.pyqtSignal([bool], name='mountConnected')                                                 # signal for connection status
    signalMountAzAltPointer = QtCore.pyqtSignal([float, float], name='mountAzAltPointer')
    signalMountTrackPreview = QtCore.pyqtSignal([bool], name='mountTrackPreview')

    BLUE = 'background-color: rgb(42, 130, 218)'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'

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
        self.raJnow = 0
        self.decJnow = 0
        self.az = 0                                                                                                         # mount reported azimuth
        self.alt = 0                                                                                                        # mount reported altitude
        self.stat = 0                                                                                                       # mount status (from Gstat command)
        self.slewing = False                                                                                                # from *D' command
        self.site_lat = 49                                                                                                  # site lat
        self.site_lon = 0                                                                                                   # site lon
        self.site_height = 0                                                                                                # site height
        self.jd = 2451544.5                                                                                                 # julian date
        self.sidereal_time = ''                                                                                             # local sidereal time
        self.pierside = 0                                                                                                   # side of pier (E/W)
        self.timeToFlip = '200'                                                                                             # minutes to flip
        self.refractionTemp = '20.0'                                                                                        # coordinate transformation need temp
        self.refractionPressure = '900.0'                                                                                   # and pressure
        self.transform = None                                                                                               # ascom novas library entry point
        self.ascom = None                                                                                                   # ascom mount driver entry point
        self.mountAlignRMSsum = 0                                                                                           # variable for counting RMS over stars
        self.mountAlignmentPoints = []                                                                                      # alignment point for modeling
        self.mountAlignNumberStars = 0                                                                                      # number of stars
        self.counter = 0                                                                                                    # counter im main loop
        self.connected = False                                                                                              # connection status
        self.driverName = 'ASCOM.FrejvallGM.Telescope'                                                                      # default driver name is Per's driver
        self.chooser = None                                                                                                 # object space
        self.driver_real = False                                                                                            # identifier, if data is real (or simulation
        self.value_azimuth = 0.0                                                                                            # object for Sz command
        self.value_altitude = 0.0                                                                                           # object for Sa command
        self.transformationLock = threading.Lock()                                                                          # locking object for single access to ascom transformation object
        self.sendCommandLock = threading.Lock()

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
                    command = self.commandQueue.get()                                                                       # if yes, getting the work command
                    if command == 'GetAlignmentModel':                                                                      # checking which command was sent
                        self.ui.btn_getActualModel.setStyleSheet(self.BLUE)
                        self.getAlignmentModel()                                                                            # running the appropriate method
                        self.ui.btn_getActualModel.setStyleSheet(self.DEFAULT)
                    elif command == 'ClearAlign':                                                                           #
                        self.sendCommand('delalig')                                                                         #
                    elif command == 'RunTargetRMSAlignment':
                        self.ui.btn_runTargetRMSAlignment.setStyleSheet(self.BLUE)
                        self.runTargetRMSAlignment()
                        self.ui.btn_runTargetRMSAlignment.setStyleSheet(self.DEFAULT)
                    elif command == 'DeleteWorstPoint':
                        self.ui.btn_deleteWorstPoint.setStyleSheet(self.BLUE)
                        self.deleteWorstPoint()
                        self.ui.btn_deleteWorstPoint.setStyleSheet(self.DEFAULT)
                    elif command == 'BackupModel':
                        self.ui.btn_backupModel.setStyleSheet(self.BLUE)                                                    # button blue
                        self.backupModel()
                        self.ui.btn_backupModel.setStyleSheet(self.DEFAULT)                                                 # button to default back
                    elif command == 'RestoreModel':
                        self.ui.btn_restoreModel.setStyleSheet(self.BLUE)
                        self.restoreModel()
                        self.ui.btn_restoreModel.setStyleSheet(self.DEFAULT)
                    elif command == 'LoadSimpleModel':
                        self.ui.btn_loadSimpleModel.setStyleSheet(self.BLUE)
                        self.loadSimpleModel()
                        self.ui.btn_loadSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SaveSimpleModel':
                        self.ui.btn_saveSimpleModel.setStyleSheet(self.BLUE)
                        self.saveSimpleModel()
                        self.ui.btn_saveSimpleModel.setStyleSheet(self.DEFAULT)
                    elif command == 'SetRefractionParameter':
                        self.setRefractionParameter()
                    elif command == 'FLIP':
                        self.flipMount()
                    else:
                        self.sendCommand(command)                                                                           # doing the command directly to mount (no method necessary)
                    self.commandQueue.task_done()
                else:                                                                                                       # if not connected, the we should do this
                    if self.counter == 0:                                                                                   # jobs once done at the beginning
                        self.getStatusOnce()                                                                                # task once
                    if self.counter % 2 == 0:                                                                               # all tasks with 400 ms
                        self.getStatusFast()                                                                                # polling the mount status Ginfo
                    if self.counter % 15 == 0:                                                                              # all tasks with 3 s
                        self.getStatusMedium()                                                                              # polling the mount
                    if self.counter % 150 == 0:                                                                             # all task with 30 seconds
                        self.getStatusSlow()                                                                                # slow ones
                time.sleep(0.2)                                                                                             # time base is 200 ms
                self.counter += 1                                                                                           # increasing counter for selection
            else:                                                                                                           # when not connected try to connect
                try:
                    self.ascom = Dispatch(self.driverName)                                                                  # select win32 driver
                    if self.driverName == 'ASCOM.FrejvallGM.Telescope':                                                     # identify real telescope against simulator
                        self.driver_real = True                                                                             # set it
                    else:
                        self.driver_real = False                                                                            # set it
                    self.ascom.connected = True                                                                             # connect to mount
                    self.connected = True                                                                                   # setting connection status from driver
                    self.counter = 0                                                                                        # whenever reconnect, then start from scratch
                except Exception as e:                                                                                      # error handling
                    if self.driverName != '':                                                                               # if driver is not empty, than error messages
                        self.logger.error('run Mount      -> Driver COM Error in dispatchMount: {0}'.format(e))             # to logger
                    self.connected = False                                                                                  # connection broken
                finally:                                                                                                    # we don't stop, but try it again
                    time.sleep(1)                                                                                           # try it every second, not more
        self.ascom.Quit()                                                                                                   # close ascom mount object
        self.transform.Quit()                                                                                               # close ascom novas transform object
        pythoncom.CoUninitialize()                                                                                          # needed for doing COM objects in threads
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()                                                                                                         # wait for stop of thread

    def sendCommand(self, command):                                                                                         # core routine for sending commands to mount
        reply = ''                                                                                                          # reply is empty
        self.sendCommandLock.acquire()
        if self.driver_real:
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
                    value = reply.rstrip('#').strip()                                                                       # return the value
                    if command == 'CMS':
                        self.logger.debug('sendCommand    -> Return Value Add Model Point: {0}'.format(reply))
                else:                                                                                                       #
                    value = ''                                                                                              # nothing
            self.sendCommandLock.release()
            return value
        else:                                                                                                               # from here we doing the simulation for 10micron mounts commands
            value = ''
            if command == 'Gev':                                                                                            # which are special, but only for the most important for MW to run
                value = str(self.ascom.SiteElevation)
            elif command == 'Gmte':
                value = '0125'
            elif command == 'Gt':
                value = self.decimalToDegree(self.ascom.SiteLatitude, True, False)
            elif command == 'Gg':
                lon = self.decimalToDegree(self.ascom.SiteLongitude, True, False)
                if lon[0] == '-':                                                                                           # due to compatibility to LX200 protocol east is negative
                    lon1 = lon.replace('-', '+')                                                                            # change that
                else:
                    lon1 = lon.replace('+', '-')                                                                            # and vice versa
                value = lon1
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
            elif command == 'GS':
                value = self.decimalToDegree(self.ascom.SiderealTime, False, False)
            elif command == 'GRTMP':
                value = '10.0'
            elif command == 'Ginfo':
                self.raJnow = self.ascom.RightAscension
                self.decJnow = self.ascom.Declination
                az = self.ascom.Azimuth
                alt = self.ascom.Altitude
                if self.ascom.Slewing:
                    stat = 6
                else:
                    if self.ascom.Tracking:
                        stat = 0
                    else:
                        stat = 7
                jd = self.ascom.SiderealTime + 2440587.5    # TODO: better time simulation
                if self.ascom.SideOfPier == 0:
                    pierside = 'E'
                else:
                    pierside = 'W'
                if self.ascom.Slewing:
                    slew = 1
                else:
                    slew = 0
                value = '{0},{1},{2},{3},{4},{5},{6},{7}#'.format(self.raJnow, self.decJnow, pierside, az, alt, jd, stat, slew)
            elif command == 'PO':
                self.ascom.Unpark()
            elif command == 'hP':
                self.ascom.Park()
            elif command == 'AP':
                self.ascom.Tracking = True
            elif command == 'RT9':
                self.ascom.Tracking = False
            elif command == 'GTMP1':
                value = '10.0'
            elif command == 'GTMP2':
                value = '10.0'
            elif command == 'GRPRS':
                value = '990.0'
            elif command == 'Guaf':
                value = '0'
            elif command == 'GMs':
                value = '15'
            elif command == 'Gh':
                value = '90'
            elif command == 'Go':
                value = '00'
            elif command == 'Gdat':
                value = '0'
            elif command in ['GVD', 'GVN', 'GVP', 'GVT', 'GVZ']:
                value = 'Simulation'
            elif command == 'GREF':
                value = '1'
            elif command == 'CMS':
                value = 'V'
            elif command == 'getalst':
                value = '0'
            else:
                pass
        self.sendCommandLock.release()
        return value

    def transformNovas(self, ra, dec, transform=1):                                                                         # wrapper for the novas ascom implementation
        self.transformationLock.acquire()                                                                                   # which is not threat safe, so we have to do this
        self.transform.SiteTemperature = float(self.refractionTemp)                                                         # needs refraction temp
        if transform == 1:                                                                                                  # 1 = J2000 -> alt/az
            if ra < 0:                                                                                                      # ra has to be between 0 and 23,99999
                ra += 24                                                                                                    #
            if ra >= 24:                                                                                                    # so set it right
                ra -= 24
            self.transform.SetJ2000(ra, dec)                                                                                # set J2000 ra, dec
            val1 = self.transform.AzimuthTopocentric                                                                        # convert az
            val2 = self.transform.ElevationTopocentric                                                                      # convert alt
        elif transform == 2:                                                                                                # 2 = Jnow -> J2000
            self.transform.SetTopocentric(ra, dec)                                                                          # set Jnow data
            val1 = self.transform.RAJ2000
            val2 = self.transform.DECJ2000
        elif transform == 3:                                                                                                # 3 = J2000 -> JNow
            self.transform.SetJ2000(ra, dec)                                                                                # set J2000 data
            val1 = self.transform.RATopocentric
            val2 = self.transform.DECTopocentric
        elif transform == 4:                                                                                                # 1 = JNow -> alt/az
            if ra < 0:                                                                                                      # ra has to be between 0 and 23,99999
                ra += 24                                                                                                    #
            if ra >= 24:                                                                                                    # so set it right
                ra -= 24
            self.transform.SetTopocentric(ra, dec)                                                                          # set JNow ra, dec
            val1 = self.transform.AzimuthTopocentric                                                                        # convert az
            val2 = self.transform.ElevationTopocentric                                                                      # convert alt
        else:
            val1 = ra
            val2 = dec
        self.transformationLock.release()                                                                                   # release locking for thread safety
        return val1, val2

    def flipMount(self):                                                                                                    # doing the flip of the mount
        reply = self.sendCommand('FLIP').rstrip('#').strip()
        if reply == '0':                                                                                                    # error handling if not successful
            self.messageQueue.put('Flip Mount could not be executed !')                                                     # write to gui
            self.logger.debug('flipMount      -> error: {0}'.format(reply))                                                 # write to logger

    def degStringToDecimal(self, value, splitter=':'):                                                                      # conversion between Strings formats and decimal representation
        sign = 1
        if '-' in value:
            value = value.replace('-', '')
            sign = -1
        elif '+' in value:
            value = value.replace('+', '')
        try:
            hour, minute, second = value.split(splitter)
        except Exception as e:
            self.logger.error('degStringToDeci-> error in conversion of:{0} with splitter:{1}, e:{2}'
                              .format(value, splitter, e))
            return 0
        return (float(hour) + float(minute) / 60 + float(second) / 3600) * sign

    @staticmethod
    def decimalToDegree(value, with_sign, with_decimal, spl=':'):                                                           # format decimal value to string in degree format
        if value >= 0:
            sign = '+'
        else:
            sign = '-'
        value = abs(value)
        hour = int(value)
        minute = int((value - hour) * 60)
        second = int(((value - hour) * 60 - minute) * 60)
        if with_decimal:
            second_dec = '.{0:1d}'.format(int((((value - hour) * 60 - minute) * 60 - second) * 10))
        else:
            second_dec = ''
        if with_sign:
            return '{0}{1:02d}{5}{2:02d}{5}{3:02d}{4}'.format(sign, hour, minute, second, second_dec, spl)
        else:
            return '{0:02d}{4}{1:02d}{4}{2:02d}{3}'.format(hour, minute, second, second_dec, spl)

    def getAlignmentModel(self):                                                                                            # download alignment model from mount
        self.mountDataQueue.put({'Name': 'ModelStarError', 'Value': 'delete'})                                              # clear the window in gui
        self.mountAlignRMSsum = 0                                                                                           # set RMS sum to 0 for calculation
        self.mountAlignmentPoints = []                                                                                      # clear the alignment points downloaded
        self.mountAlignNumberStars = int(self.sendCommand('getalst').rstrip('#').strip())                                   # get number of stars
        if self.mountAlignNumberStars == 0:                                                                                 # if no stars, finish
            return False
        for i in range(1, self.mountAlignNumberStars+1):                                                                    # otherwise download them step for step
            try:
                reply = self.sendCommand('getalp{0:d}'.format(i)).split(',')
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
                return False
            ha = reply[0].strip().split('.')[0]
            dec = reply[1].strip().split('.')[0]
            errorRMS = float(reply[2].strip())
            errorAngle = reply[3].strip().rstrip('#')
            self.mountAlignRMSsum += errorRMS ** 2
            self.mountAlignmentPoints.append((i, errorRMS))
            dec = dec.replace('*', ':')
            self.mountDataQueue.put({'Name': 'ModelStarError',
                                     'Value': '#{0:02d} HA: {1} DEC: {2} Err: {3:4.1f}\x22 EA: {4:3s}\xb0\n'
                                    .format(i, ha, dec, errorRMS, errorAngle)})
        self.mountDataQueue.put({'Name': 'NumberAlignmentStars', 'Value': self.mountAlignNumberStars})                      # write them to gui
        self.mountDataQueue.put({'Name': 'ModelRMSError', 'Value': '{0:3.1f}'
                                .format(math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars))})                    # set the error values in gui
        return True

    def runTargetRMSAlignment(self):
        if not self.getAlignmentModel():
            return
        self.mountAlignRMSsum = 999.9                                                                                       # set maximum
        self.mountAlignNumberStars = 4                                                                                      # set minimum for stars
        while math.sqrt(self.mountAlignRMSsum / self.mountAlignNumberStars) > float(self.ui.targetRMS.value()) \
                and self.mountAlignNumberStars > 3:
            a = sorted(self.mountAlignmentPoints, key=itemgetter(1), reverse=True)                                          # index 0 ist the worst star
            try:                                                                                                            # delete the worst star
                self.sendCommand('delalst{0:d}'.format(a[0][0]))
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
            self.getAlignmentModel()

    def deleteWorstPoint(self):
        if not self.getAlignmentModel():
            return
        self.mountAlignRMSsum = 999.9                                                                                       # set maximum
        self.mountAlignNumberStars = 4                                                                                      # set minimum for stars
        if self.mountAlignNumberStars > 3:
            a = sorted(self.mountAlignmentPoints, key=itemgetter(1), reverse=True)                                          # index 0 ist the worst star
            try:                                                                                                            # delete the worst star
                self.sendCommand('delalst{0:d}'.format(a[0][0]))
            except pythoncom.com_error as e:
                self.messageQueue.put('Driver COM Error in sendCommand {0}'.format(e))
            self.getAlignmentModel()

    def saveActualModel(self, target):
        self.sendCommand('modeldel0' + target)
        reply = self.sendCommand('modelsv0' + target)
        if reply == '1':
            return True
        else:
            return False

    def loadActualModel(self, target):
        reply = self.sendCommand('modelld0' + target)
        if reply == '1':
            return True
        else:
            return False

    def backupModel(self):
        if self.saveActualModel('BACKUP'):
            self.messageQueue.put('Actual Model save to BACKUP')
        else:
            self.logger.debug('backupModel    -> Model BACKUP could not be saved')                                          # log it

    def restoreModel(self):
        if self.loadActualModel('BACKUP'):
            self.messageQueue.put('Actual Model loaded from BACKUP')
        else:
            self.messageQueue.put('There is no model named BACKUP or error while loading')
            self.logger.debug('backupModel    -> Model BACKUP could not be loaded')                                         # log it

    def saveSimpleModel(self):
        if self.saveActualModel('SIMPLE'):
            self.messageQueue.put('Actual Model save to SIMPLE')
        else:
            self.logger.debug('saveSimpleModel-> Model SIMPLE could not be saved')                                          # log it

    def loadSimpleModel(self):
        if self.loadActualModel('SIMPLE'):
            self.messageQueue.put('Actual Model loaded from SIMPLE')
        else:
            self.messageQueue.put('There is no model named SIMPLE or error while loading')
            self.logger.debug('loadSimpleModel-> Model SIMPLE could not be loaded')                                         # log it

    def setRefractionParameter(self):
        if self.ui.le_pressureStick.text() != '':                                                                           # value must be there
            self.sendCommand('SRPRS{0:04.1f}'.format(float(self.ui.le_pressureStick.text())))
            if float(self.ui.le_temperatureStick.text()) > 0:
                self.sendCommand('SRTMP+{0:03.1f}'.format(float(self.ui.le_temperatureStick.text())))
            else:
                self.sendCommand('SRTMP-{0:3.1f}'.format(-float(self.ui.le_temperatureStick.text())))
            self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.sendCommand('GRTMP')})
            self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.sendCommand('GRPRS')})

    def getStatusFast(self):                                                                                                # fast status item like pointing
        reply = self.sendCommand('GS')
        if reply:
            self.sidereal_time = reply.strip('#')
            self.mountDataQueue.put({'Name': 'GetLocalTime', 'Value': '{0}'.format(self.sidereal_time)})                    # Sidereal local time
        reply = self.sendCommand('Ginfo')                                                                                   # use command "Ginfo" for fast topics
        if reply:                                                                                                           # if reply is there
            ra, dec, self.pierside, az, alt, self.jd, stat, slew = reply.rstrip('#').strip().split(',')                     # split the response to its parts
            self.raJnow = float(ra)
            self.decJnow = float(dec)
            self.jd = self.jd.rstrip('#')                                                                                   # needed for 2.14.8 beta firmware
            self.az = float(az)                                                                                             # same to azimuth
            self.alt = float(alt)                                                                                           # and altitude
            self.stat = int(stat)                                                                                           # status should be int for referencing list
            self.slewing = (slew == '1')                                                                                    # set status slewing
            self.ra, self.dec = self.transformNovas(self.raJnow, self.decJnow, 2)                                           # convert J2000
            ra_show = self.decimalToDegree(self.ra, False, False)
            dec_show = self.decimalToDegree(self.dec, True, False)
            self.mountDataQueue.put({'Name': 'GetTelescopeDEC', 'Value': '{0}'.format(dec_show)})                           # put dec to gui
            self.mountDataQueue.put({'Name': 'GetTelescopeRA', 'Value': '{0}'.format(ra_show)})                             # put ra to gui
            self.mountDataQueue.put({'Name': 'GetTelescopeAltitude', 'Value': '{0:03.2f}'.format(self.alt)})                # Altitude
            self.mountDataQueue.put({'Name': 'GetTelescopeAzimuth', 'Value': '{0:03.2f}'.format(self.az)})                  # Azimuth
            self.mountDataQueue.put({'Name': 'GetMountStatus', 'Value': '{0}'.format(self.stat)})                           # Mount status -> slew to stop
            if str(self.pierside) == str('W'):                                                                              # pier side
                self.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'WEST'})                                  # Transfer to test in GUI
            else:                                                                                                           #
                self.mountDataQueue.put({'Name': 'GetTelescopePierSide', 'Value': 'EAST'})                                  # Transfer to Text for GUI
            self.signalMountAzAltPointer.emit(self.az, self.alt)                                                            # set azalt Pointer in diagrams to actual pos
            self.timeToFlip = self.sendCommand('Gmte')
            self.mountDataQueue.put({'Name': 'GetTimeToTrackingLimit', 'Value': self.timeToFlip})                           # Flip time

    def getStatusMedium(self):                                                                                              # medium status items like refraction
        if self.ui.checkAutoRefraction.isChecked():                                                                         # check if autorefraction is set
            if self.stat != 0:                                                                                              # if no tracking, than autorefraction is good
                self.setRefractionParameter()                                                                               # transfer refraction from to mount
            else:                                                                                                           #
                success, message = self.SGPro.SgGetDeviceStatus('Camera')                                                   # getting the Camera status
                if success and message in ['IDLE', 'DOWNLOADING']:                                                          # if tracking, when camera is idle or downloading
                    self.setRefractionParameter()                                                                           # transfer refraction to mount
                else:                                                                                                       # otherwise
                    self.logger.debug('getStatusMedium-> no autorefraction: {0}'.format(message))                           # no autorefraction is possible
        self.signalMountTrackPreview.emit(True)

    def getStatusSlow(self):                                                                                                # slow update item like temps
        self.timeToFlip = self.sendCommand('Gmte')
        self.mountDataQueue.put({'Name': 'GetTimeToTrackingLimit', 'Value': self.timeToFlip})                               # Flip time
        self.refractionTemp = self.sendCommand('GRTMP')
        self.mountDataQueue.put({'Name': 'GetRefractionTemperature', 'Value': self.refractionTemp})                         # refraction temp out of mount
        self.refractionPressure = self.sendCommand('GRPRS')
        self.mountDataQueue.put({'Name': 'GetRefractionPressure', 'Value': self.refractionPressure})                        # refraction pressure out of mount
        self.mountDataQueue.put({'Name': 'GetTelescopeTempRA', 'Value': self.sendCommand('GTMP1')})                         # temp of RA motor
        self.mountDataQueue.put({'Name': 'GetTelescopeTempDEC', 'Value': self.sendCommand('GTMP2')})                        # temp of dec motor
        self.mountDataQueue.put({'Name': 'GetSlewRate', 'Value': self.sendCommand('GMs')})                                  # get actual slew rate
        self.mountDataQueue.put({'Name': 'GetRefractionStatus', 'Value': self.sendCommand('GREF')})                         #
        self.mountDataQueue.put({'Name': 'GetUnattendedFlip', 'Value': self.sendCommand('Guaf')})                           #
        self.mountDataQueue.put({'Name': 'GetDualAxisTracking', 'Value': self.sendCommand('Gdat')})                         #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitHigh', 'Value': self.sendCommand('Gh')})                    #
        self.mountDataQueue.put({'Name': 'GetCurrentHorizonLimitLow', 'Value': self.sendCommand('Go')})                     #

    def getStatusOnce(self):                                                                                                # one time updates for settings
        self.site_height = self.sendCommand('Gev')                                                                          # site height
        lon1 = self.sendCommand('Gg')                                                                                       # get site lon
        if lon1[0] == '-':                                                                                                  # due to compatibility to LX200 protocol east is negative
            self.site_lon = lon1.replace('-', '+')                                                                          # change that
        else:
            self.site_lon = lon1.replace('+', '-')                                                                          # and vice versa
        self.site_lat = self.sendCommand('Gt')                                                                              # get site latitude
        self.transform.Refraction = False                                                                                   # set parameter for ascom nova library
        self.transform.SiteElevation = float(self.site_height)                                                              # height
        self.transform.SiteLatitude = self.degStringToDecimal(self.site_lat)                                                # site lat
        self.transform.SiteLongitude = self.degStringToDecimal(self.site_lon)                                               # site lon
        self.mountDataQueue.put({'Name': 'GetCurrentSiteElevation', 'Value': self.site_height})                             # write data to GUI
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLongitude', 'Value': lon1})                                         #
        self.mountDataQueue.put({'Name': 'GetCurrentSiteLatitude', 'Value': self.site_lat})                                 #
        self.mountDataQueue.put({'Name': 'GetFirmwareDate', 'Value': self.sendCommand('GVD')})                              #
        self.mountDataQueue.put({'Name': 'GetFirmwareNumber', 'Value': self.sendCommand('GVN')})                            #
        self.mountDataQueue.put({'Name': 'GetFirmwareProductName', 'Value': self.sendCommand('GVP')})                       #
        self.mountDataQueue.put({'Name': 'GetFirmwareTime', 'Value': self.sendCommand('GVT')})                              #
        self.mountDataQueue.put({'Name': 'GetHardwareVersion', 'Value': self.sendCommand('GVZ')})                           #
        self.logger.debug('getStatusOnce  -> FW:{0}'.format(self.sendCommand('GVN')))                                       # firmware version for checking
        self.logger.debug('getStatusOnce  -> Site Lon:{0}'.format(self.site_lon))                                           # site lon
        self.logger.debug('getStatusOnce  -> Site Lat:{0}'.format(self.site_lat))                                           # site lat
        self.logger.debug('getStatusOnce  -> Site Height:{0}'.format(self.site_height))                                     # site height

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
