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
import platform
if platform.system() == 'Windows':
    from win32com.client.dynamic import Dispatch
    import pythoncom


class AscomDome:
    logger = logging.getLogger(__name__)

    def __init__(self, main, app, data):
        # make main sources available
        self.main = main
        self.app = app
        self.data = data
        self.ascom = None
        self.chooser = None
        self.driverName = ''
        self.application = dict()
        self.application['Available'] = True
        self.application['Name'] = 'Ascom Dome'
        self.application['Status'] = ''

    def start(self):
        pythoncom.CoInitialize()
        if self.driverName != '' and self.ascom is None:
            try:
                self.ascom = Dispatch(self.driverName)
                self.ascom.connected = True
                self.logger.info('Driver chosen:{0}'.format(self.driverName))
                self.application['Status'] = 'OK'
                self.app.sharedDomeDataLock.lockForWrite()
                self.data['Connected'] = True
                self.app.sharedDomeDataLock.unlock()
                self.logger.info('ASCOM dome started')
            except Exception as e:
                self.application['Status'] = 'ERROR'
                self.logger.error('Could not dispatch driver: {0} and connect it, error: {1}'.format(self.driverName, e))
            finally:
                pass
        elif self.driverName == '':
            # no connection made
            self.app.sharedDomeDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedDomeDataLock.unlock()
            self.application['Status'] = 'ERROR'
            self.logger.info('ASCOM Dome could not be started')

    def stop(self):
        try:
            if self.ascom:
                self.ascom.connected = False
        except Exception as e:
            self.logger.error('Could not stop driver: {0} and close it, error: {1}'.format(self.driverName, e))
        finally:
            self.app.sharedDomeDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedDomeDataLock.unlock()
            self.ascom = None
            self.logger.info('ASCOM Dome stopped')
            pythoncom.CoUninitialize()

    def slewToAzimuth(self, azimuth):
        if not self.ascom:
            return
        if not self.ascom.connected:
            return
        try:
            self.ascom.SlewToAzimuth(float(azimuth))
        except Exception as e:
            self.logger.error('Problem slewing azimuth, error: {0}'.format(e))
        finally:
            pass

    def getStatus(self):
        try:
            if self.ascom:
                if self.ascom.connected:
                    self.app.sharedDomeDataLock.lockForWrite()
                    self.data['Connected'] = True
                    self.app.sharedDomeDataLock.unlock()
                else:
                    self.app.sharedDomeDataLock.lockForWrite()
                    self.data['Connected'] = False
                    self.app.sharedDomeDataLock.unlock()
                self.application['Status'] = 'OK'
            else:
                self.app.sharedDomeDataLock.lockForWrite()
                self.data['Connected'] = False
                self.app.sharedDomeDataLock.unlock()
        except Exception as e:
            self.logger.error('Could not dispatch driver: {0} and connect it, error: {1}'.format(self.driverName, e))
            self.app.sharedDomeDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedDomeDataLock.unlock()
            self.application['Status'] = 'ERROR'
        finally:
            pass

    def getData(self):
        if not self.ascom:
            return
        if not self.ascom.connected:
            return
        self.app.sharedDomeDataLock.lockForWrite()
        try:
            if self.data['Slewing'] and not self.ascom.Slewing:
                self.main.signalSlewFinished.emit()
                self.app.audioCommandQueue.put('DomeSlew')
            self.data['Slewing'] = self.ascom.Slewing
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['Azimuth'] = self.ascom.Azimuth
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        #try:
        #    self.data['Altitude'] = self.ascom.Altitude
        #except Exception as e:
        #    self.logger.error('Problem getting data, error: {0}'.format(e))
        #finally:
        #    pass
        self.app.sharedDomeDataLock.unlock()

    def setupDriver(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'Dome'
            self.driverName = self.chooser.Choose(self.driverName)
            self.app.messageQueue.put('Driver chosen:{0}\n'.format(self.driverName))
            self.logger.info('Driver chosen:{0}'.format(self.driverName))
        except Exception as e:
            self.app.messageQueue.put('#BRDriver error in Setup Driver\n')
            self.logger.error('General error:{0}'.format(e))
        finally:
            pass
