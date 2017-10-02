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
        self.transformationLockERFA = threading.Lock()                                                                      # locking object for single access to ascom transformation object

    def ra_dec_lst_to_az_alt(self, ra, dec):                                                                                # formula to make alt/az from hour angle and dec
        LAT = self.degStringToDecimal(self.app.mount.site_lat)
        ra = (ra * 360 / 24 + 360.0) % 360.0                                                                                # using hours.
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
            self.logger.error('error in conversion of:{0} with splitter:{1}, e:{2}'.format(value, splitter, e))
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

    # ---------------------------------------------------------------------------
    # implementation ascom.transform to erfa.py
    # ---------------------------------------------------------------------------

    def transformERFA(self, ra, dec, transform=1):
        self.transformationLockERFA.acquire()
        # TODO: check if site parameters available
        SiteElevation = float(self.app.mount.site_height)
        SiteLatitude = self.degStringToDecimal(self.app.mount.site_lat)
        SiteLongitude = self.degStringToDecimal(self.app.mount.site_lon)
        ts = datetime.datetime.utcnow()
        suc, dut1_prev = self.ERFA.eraDat(ts.year, ts.month, ts.day, 0)
        # TODO: Logger info with errors
        dut1 = 37 + 4023.0 / 125.0 - dut1_prev
        jd = float(self.app.mount.jd)
        suc, date1, date2 = self.ERFA.eraDtf2d('', ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second + ts.microsecond / 1000000)
        # jd = date1 + date2
        suc, tai1, tai2 = self.ERFA.eraUtctai(jd, 0)
        # TODO: Logger info with errors
        tt1, tt2 = self.ERFA.eraTaitt(tai1, tai2)
        jdtt = tt1 + tt2
        date1 = jd
        date2 = 0

        if transform == 1:  # J2000 to Topo Az /Alt
            ra = ra % 24                                                                                                    # mount has hours
            '''
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
            AzimuthTopo = aob * 360 / self.ERFA.ERFA_D2PI
            AltitudeTopo = 90.0 - zob * 360 / self.ERFA.ERFA_D2PI
            '''
            ri, di, eo = self.ERFA.eraAtci13(ra * self.ERFA.ERFA_D2PI / 24,
                                             dec * self.ERFA.ERFA_D2PI / 360,
                                             0,
                                             0,
                                             0,
                                             0,
                                             date1 + date2,
                                             0)
            RATopo = self.ERFA.eraAnp(ri - eo) * 24 / self.ERFA.ERFA_D2PI
            DECTopo = di * 360 / self.ERFA.ERFA_D2PI
            AzimuthTopo, AltitudeTopo = self.ra_dec_lst_to_az_alt(RATopo, DECTopo)

            val1 = AzimuthTopo
            val2 = AltitudeTopo

        elif transform == 2:    # Topo to J2000
            '''
            suc, rc, dc = self.ERFA.eraAtoc13('R',
                                              self.ERFA.eraAnp(ra * self.ERFA.ERFA_D2PI / 24 + self.ERFA.eraEo06a(jdtt, 0.0)),
                                              dec * self.ERFA.ERFA_D2PI / 360,
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
            '''
            rc, dc, eo = self.ERFA.eraAtic13(self.ERFA.eraAnp(ra * self.ERFA.ERFA_D2PI / 24 + self.ERFA.eraEo06a(jdtt, 0.0)),
                                             dec * self.ERFA.ERFA_D2PI / 360,
                                             date1 + date2,
                                             0.0)

            RAJ2000 = rc * 24.0 / self.ERFA.ERFA_D2PI
            DECJ2000 = dc * self.ERFA.ERFA_DR2D
            val1 = RAJ2000
            val2 = DECJ2000
        elif transform == 3:    # J2000 to Topo
            '''
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
            '''
            ri, di, eo = self.ERFA.eraAtci13(ra * self.ERFA.ERFA_D2PI / 24,
                                             dec * self.ERFA.ERFA_D2PI / 360,
                                             0,
                                             0,
                                             0,
                                             0,
                                             date1 + date2,
                                             0)
            RATopo = self.ERFA.eraAnp(ri - eo) * 24 / self.ERFA.ERFA_D2PI
            DECTopo = di * 360 / self.ERFA.ERFA_D2PI
            val1 = RATopo
            val2 = DECTopo
        else:
            val1 = ra
            val2 = dec
        self.transformationLockERFA.release()
        return val1, val2
