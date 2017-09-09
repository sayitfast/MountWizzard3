from unittest import TestCase
from astrometry import erfa
import time
from astropy import _erfa as erfa_astro


class TestErfa(TestCase):

    def setUp(self):
        # necessary structs in classes
        self.ERFA = erfa.ERFA()

        # parameters for test
        self.ra_center = 345.986294056
        self.dec_center = 28.1503891981
        self.pr = 0
        self.pd = 0
        self.px = 0
        self.rv = 0
        self.elong = 0.0
        self.phi = 0.0
        self.hm = 0
        self.xp = 0.0
        self.yp = 0.0
        self.phpa = 1000.0
        self.tc = 0.0
        self.rh = 0.0
        self.wl = 0.5

        self.astrom = self.ERFA.astrom
        self.eo = 0

        self.dut1 = 0.36                # // http: // maia.usno.navy.mil / ser7 / ser7.dat

        # return values
        self.di = 0
        self.ri = 0
        self.eo = 0

        # pre calculations for right format
        self.rc = self.ERFA.ERFA_DD2R * self.ra_center
        self.dc = self.ERFA.ERFA_DD2R * self.dec_center
        self.ts = time.gmtime(0)

    def test_eraJd2cal(self):
        dj1 = 2450123.7
        dj2 = 0.0
        ok, iy, im, id, fd = self.ERFA.eraJd2cal(dj1, dj2)
        value = erfa_astro.jd2cal(dj1, dj2)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], iy)
        self.assertEqual(value[1], im)
        self.assertEqual(value[2], id)
        self.assertEqual(value[3], fd)

        dj1 = 2400000.5
        dj2 = 50123.2
        ok, iy, im, id, fd = self.ERFA.eraJd2cal(dj1, dj2)
        value = erfa_astro.jd2cal(dj1, dj2)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], iy)
        self.assertEqual(value[1], im)
        self.assertEqual(value[2], id)
        self.assertEqual(value[3], fd)

        dj1 = 2451545.0
        dj2 = -1421.3
        ok, iy, im, id, fd = self.ERFA.eraJd2cal(dj1, dj2)
        value = erfa_astro.jd2cal(dj1, dj2)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], iy)
        self.assertEqual(value[1], im)
        self.assertEqual(value[2], id)
        self.assertEqual(value[3], fd)

        dj1 = 2450123.5
        dj2 = 0.2
        ok, iy, im, id, fd = self.ERFA.eraJd2cal(dj1, dj2)
        value = erfa_astro.jd2cal(dj1, dj2)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], iy)
        self.assertEqual(value[1], im)
        self.assertEqual(value[2], id)
        self.assertEqual(value[3], fd)

        dj1 = 2451967
        dj2 = 0
        ok, iy, im, id, fd = self.ERFA.eraJd2cal(dj1, dj2)
        value = erfa_astro.jd2cal(dj1, dj2)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], iy)
        self.assertEqual(value[1], im)
        self.assertEqual(value[2], id)
        self.assertEqual(value[3], fd)

    def test_eraCal2jd(self):
        ok, djm0, djm = self.ERFA.eraCal2jd(self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday)
        value = erfa_astro.cal2jd(self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday)
        print(value)
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], djm0)
        self.assertEqual(value[1], djm)

    def test_eraDtf2d(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        value = erfa_astro.dtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        self.assertEqual(0, ok)
        self.assertEqual(date1 + date2, value[0])

    '''
    def test_eraApci13(self):
        self.ERFA.eraApci13(self.date1, self.date2, self.astrom, self.eo)

    def test_eraAtci13(self):
        self.ERFA.eraAtci13(self.rc, self.dc, self.pr, self.pd, self.px, self.rv, self.date1, self.date2, self.ri, self.di, self.eo)
    '''