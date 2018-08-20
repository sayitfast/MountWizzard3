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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import socket
import sys

import PyQt5.QtCore
import skyfield.api


class Firmware(object):

    firmwareLock = PyQt5.QtCore.QReadWriteLock()

    def __init__(self):

        self._productName = ''
        self._fwNumber = ''
        self._fw = 0
        self._hwVersion = ''
        self._fwDate = ''
        self._fwTime = ''

    @property
    def productName(self):
        return self._productName

    @productName.setter
    def productName(self, value):
        self._productName = value

    @property
    def fwNumber(self):
        return self._fwNumber

    @property
    def fw(self):
        return self._fw

    @fwNumber.setter
    def fwNumber(self, value):
        self._fwNumber = value
        if value.count('.') == 2:
            _number = value.split('.')
            self._fw = int(_number[0]) * 10000 + int(_number[1]) * 100 + int(_number[2])
        else:
            self._fw = 0

    @property
    def hwVersion(self):
        return self._hwVersion

    @hwVersion.setter
    def hwVersion(self, value):
        self._hwVersion = value

    @property
    def fwDate(self):
        return self._fwDate

    @fwDate.setter
    def fwDate(self, value):
        self._fwDate = value

    @property
    def fwTime(self):
        return self._fwTime

    @fwTime.setter
    def fwTime(self, value):
        self._fwTime = value

    def __str__(self):
        output = '<Product: {0}>   <Firmware: {1}>   <Hardware: {2}>'
        value = output.format(self._productName,
                              self._fwNumber,
                              self._hwVersion,
                              )
        return value


class Site(object):

    siteLock = PyQt5.QtCore.QReadWriteLock()

    def __init__(self, timeScale):
        self._location = None
        self._mountTime = None
        self._timeScale = timeScale

    @staticmethod
    def _stringToDegree(value, splitter=':'):
        value = [float(x) for x in value.split(splitter)]
        value = value[0] + value[1] / 60 + value[2] / 3600
        return value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        lat, lon, elev = value
        lon = skyfield.api.Angle(degrees=self._stringToDegree(lon))
        lat = skyfield.api.Angle(degrees=self._stringToDegree(lat))
        self._location = skyfield.api.Topos(longitude=lon,
                                            latitude=lat,
                                            elevation_m=elev)

    def __str__(self):
        output = '<Lat: {0}>   <Lon: {1}>   <Elev: {2}>'
        value = output.format(self._location.latitude,
                              self._location.longitude,
                              self._location.elevation.m,
                              )
        return value


class Setting(object):

    settingLock = PyQt5.QtCore.QReadWriteLock()

    def __init__(self):
        pass

