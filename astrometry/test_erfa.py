from unittest import TestCase
from astrometry import erfa
import time
from astropy import _erfa as erfa_astro
import numpy


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

    def test_eraPnm06a(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        rnpb = self.ERFA.eraPnm06a(date1, date2)
        rnpb_ref = erfa_astro.pnm06a(date1, date2)
        self.assertEqual(rnpb[0][0], rnpb_ref[0][0])
        self.assertEqual(rnpb[0][1], rnpb_ref[0][1])
        self.assertEqual(rnpb[0][2], rnpb_ref[0][2])
        self.assertEqual(rnpb[1][0], rnpb_ref[1][0])
        self.assertEqual(rnpb[1][1], rnpb_ref[1][1])
        self.assertEqual(rnpb[1][2], rnpb_ref[1][2])
        self.assertEqual(rnpb[2][0], rnpb_ref[2][0])
        self.assertEqual(rnpb[2][1], rnpb_ref[2][1])
        self.assertEqual(rnpb[2][2], rnpb_ref[2][2])

    def test_eraBpn2xy(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        rnpb = self.ERFA.eraPnm06a(date1, date2)
        x, y = self.ERFA.eraBpn2xy(rnpb)
        x_ref, y_ref = erfa_astro.bpn2xy(rnpb)
        self.assertEqual(x, x_ref)
        self.assertEqual(y, y_ref)

    def test_eraS06(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        rnpb = self.ERFA.eraPnm06a(date1, date2)
        x, y = self.ERFA.eraBpn2xy(rnpb)
        val = self.ERFA.eraS06(date1, date2, x, y)
        val_ref = erfa_astro.s06(date1, date2, x, y)
        self.assertEqual(val, val_ref)

    def test_eraApci(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        ok, ehpv, ebpv = self.ERFA.eraEpv00(date1, date2)
        rnpb = self.ERFA.eraPnm06a(date1, date2)
        x, y = self.ERFA.eraBpn2xy(rnpb)
        s = self.ERFA.eraS06(date1, date2, x, y)

        astrom_ref = erfa_astro.apci(date1, date2, ebpv,  ehpv[0], x, y, s)
        self.ERFA.eraApci(date1, date2, ebpv,  ehpv[0], x, y, s)
        self.assertEqual(astrom_ref[()][6][0][0], self.ERFA.astrom.bpn[0][0])
        self.assertEqual(astrom_ref[()][6][0][1], self.ERFA.astrom.bpn[0][1])
        self.assertEqual(astrom_ref[()][6][0][2], self.ERFA.astrom.bpn[0][2])
        self.assertEqual(astrom_ref[()][6][1][0], self.ERFA.astrom.bpn[1][0])
        self.assertEqual(astrom_ref[()][6][1][1], self.ERFA.astrom.bpn[1][1])
        self.assertEqual(astrom_ref[()][6][1][2], self.ERFA.astrom.bpn[1][2])
        self.assertEqual(astrom_ref[()][6][2][0], self.ERFA.astrom.bpn[2][0])
        self.assertEqual(astrom_ref[()][6][2][1], self.ERFA.astrom.bpn[2][1])
        self.assertEqual(astrom_ref[()][6][2][2], self.ERFA.astrom.bpn[2][2])

    def test_eraEors(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        ok, ehpv, ebpv = self.ERFA.eraEpv00(date1, date2)
        rnpb = self.ERFA.eraPnm06a(date1, date2)
        x, y = self.ERFA.eraBpn2xy(rnpb)
        s = self.ERFA.eraS06(date1, date2, x, y)
        self.ERFA.eraApci(date1, date2, ebpv,  ehpv[0], x, y, s)

        eo_ref = erfa_astro.eors(rnpb, s)
        eo = self.ERFA.eraEors(rnpb, s)
        self.assertEqual(eo, eo_ref)

    def test_eraApci13(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)

        astrom_ref, eo_ref = erfa_astro.apci13(date1, date2)
        eo = self.ERFA.eraApci13(date1, date2)
        self.assertEqual(astrom_ref[()][0], self.ERFA.astrom.pmt)
        self.assertEqual(astrom_ref[()][1][0], self.ERFA.astrom.eb[0])
        self.assertEqual(astrom_ref[()][1][1], self.ERFA.astrom.eb[1])
        self.assertEqual(astrom_ref[()][1][2], self.ERFA.astrom.eb[2])
        self.assertEqual(astrom_ref[()][2][0], self.ERFA.astrom.eh[0])
        self.assertEqual(astrom_ref[()][2][1], self.ERFA.astrom.eh[1])
        self.assertEqual(astrom_ref[()][2][2], self.ERFA.astrom.eh[2])
        self.assertEqual(astrom_ref[()][3], self.ERFA.astrom.em)
        self.assertEqual(astrom_ref[()][4][0], self.ERFA.astrom.v[0])
        self.assertEqual(astrom_ref[()][4][1], self.ERFA.astrom.v[1])
        self.assertEqual(astrom_ref[()][4][2], self.ERFA.astrom.v[2])
        self.assertEqual(astrom_ref[()][5], self.ERFA.astrom.bm1)
        self.assertEqual(astrom_ref[()][6][0][0], self.ERFA.astrom.bpn[0][0])
        self.assertEqual(astrom_ref[()][6][0][1], self.ERFA.astrom.bpn[0][1])
        self.assertEqual(astrom_ref[()][6][0][2], self.ERFA.astrom.bpn[0][2])
        self.assertEqual(astrom_ref[()][6][1][0], self.ERFA.astrom.bpn[1][0])
        self.assertEqual(astrom_ref[()][6][1][1], self.ERFA.astrom.bpn[1][1])
        self.assertEqual(astrom_ref[()][6][1][2], self.ERFA.astrom.bpn[1][2])
        self.assertEqual(astrom_ref[()][6][2][0], self.ERFA.astrom.bpn[2][0])
        self.assertEqual(astrom_ref[()][6][2][1], self.ERFA.astrom.bpn[2][1])
        self.assertEqual(astrom_ref[()][6][2][2], self.ERFA.astrom.bpn[2][2])
        # self.assertAlmostEqual(astrom_ref[()][7], self.ERFA.astrom.along)
        # self.assertAlmostEqual(astrom_ref[()][8], self.ERFA.astrom.phi)
        # self.assertAlmostEqual(astrom_ref[()][9], self.ERFA.astrom.xpl)
        # self.assertAlmostEqual(astrom_ref[()][10], self.ERFA.astrom.ypl)
        # self.assertAlmostEqual(astrom_ref[()][11], self.ERFA.astrom.sphi)
        # self.assertAlmostEqual(astrom_ref[()][12], self.ERFA.astrom.cphi)
        # self.assertAlmostEqual(astrom_ref[()][13], self.ERFA.astrom.diurab)
        # self.assertAlmostEqual(astrom_ref[()][14], self.ERFA.astrom.eral)
        # self.assertAlmostEqual(astrom_ref[()][15], self.ERFA.astrom.refa)
        # self.assertAlmostEqual(astrom_ref[()][16], self.ERFA.astrom.refb)
        self.assertAlmostEqual(eo_ref, eo)

    def test_eraPmpx(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        eo = self.ERFA.eraApci13(date1, date2)
        rc = 3.14
        dc = 0.5
        pr = 0
        pd = 0
        px = 0
        rv = 0

        pco = self.ERFA.eraPmpx(rc, dc, pr, pd, px, rv, self.astrom.pmt, self.astrom.eb)
        pco_ref = erfa_astro.pmpx(rc, dc, pr, pd, px, rv, self.astrom.pmt, self.astrom.eb)
        self.assertEqual(pco[0], pco_ref[0])
        self.assertEqual(pco[1], pco_ref[1])
        self.assertEqual(pco[2], pco_ref[2])

    def test_eraLdsun(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        eo = self.ERFA.eraApci13(date1, date2)
        rc = 3.14
        dc = 0.5
        pr = 0
        pd = 0
        px = 0
        rv = 0
        pco = self.ERFA.eraPmpx(rc, dc, pr, pd, px, rv, self.astrom.pmt, self.astrom.eb)

        pnat = self.ERFA.eraLdsun(pco, self.astrom.eh, self.astrom.em)
        pnat_ref = erfa_astro.ldsun(pco, self.astrom.eh, self.astrom.em)
        self.assertEqual(pnat[0], pnat_ref[0])
        self.assertEqual(pnat[1], pnat_ref[1])
        self.assertEqual(pnat[2], pnat_ref[2])

    def test_eraAb(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        eo = self.ERFA.eraApci13(date1, date2)
        rc = 3.14
        dc = 0.5
        pr = 0
        pd = 0
        px = 0
        rv = 0
        pco = self.ERFA.eraPmpx(rc, dc, pr, pd, px, rv, self.astrom.pmt, self.astrom.eb)
        pnat = self.ERFA.eraLdsun(pco, self.astrom.eh, self.astrom.em)

        ppr = self.ERFA.eraAb(pnat, self.astrom.v, self.astrom.em, self.astrom.bm1)
        ppr_ref = erfa_astro.ab(pnat, self.astrom.v, self.astrom.em, self.astrom.bm1)
        self.assertEqual(ppr[0], ppr_ref[0])
        self.assertEqual(ppr[1], ppr_ref[1])
        self.assertEqual(ppr[2], ppr_ref[2])

    def test_eraAtci13(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        rc = 3.14
        dc = 0.5
        pr = 0
        pd = 0
        px = 0
        rv = 0

        ri, di, eo = self.ERFA.eraAtci13(rc, dc, pr, pd, px, rv, date1, date2)
        ri_ref, di_ref, eo_ref = erfa_astro.atci13(rc, dc, pr, pd, px, rv, date1, date2)
        self.assertEqual(ri, ri_ref)
        self.assertEqual(di, di_ref)
        self.assertEqual(eo, eo_ref)

    def test_eraAtic13(self):
        ok, date1, date2 = self.ERFA.eraDtf2d('UTC', self.ts.tm_year, self.ts.tm_mon, self.ts.tm_mday, self.ts.tm_hour, self.ts.tm_min, self.ts.tm_sec)
        ri = 3.14
        di = 0.5

        rc, dc, eo = self.ERFA.eraAtic13(ri, di, date1, date2)
        rc_ref, dc_ref, eo_ref = erfa_astro.atic13(ri, di, date1, date2)
        self.assertEqual(rc, rc_ref)
        self.assertEqual(dc, dc_ref)
        self.assertEqual(eo, eo_ref)
        print(ri, rc, di, dc)
