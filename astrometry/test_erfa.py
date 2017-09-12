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
        self.assertEqual(ok, 0)
        self.assertEqual(value[0], djm0)
        self.assertEqual(value[1], djm)

    def test_eraDtf2d(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        value = erfa_astro.dtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        self.assertEqual(0, ok)
        self.assertEqual(date1 + date2, value[0])

    def test_eraEpv00(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        ok, pvh, pvb = self.ERFA.eraEpv00(date1, date2)
        pvh_ref, pvb_ref = erfa_astro.epv00(date1, date2)
        self.assertEqual(ok, 0)
        self.assertEqual(pvh[0][0], pvh_ref[0][0])
        self.assertEqual(pvh[0][1], pvh_ref[0][1])
        self.assertEqual(pvh[0][2], pvh_ref[0][2])
        self.assertEqual(pvh[1][0], pvh_ref[1][0])
        self.assertEqual(pvh[1][1], pvh_ref[1][1])
        self.assertEqual(pvh[1][2], pvh_ref[1][2])
        self.assertEqual(pvb[0][0], pvb_ref[0][0])
        self.assertEqual(pvb[0][1], pvb_ref[0][1])
        self.assertEqual(pvb[0][2], pvb_ref[0][2])
        self.assertEqual(pvb[1][0], pvb_ref[1][0])
        self.assertEqual(pvb[1][1], pvb_ref[1][1])
        self.assertEqual(pvb[1][2], pvb_ref[1][2])

    def test_eraObl06(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        epsa = self.ERFA.eraObl06(date1, date2)
        epsa_ref = erfa_astro.obl06(date1, date2)
        self.assertEqual(epsa, epsa_ref)

    def test_eraPfw06(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        gamb, phib, psib, epsa = self.ERFA.eraPfw06(date1, date2)
        gamb_ref, phib_ref, psib_ref, epsa_ref = erfa_astro.pfw06(date1, date2)
        self.assertEqual(gamb, gamb_ref)
        self.assertEqual(phib, phib_ref)
        self.assertEqual(psib, psib_ref)
        self.assertEqual(epsa, epsa_ref)

    def test_eraFal03(self):
        for i in range(-10, 10):
            el = self.ERFA.eraFal03(i)
            el_ref = erfa_astro.fal03(i)
            self.assertEqual(el, el_ref)

    def test_eraFaf03(self):
        for i in range(-10, 10):
            el = self.ERFA.eraFaf03(i)
            el_ref = erfa_astro.faf03(i)
            self.assertEqual(el, el_ref)

    def test_eraFaom03(self):
        for i in range(-10, 10):
            el = self.ERFA.eraFaom03(i)
            el_ref = erfa_astro.faom03(i)
            self.assertEqual(el, el_ref)

    def test_eraNut00a(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        dp, de = self.ERFA.eraNut00a(date1, date2)
        dp_ref, de_ref = erfa_astro.nut00a(date1, date2)
        self.assertEqual(dp, dp_ref)
        self.assertEqual(de, de_ref)

    def test_eraNut06a(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        dp, de = self.ERFA.eraNut06a(date1, date2)
        dp_ref, de_ref = erfa_astro.nut06a(date1, date2)
        self.assertEqual(dp, dp_ref)
        self.assertEqual(de, de_ref)

    def test_eraS06(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        val = self.ERFA.eraS06(date1, date2, x, y)
        val_ref = erfa_astro.s06(date1, date2, x, y)
        self.assertEqual(val, val_ref)

    def test_eraApci13(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        value = erfa_astro.apci13(date1, date2)
        ok, astrom, eo = self.ERFA.eraApci13(date1, date2)

    '''

    def test_eraAtci13(self):
        self.ERFA.eraAtci13(self.rc, self.dc, self.pr, self.pd, self.px, self.rv, self.date1, self.date2, self.ri, self.di, self.eo)
    '''