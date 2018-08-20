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


class WrongSettingError:
    pass


class Firmware(object):

    def __init__(self,
                 productName='',
                 fwNumber='',
                 fw=0,
                 hwVersion='',
                 fwDate='',
                 fwTime='',
                 ):

        self._productName = productName
        self._fwNumber = fwNumber
        self._fw = fw
        self._hwVersion = hwVersion
        self._fwDate = fwDate
        self._fwTime = fwTime

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
        value = '{0} {1} {2}'.format(self._productName,
                                     self._fwNumber,
                                     self._hwVersion,
                                     )
        return value

    def __repr__(self):
        # how to print it
        pass

    def hms(self, warn=True):
        """Convert to a tuple (hours, minutes, seconds).
        """
        pass


class Setting(object):

    def __init__(self):
        pass

    def __getattr__(self, name):
        if name == 'hours':
            if self.preference != 'hours':
                raise WrongUnitError('hours')
            self.hours = hours = self._hours
            return hours
        if name == 'degrees':
            if self.preference != 'degrees':
                raise WrongUnitError('degrees')
            self.degrees = degrees = self._degrees
            return degrees
        raise AttributeError('no attribute named %r' % (name,))

    def __setattr__(self, name):
        # set the attributes
        pass

    def __str__(self):
        if self.radians.size == 0:
            return 'Angle []'
        return self.dstr() if self.preference == 'degrees' else self.hstr()

    def __repr__(self):
        # how to print it
        pass

    def hms(self, warn=True):
        """Convert to a tuple (hours, minutes, seconds).
        """
        pass