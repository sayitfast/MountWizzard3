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
import datetime
from astrometry.erfa import ERFA
import threading


class Transform:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.ERFA = ERFA()
        self.transformationLockERFA = threading.Lock()
        self.conversionLock = threading.Lock()

    def ra_dec_lst_to_az_alt(self, ra, dec):
        LAT = self.degStringToDecimal(self.app.workerMountDispatcher.data['SiteLatitude'])
        ra = (ra * 360 / 24 + 360.0) % 360.0
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

    def transformERFA(self, ra, dec, transform=1):
        # ---------------------------------------------------------------------------
        # implementation ascom.transform to erfa.py
        # ---------------------------------------------------------------------------
        self.transformationLockERFA.acquire()
        SiteElevation = float(self.app.workerMountDispatcher.data['SiteHeight'])
        SiteLatitude = self.degStringToDecimal(self.app.workerMountDispatcher.data['SiteLatitude'])
        SiteLongitude = self.degStringToDecimal(self.app.workerMountDispatcher.data['SiteLongitude'])
        if SiteLatitude == 0 or SiteLongitude == 0 or SiteElevation == 0:
            self.logger.error('No site parameters set')
            return 0, 0
        ts = datetime.datetime.utcnow()
        suc, dut1_prev = self.ERFA.eraDat(ts.year, ts.month, ts.day, 0)
        if suc != 0:
            self.logger.error('error result : {0} in eraDat year: {1}, month: {2}, day: {3}'.format(suc, ts.year, ts.month, ts.day))
        dut1 = 37 + 4023.0 / 125.0 - dut1_prev
        jd = float(self.app.workerMountDispatcher.data['JulianDate'])
        suc, tai1, tai2 = self.ERFA.eraUtctai(jd, 0)
        if suc != 0:
            self.logger.error('error result : {0} in eraUtctai jd: {1}'.format(suc, jd))
        tt1, tt2 = self.ERFA.eraTaitt(tai1, tai2)
        jdtt = tt1 + tt2
        date1 = jd
        date2 = 0

        if transform == 1:  # J2000 to Topo Az /Alt
            ra = ra % 24                                                                                                    # mount has hours
            suc, aob, zob, hob, dob, rob, eo = self.ERFA.eraAtco13(ra * self.ERFA.ERFA_D2PI / 24,
                                                                   dec * self.ERFA.ERFA_D2PI / 360,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0,
                                                                   date1 + date2,
                                                                   0.0,
                                                                   dut1,
                                                                   SiteLongitude * self.ERFA.ERFA_DD2R,
                                                                   SiteLatitude * self.ERFA.ERFA_DD2R,
                                                                   SiteElevation,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0,
                                                                   0.0)
            val1 = aob * 360 / self.ERFA.ERFA_D2PI
            val2 = 90.0 - zob * 360 / self.ERFA.ERFA_D2PI

        elif transform == 2:                                                                                                # Topo to J2000
            rc, dc, eo = self.ERFA.eraAtic13(self.ERFA.eraAnp(ra * self.ERFA.ERFA_D2PI / 24 + self.ERFA.eraEo06a(jdtt, 0.0)),
                                             dec * self.ERFA.ERFA_D2PI / 360,
                                             date1 + date2,
                                             0.0)
            val1 = rc * 24.0 / self.ERFA.ERFA_D2PI
            val2 = dc * self.ERFA.ERFA_DR2D

        elif transform == 3:                                                                                                # J2000 to Topo
            ri, di, eo = self.ERFA.eraAtci13(ra * self.ERFA.ERFA_D2PI / 24,
                                             dec * self.ERFA.ERFA_D2PI / 360,
                                             0,
                                             0,
                                             0,
                                             0,
                                             date1 + date2,
                                             0)
            val1 = self.ERFA.eraAnp(ri - eo) * 24 / self.ERFA.ERFA_D2PI
            val2 = di * 360 / self.ERFA.ERFA_D2PI
        else:
            val1 = ra
            val2 = dec
        self.transformationLockERFA.release()
        return val1, val2
