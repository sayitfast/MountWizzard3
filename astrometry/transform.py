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
import logging
import math
import threading
# win32com
from win32com.client.dynamic import Dispatch


class Transform:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.transformationLock = threading.Lock()                                                                          # locking object for single access to ascom transformation object
        try:                                                                                                                # start accessing a com object
            self.transform = Dispatch('ASCOM.Astrometry.Transform.Transform')                                               # novas library for Jnow J2000 conversion through ASCOM
            self.transform.Refraction = False
        except Exception as e:
            self.logger.error('transform.init -> loading ASCOM transform error:{0}'.format(e))
        finally:
            pass

    def transformNovas(self, ra, dec, transform=1):                                                                         # wrapper for the novas ascom implementation
        self.transformationLock.acquire()                                                                                   # which is not threat safe, so we have to do this
        # self.transform.JulianDateTT = self.jd
        if transform == 1:                                                                                                  # 1 = J2000 -> alt/az
            ra = ra % 24
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
            ra = ra % 24
            self.transform.SetTopocentric(ra, dec)                                                                          # set JNow ra, dec
            val1 = self.transform.AzimuthTopocentric                                                                        # convert az
            val2 = self.transform.ElevationTopocentric                                                                      # convert alt
        elif transform == 5:                                                                                                # 5 = Apparent -> alt/az
            ra = ra % 24
            self.transform.SetApparent(ra, dec)                                                                             # set apparent ra, dec
            val1 = self.transform.AzimuthTopocentric                                                                        # convert az
            val2 = self.transform.ElevationTopocentric                                                                      # convert alt
        else:
            val1 = ra
            val2 = dec
        self.transformationLock.release()                                                                                   # release locking for thread safety
        return val1, val2

    def transformNovasSiteParams(self, site_lat, site_lon, site_height):
        self.transform.Refraction = False                                                                                   # set parameter for ascom nova library
        self.transform.SiteElevation = site_height                                                                          # height
        self.transform.SiteLatitude = self.degStringToDecimal(site_lat)                                                     # site lat
        self.transform.SiteLongitude = self.degStringToDecimal(site_lon)                                                    # site lon

    def transformNovasRefractionParams(self, site_temp, site_press):
        self.transform.SiteTemperature = site_temp                                                                          # height

    @staticmethod
    def ra_dec_lst_to_az_alt(ra, dec, LAT):                                                                                 # formula to make alt/az from hour angle and dec
        ra = (ra * 15 + 360.0) % 360.0
        dec = math.radians(dec)
        ra = math.radians(ra)
        lat = math.radians(LAT)
        alt = math.asin(math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ra))
        A = math.acos((math.sin(dec) - math.sin(alt) * math.sin(lat)) / (math.cos(alt) * math.cos(lat)))
        A = math.degrees(A)
        alt = math.degrees(alt)
        if math.sin(ra) >= 0.0:
            az = 360.0 - A
        else:
            az = A
        return az, alt

    def degStringToDecimal(self, value, splitter=':'):                                                                      # conversion between Strings formats and decimal representation
        sign = 1
        if '-' in value:
            value = value.replace('-', '')
            sign = -1
        elif '+' in value:
            value = value.replace('+', '')
        try:
            if len(value.split(splitter)) == 3:
                hour, minute, second = value.split(splitter)
                return (float(hour) + float(minute) / 60 + float(second) / 3600) * sign
            elif len(value.split(splitter)) == 2:
                hour, minute = value.split(splitter)
                return (float(hour) + float(minute) / 60) * sign
        except Exception as e:
            self.logger.error('degStringToDeci-> error in conversion of:{0} with splitter:{1}, e:{2}'.format(value, splitter, e))
            return 0

    @staticmethod
    def decimalToDegree(value, with_sign=True, with_decimal=False, spl=':'):                                               # format decimal value to string in degree format
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
