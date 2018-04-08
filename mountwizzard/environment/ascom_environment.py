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
import PyQt5
import time
if platform.system() == 'Windows':
    from win32com.client.dynamic import Dispatch
    import pythoncom


class AscomEnvironment:
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
        self.application['Name'] = 'Ascom Environment'
        self.application['Status'] = ''

    def start(self):
        pythoncom.CoInitialize()
        if self.driverName != '' and self.ascom is None:
            try:
                self.ascom = Dispatch(self.driverName)
                self.ascom.connected = True
                self.logger.info('Driver chosen:{0}'.format(self.driverName))
                self.application['Status'] = 'OK'
                self.logger.info('ASCOM Environment started')
            except Exception as e:
                self.application['Status'] = 'ERROR'
                self.logger.error('Could not dispatch driver: {0} and connect it, error: {1}'.format(self.driverName, e))
            finally:
                pass
        elif self.driverName == '':
            # no connection made
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedEnvironmentDataLock.unlock()
            self.application['Status'] = 'ERROR'
            self.logger.info('ASCOM Environment could not be started')

    def stop(self):
        try:
            if self.ascom:
                self.ascom.connected = False
        except Exception as e:
            self.logger.error('Could not stop driver: {0} and close it, error: {1}'.format(self.driverName, e))
        finally:
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedEnvironmentDataLock.unlock()
            self.ascom = None
            self.logger.info('ASCOM Environment stopped')
            pythoncom.CoUninitialize()

    def getStatus(self):
        try:
            if self.ascom:
                if self.ascom.connected:
                    self.app.sharedEnvironmentDataLock.lockForWrite()
                    self.data['Connected'] = True
                    self.app.sharedEnvironmentDataLock.unlock()
                else:
                    self.app.sharedEnvironmentDataLock.lockForWrite()
                    self.data['Connected'] = False
                    self.app.sharedEnvironmentDataLock.unlock()
                self.application['Status'] = 'OK'
            else:
                self.app.sharedEnvironmentDataLock.lockForWrite()
                self.data['Connected'] = False
                self.app.sharedEnvironmentDataLock.unlock()
        except Exception as e:
            self.logger.error('Could not dispatch driver: {0} and connect it, error: {1}'.format(self.driverName, e))
            self.app.sharedEnvironmentDataLock.lockForWrite()
            self.data['Connected'] = False
            self.app.sharedEnvironmentDataLock.unlock()
            self.application['Status'] = 'ERROR'
        finally:
            pass

    def getData(self):
        self.app.sharedEnvironmentDataLock.lockForWrite()
        try:
            self.data['DewPoint'] = self.ascom.DewPoint
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['Temperature'] = self.ascom.Temperature
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['Humidity'] = self.ascom.Humidity
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['Pressure'] = self.ascom.Pressure
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['SQR'] = self.ascom.SkyQuality
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['CloudCover'] = self.ascom.CloudCover
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['RainRate'] = self.ascom.RainRate
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['WindSpeed'] = self.ascom.WindSpeed
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        try:
            self.data['WindDirection'] = self.ascom.WindDirection
        except Exception as e:
            self.logger.error('Problem getting data, error: {0}'.format(e))
        finally:
            pass
        self.app.sharedEnvironmentDataLock.unlock()

    def setupDriver(self):
        try:
            self.chooser = Dispatch('ASCOM.Utilities.Chooser')
            self.chooser.DeviceType = 'ObservingConditions'
            self.driverName = self.chooser.Choose(self.driverName)
            self.app.messageQueue.put('Driver chosen:{0}\n'.format(self.driverName))
            self.logger.info('Driver chosen:{0}'.format(self.driverName))
        except Exception as e:
            self.app.messageQueue.put('#BRDriver error in Setup Driver\n')
            self.logger.error('General error:{0}'.format(e))
        finally:
            pass
