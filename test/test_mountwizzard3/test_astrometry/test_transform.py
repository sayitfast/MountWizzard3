import unittest

import os
import PyQt5.QtCore

import skyfield.api
import astrometry.transform
import time

WorkDir = '~/PycharmProjects/MountWizzard3/config'

load = skyfield.api.Loader(WorkDir, expire=False, verbose=False)


class TestTransformations(unittest.TestCase):

    def testJ2000toJNow(self):
        global load
        ts = load.timescale()
        self.transform = astrometry.transform.Transform(self)
        # if nothing is present, use the coordinates of greenwich
        # date of 01.05.2018
        barnard = skyfield.api.Star(ra_hours=(17, 57, 48.49803),
                                    dec_degrees=(4, 41, 36.2072),
                                    )
        planets = load('de421.bsp')
        earth = planets['earth']

        for jd in range(2458240, 2459240, 100):
            self.transform.julianDate = jd
            timeTopo = ts.tt_jd(jd)
            astrometric = earth.at(timeTopo).observe(barnard).apparent()
            raJnow = barnard.ra.hours
            decJnow = barnard.dec.degrees
            #print('input:        {0:8.6f},{1:8.6f}'.format(raJnow, decJnow))
            raERFA, decERFA = self.transform.transformERFA(raJnow, decJnow, transform=3)
            #print('output ERFA:  {0:8.6f},{1:8.6f}'.format(raERFA, decERFA))
            raSKY, decSKY, dist = astrometric.radec(epoch=timeTopo)
            raSKY = raSKY.hours
            decSKY = decSKY.degrees
            #print('output SKYa:  {0:8.6f},{1:8.6f}'.format(raSKY, decSKY))
            print('delta :       {0:8.8f},{1:8.8f}'.format((raERFA-raSKY)*3600,
                                                           (decERFA-decSKY)*3600))



        time.sleep(1)

if __name__ == '__main__':
    unittest.main()
