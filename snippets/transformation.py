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

from win32com.client.dynamic import Dispatch
from astropy.coordinates import solar_system_ephemeris
from astropy.coordinates import GCRS
import time



class Test:

    transform = Dispatch('ASCOM.Astrometry.Transform.Transform')

    def transformNovas(self, ra, dec, temp, height):
        self.transform.Refraction = False
        self.transform.SiteElevation = height
        self.transform.SiteLatitude = 49.0
        self.transform.SiteLongitude = 11.0
        self.transform.SiteTemperature = temp

        self.transform.SetJ2000(ra, dec)
        self.transform.Refresh
        val1 = self.transform.RATopocentric
        val2 = self.transform.DECTopocentric
        return val1, val2

    def transformAlt(self, ra, dec):

        with solar_system_ephemeris.set('jpl'):
            transform_to(GCRS(obstime=Time("J2000")))

        return val1, val2



if __name__ == "__main__":
    a = Test()
    ra1, dec1 = a.transformNovas(12, 57, 20.0, 0.0)
    ra2, dec2 = a.transformNovas(12, 57, 20.0, 0.0)
    print(ra2 - ra1, dec2 - dec1)
    time.sleep(1)
    ra2, dec2 = a.transformNovas(12, 57, 20.0, 0.0)
    print(ra2 - ra1, dec2 - dec1)
