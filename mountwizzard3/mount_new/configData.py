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
                 fwTime='',):

        self.productName = productName
        self.fwNumber = fwNumber
        self.fw = fw
        self.hwVersion = hwVersion
        self.fwDate = fwDate
        self.fwTime = fwTime

    def __getattr__(self, name):
        if name == 'productName':
            self.productName = self._productName
            return self.productName
        if name == 'fwNumber':
            self.fwNumber = self._fwNumber
            return self.fwNumber
        if name == 'fw':
            self.fw = self._fw
            return self.fw
        if name == 'hwVersion':
            self.hwVersion = self._hwVersion
            return self.hwVersion
        if name == 'fwDate':
            self.fwDate = self._fwDate
            return self.fwDate
        if name == 'fwTime':
            self.fwTime = self._productName
            return self.fwTime

    def __setattr__(self, name, value):
        if name == 'productName':
            self._productName = value
        if name == 'fwNumber':
            self._fwNumber = value
            if value.count('.') == 2:
                _number = value.split('.')
                self._fw = _number[0] * 10000 + _number[1] * 100 + _number[2]
        if name == 'hwVersion':
            self._hwVersion = value
        if name == 'fwDate':
            self._fwDate = value
        if name == 'fwTime':
            self._fwTime = value

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