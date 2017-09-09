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
# --------------------------------------------------------------------------------
# python implementation of the ERFA library for the basic transformation functions
# --------------------------------------------------------------------------------
import math
from decimal import *


class ASTROM:
    pass


class ERFA:
    # star independent astrometry parameters
    astrom = ASTROM()
    ehpv = 0
    ebpv = 0
    r = 0
    x = 0
    y = 0
    # CONSTANTS
    ERFA_DD2R = 1.745329251994329576923691e-2
    ERFA_DJM0 = 2400000.5
    ERFA_DAYSEC = 86400.0

    # Macros as functions
    @staticmethod
    def ERFA_DNINT(value):
        return round(value, 0)

    def eraCal2jd(self, iy, im, id):
        # Earliest year allowed (4800BC)
        IYMIN = -4799

        # Month lengths in days
        mtab = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

        # Preset status.
        j = 0

        # Validate year and month.
        if iy < IYMIN:
            return -1, 0, 0
        if im < 1 or im > 12:
            return -2, 0, 0

        # If February in a leap year, 1, otherwise 0.
        # (im == 2) & & !(iy % 4) & & (iy % 100 | | !(iy % 400))
        if im == 2 and not iy % 4 and (iy % 100 or not iy % 400):
            ly = 1
        else:
            ly = 0

        # Validate day, taking into account leap years.
        if (id < 1) or (id > (mtab[im - 1] + ly)):
            j = -3

        # Return result.
        my = (im - 14) / 12
        iypmy = Decimal(iy + my)
        djm0 = self.ERFA_DJM0
        djm = int((Decimal(1461) * (iypmy + Decimal(4800))) / Decimal(4)) + int((Decimal(367) * Decimal((im - 2 - 12 * my))) / Decimal(12)) - int((Decimal(3) * ((iypmy + Decimal(4900)) / Decimal(100))) / Decimal(4)) + Decimal(id) - Decimal(2432076)

        # Return status and values.
        return j, float(djm0), float(djm)

    def eraDat(self, iy, im, id, fd):
        # Release year for this version of eraDat
        IYV = 2016

        # Reference dates (MJD) and drift rates (s/day), pre leap seconds
        drift = ((37300.0, 0.0012960),
                 (37300.0, 0.0012960),
                 (37300.0, 0.0012960),
                 (37665.0, 0.0011232),
                 (37665.0, 0.0011232),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (38761.0, 0.0012960),
                 (39126.0, 0.0025920),
                 (39126.0, 0.0025920))

        # Number of Delta(AT) expressions before leap seconds were introduced  = 0
        NERA1 = len(drift)

        # Dates and Delta(AT)s -> iyear, month, delat
        changes = ((1960, 1, 1.4178180),
                   (1961, 1, 1.4228180),
                   (1961, 8, 1.3728180),
                   (1962, 1, 1.8458580),
                   (1963, 11, 1.9458580),
                   (1964, 1, 3.2401300),
                   (1964, 4, 3.3401300),
                   (1964, 9, 3.4401300),
                   (1965, 1, 3.5401300),
                   (1965, 3, 3.6401300),
                   (1965, 7, 3.7401300),
                   (1965, 9, 3.8401300),
                   (1966, 1, 4.3131700),
                   (1968, 2, 4.2131700),
                   (1972, 1, 10.0),
                   (1972, 7, 11.0),
                   (1973, 1, 12.0),
                   (1974, 1, 13.0),
                   (1975, 1, 14.0),
                   (1976, 1, 15.0),
                   (1977, 1, 16.0),
                   (1978, 1, 17.0),
                   (1979, 1, 18.0),
                   (1980, 1, 19.0),
                   (1981, 7, 20.0),
                   (1982, 7, 21.0),
                   (1983, 7, 22.0),
                   (1985, 7, 23.0),
                   (1988, 1, 24.0),
                   (1990, 1, 25.0),
                   (1991, 1, 26.0),
                   (1992, 7, 27.0),
                   (1993, 7, 28.0),
                   (1994, 7, 29.0),
                   (1996, 1, 30.0),
                   (1997, 7, 31.0),
                   (1999, 1, 32.0),
                   (2006, 1, 33.0),
                   (2009, 1, 34.0),
                   (2012, 7, 35.0),
                   (2015, 7, 36.0),
                   (2017, 1, 37.0))

        # Number of Delta(AT) changes
        NDAT = len(changes)

        # Initialize the result to zero.
        deltat = 0.0

        # If invalid fraction of a day set error status and give up.
        if fd < 0.0 or fd > 1.0:
            return -4, deltat

        # Convert the date into an MJD.  = 0
        j, djm0, djm = self.eraCal2jd(iy, im, id)

        # If invalid year month or day give up.
        if j < 0:
            return j, deltat

        # If pre-UTC year set warning status and give up.
        if iy < changes[0][0]:
            return 1

        # If suspiciously late year set warning status but proceed.
        if iy > IYV + 5:
            j = 1

        # Combine year and month to form a date-ordered integer...
        m = 12 * iy + im

        # ...and use it to find the preceding table entry.
        for i in range(NDAT-1, -1,  -1):
            if m >= (12 * changes[i][0] + changes[i][1]):
                break

        # Prevent underflow warnings.
        if i < 0:
            return -5, deltat

        # Get the Delta(AT).
        deltat = changes[i][2]

        # If pre-1972 adjust for drift.
        if i < NERA1:
            deltat += (djm + fd - drift[i][0]) * drift[i][1]

        # Return the status.
        return j, deltat

    def eraJd2cal(self, dj1, dj2):
        DJMIN = -68569.5
        DJMAX = 1e9
        iy = 0
        im = 0
        id = 0
        fd = 0

        # Verify date is acceptable.
        dj = dj1 + dj2
        if dj < DJMIN or dj > DJMAX:
            return -1, iy, im, id, fd

        # Copy the date, big then small, and re-align to midnight.
        if dj1 >= dj2:
            d1 = Decimal(dj1)
            d2 = Decimal(dj2)
        else:
            d1 = Decimal(dj2)
            d2 = Decimal(dj1)
        d2 -= Decimal(0.5)

        # Separate day and fraction.
        f1 = Decimal(d1) % Decimal(1)
        f2 = Decimal(d2) % Decimal(1)
        f = Decimal(f1 + f2) % Decimal(1)
        if f < Decimal(0.0):
            f += Decimal(1.0)
        d = self.ERFA_DNINT(d1 - f1) + self.ERFA_DNINT(d2 - f2) + self.ERFA_DNINT(f1 + f2 - f)
        jd = self.ERFA_DNINT(d) + Decimal(1)

        # Express day in Gregorian calendar.
        p = int(Decimal(jd) + Decimal(68569))
        q = int((Decimal(4) * p) / Decimal(146097))
        r = p - int((Decimal(146097) * q + Decimal(3)) / Decimal(4))
        s = int((Decimal(4000) * (r + Decimal(1))) / Decimal(1461001))
        t = r - int(Decimal(1461) * s / Decimal(4)) + Decimal(31)
        u = int(Decimal(80) * t / Decimal(2447))
        v = int(u / Decimal(11))
        day = round(t - Decimal(2447) * u / Decimal(80), 0)
        month = round(u + Decimal(2) - Decimal(12) * v, 0)
        year = round(Decimal(100) * (q - Decimal(49)) + s + v, 0)
        fraction = f
        return 0, int(year), int(month), int(day), float(fraction)

    def eraDtf2d(self, scale, iy, im, id, ihr, imn, sec):
        # Today's Julian Day Number.
        js, dj, w = self.eraCal2jd(iy, im, id)
        if js != 0:
            return js, 0, 0
        dj += w

        # Day length and final minute length in seconds (provisional).
        day = self.ERFA_DAYSEC
        seclim = 60.0

        # Deal with the UTC leap second case.
        if scale == 'UTC':

            # TAI-UTC at 0h today.
            js, dat0 = self.eraDat(iy, im, id, 0.0)
            if js < 0:
                return js, 0, 0

            # TAI-UTC at 12h today (to detect drift).
            js, dat12 = self.eraDat(iy, im, id, 0.5)
            if js < 0:
                return js, 0, 0

            # TAI-UTC at 0h tomorrow (to detect jumps).
            js, iy2, im2, id2, w = self.eraJd2cal(dj, 1.5)
            if js == 1:
                return js, 0, 0
            js, dat24 = self.eraDat(iy2, im2, id2, 0.0)
            if js < 0:
                return js, 0, 0

            # Any sudden change in TAI-UTC between today and tomorrow.
            dleap = dat24 - (2.0 * dat12 - dat0)

            # If leap second day, correct the day and final minute lengths.
            day += dleap
            if ihr == 23 and imn == 59:
                seclim += dleap

        # Validate the time.
        if 0 <= ihr <= 23:
            if 0 <= imn <= 59:
                if sec >= 0:
                    if sec >= seclim:
                        js += 2
                else:
                    js = -6
            else:
                js = -5
        else:
            js = -4
        if js < 0:
            return js, 0, 0

        # The time in days.
        time = (60.0 * (60.0 * ihr + imn) + sec) / day

        # Return the Status date and time.
        return js, dj, time

    # real calulcation

    def eraEpv00(self, date1, date2, ehpv, ebpv):
        pass

    def eraPnm06a(self, date1, date2, r):
        pass

    def eraBpn2xy(self, r, x, y):
        pass

    def eraS06(self, date1, date2, x, y):
        return 0

    def eraApci(self, date1, date2, ebpv, ehpv, x, y, s, astrom):
        pass

    def eraEors(self, r, s):
        return 0

    def eraApci13(self, date1, date2, astrom, eo):
        # Earth barycentric & heliocentric position/velocity (au, au/d).
        ehpv = self.ehpv
        ebpv = self.ebpv
        self.eraEpv00(date1, date2, ehpv, ebpv)
        # Form the equinox based BPN matrix, IAU 2006/2000A.
        r = self.r
        self.eraPnm06a(date1, date2, r)
        # Extract CIP X,Y.
        x = self.x
        y = self.y
        self.eraBpn2xy(r, x, y)
        # Obtain CIO locator s.
        s = self.eraS06(date1, date2, x, y)
        # Compute the star-independent astrometry parameters.
        self.eraApci(date1, date2, ebpv, ehpv, x, y, s, astrom)
        # Equation of the origins.
        eo = self.eraEors(r, s)

    def eraAtciq(self, re, dc, pr, pd, px, py, astrom, ri, di):
        pass

    def eraAtci13(self, rc, dc, pr, pd, px, rv, date1, date2, ri, di, eo):
        # star independent parameters
        astrom = self.astrom
        # the transformation parameters.
        self.eraApci13(date1, date2, astrom, eo)
        # ICRS (epoch J2000.0) to CIRS.
        self.eraAtciq(rc, dc, pr, pd, px, rv, astrom, ri, di)
