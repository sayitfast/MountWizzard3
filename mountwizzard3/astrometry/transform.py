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
###########################################################
import logging
import math
import datetime
import PyQt5
from astropy import _erfa


class Transform:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.ERFA = _erfa
        self.mutexERFA = PyQt5.QtCore.QMutex()
        self.mutexTopocentric = PyQt5.QtCore.QMutex()
        # if nothing is present, use the coordinates of greenwich
        self.siteLat = 51.476852
        self.siteLon = 0
        self.siteHeight = 46
        # date of 01.05.2018
        self.julianDate = 2458240
        # connect data transfer
        self.app.signalMountSiteData.connect(self.setSiteData)
        self.app.signalJulianDate.connect(self.setJulianDate)

    def setSiteData(self, lat, lon, height):
        self.siteLat = self.degStringToDecimal(lat)
        self.siteLon = self.degStringToDecimal(lon)
        self.siteHeight = float(height)

    def setJulianDate(self, jd):
        self.julianDate = jd

    def topocentricToAzAlt(self, ra, dec):
        self.mutexTopocentric.lock()
        ra = (ra * 360 / 24 + 360.0) % 360.0
        dec = math.radians(dec)
        ra = math.radians(ra)
        lat = math.radians(self.siteLat)
        alt = math.asin(math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ra))
        value = (math.sin(dec) - math.sin(alt) * math.sin(lat)) / (math.cos(alt) * math.cos(lat))
        # we have to check for rounding error, which could happen
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        A = math.acos(value)
        A = math.degrees(A)
        alt = math.degrees(alt)
        if math.sin(ra) >= 0.0:
            az = 360.0 - A
        else:
            az = A
        self.mutexTopocentric.unlock()
        return az, alt

    def degStringToDecimal(self, value, splitter=':'):
        returnValue = 0
        sign = 1
        if '-' in value:
            value = value.replace('-', '')
            sign = -1
        elif '+' in value:
            value = value.replace('+', '')
        else:
            # just for formal understanding
            pass
        try:
            if len(value.split(splitter)) == 3:
                hour, minute, second = value.split(splitter)
                returnValue = (float(hour) + float(minute) / 60 + float(second) / 3600) * sign
            elif len(value.split(splitter)) == 2:
                hour, minute = value.split(splitter)
                returnValue = (float(hour) + float(minute) / 60) * sign
        except Exception as e:
            self.logger.error('Error in conversion of:{0} with splitter:{1}, e:{2}'.format(value, splitter, e))
            returnValue = 0
        finally:
            pass
        return returnValue

    @staticmethod
    def decimalToDegree(value, with_sign=True, with_decimal=False, spl=':'):
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
            returnValue = '{0}{1:02d}{5}{2:02d}{5}{3:02d}{4}'.format(sign, hour, minute, second, second_dec, spl)
        else:
            returnValue = '{0:02d}{4}{1:02d}{4}{2:02d}{3}'.format(hour, minute, second, second_dec, spl)
        return returnValue

    @staticmethod
    def decimalToDegreeMountSr(value):
        degree = int(value)
        minute = int((value - degree) * 60)
        second = int(((value - degree) * 60 - minute) * 60)
        second_dec = int((((value - degree) * 60 - minute) * 60 - second) * 100)
        returnValue = ':Sr{0:02d}:{1:02d}:{2:02d}.{3:02d}#'.format(degree, minute, second, second_dec)
        return returnValue

    @staticmethod
    def decimalToDegreeMountSd(value):
        if value >= 0:
            sign = '+'
        else:
            sign = '-'
        value = abs(value)
        degree = int(value)
        minute = int((value - degree) * 60)
        second = int(((value - degree) * 60 - minute) * 60)
        second_dec = int((((value - degree) * 60 - minute) * 60 - second) * 10)
        returnValue = ':Sd{0}{1:02d}*{2:02d}:{3:02d}.{4:01d}#'.format(sign, degree, minute, second, second_dec)
        return returnValue

    def transformERFA(self, ra, dec, transform=1):
        self.mutexERFA.lock()
        ts = datetime.datetime.utcnow()
        dut1_prev = self.ERFA.dat(ts.year, ts.month, ts.day, 0)
        dut1 = 37 + 4023.0 / 125.0 - dut1_prev
        # suc, tai1, tai2 = self.ERFA.eraUtctai(self.julianDate, 0)
        tai1, tai2 = self.ERFA.utctai(self.julianDate, 0)
        # tt1, tt2 = self.ERFA.eraTaitt(tai1, tai2)
        tt1, tt2 = self.ERFA.taitt(tai1, tai2)
        jdtt = tt1 + tt2
        date1 = self.julianDate
        date2 = 0

        if transform == 1:  # J2000 to Topo Az /Alt
            ra = ra % 24
            aob, zob, hob, dob, rob, eo = self.ERFA.atco13(ra * self.ERFA.D2PI / 24,
                                                           dec * self.ERFA.D2PI / 360,
                                                           0.0,
                                                           0.0,
                                                           0.0,
                                                           0.0,
                                                           date1 + date2,
                                                           0.0,
                                                           dut1,
                                                           self.siteLon * self.ERFA.DD2R,
                                                           self.siteLat * self.ERFA.DD2R,
                                                           self.siteHeight,
                                                           0.0,
                                                           0.0,
                                                           0.0,
                                                           0.0,
                                                           0.0,
                                                           0.0)
            val1 = aob * 360 / self.ERFA.D2PI
            val2 = 90.0 - zob * 360 / self.ERFA.D2PI

        elif transform == 2:                                                                                                # Topo to J2000
            rc, dc, eo = self.ERFA.atic13(self.ERFA.anp(ra * self.ERFA.D2PI / 24 + self.ERFA.eo06a(jdtt, 0.0)),
                                          dec * self.ERFA.D2PI / 360,
                                          date1 + date2,
                                          0.0)
            val1 = rc * 24.0 / self.ERFA.D2PI
            val2 = dc * self.ERFA.DR2D

        elif transform == 3:                                                                                                # J2000 to Topo
            ri, di, eo = self.ERFA.atci13(ra * self.ERFA.D2PI / 24,
                                          dec * self.ERFA.D2PI / 360,
                                          0,
                                          0,
                                          0,
                                          0,
                                          date1 + date2,
                                          0)
            val1 = self.ERFA.anp(ri - eo) * 24 / self.ERFA.D2PI
            val2 = di * 360 / self.ERFA.D2PI
        else:
            val1 = ra
            val2 = dec
        self.mutexERFA.unlock()
        return val1, val2
